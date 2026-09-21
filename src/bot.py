import discord
from discord.ext import tasks, commands
from discord import app_commands
from datetime import datetime, timedelta
import pytz
import os
import sys
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiohttp
import json
import asyncio

from dotenv import load_dotenv
load_dotenv()

# Set intents
intents = discord.Intents.default()
intents.message_content = True  # Required for fetching user message content
intents.members = True
intents.presences = True        # Useful for member information in transcripts

# Initialize bot with application_id
# Switched from discord.Client to commands.Bot so we can use add_cog().
# command_prefix is required by the constructor but unused since all
# commands here are slash commands via app_commands.CommandTree.
bot = commands.Bot(command_prefix="!", intents=intents, application_id="1325712952501735496")
# commands.Bot already creates its own CommandTree internally (bot.tree) —
# reuse it instead of creating a second one, which raises ClientException.
tree = bot.tree
EST = pytz.timezone("US/Eastern")

# Use the utils file
from utils import log_message

# Import your command sets
from promote import register_commands as register_promote
from demote import register_commands as register_demote
from backend import register_commands as register_commands_backend
from fun import register_commands as register_fun
from misc import register_commands as register_misc
from moderation import register_commands as register_moderation
from unban import register_commands as register_unban
from blacklist import register_commands as register_blacklist
from application import register_commands as register_application
from announce_training import register_commands as register_training
from loa import register_commands as register_LOA, loa_cleanup_task
from badgecreate import register_commands as register_badgecreate
from blacklist_review import register_commands as register_blacklistreview
from leadership_verify import register_commands as register_leadershipverify
from transfers import register_commands as register_transfers
from hr_system import register_commands as register_humanresources
from dual_clan import register_dual_clan_detector
from clockify_add import register_commands as register_clockify
from activities import start_activity_rotation
from hr_system import HRPanelView, ConfirmCloseView, HRChannelControlsView
from alt_checker import register_alt_checker
from welcome_goodbye import register_events as register_welcome_goodbye
from bg_check import register_commands as register_bg_check, setup_persistent_views
from hr_review import register_commands as register_hr_review
from log_dm import register_dm_logger
from ridealong import register_commands as register_ridealong
from schedule_system import register_commands as register_schedule, start_weekly_schedule_reset
from schedule_system import load_schedule_entries
from status import register_commands as register_status
from loa_conclude import register_commands as register_loaconclude
from leadership_application import register_review_command as register_leadershipapplication
from roleadd import register_commands as register_role_commands
from fetch_guilds import register_commands as register_fetch_guilds
from request_blacklist import setup_request_blacklist as register_request_blacklist
from active_warrants import register_commands as register_activewarrants
from webhook_server import start_server
from subdivision_webhook_server import start_server_sub
from ai_chat_cog_gemini import AIChatCog



@bot.event
async def on_ready():


    try:
        synced_global = await tree.sync()
        print(f"Synced {len(synced_global)} global commands.")
        print(f"Bot is online as {bot.user}.")

        start_activity_rotation(bot)
        print("Activities Started")
        load_schedule_entries()
        print("Loaded schedule entries from JSON.")
        bot.loop.create_task(loa_cleanup_task(bot))
        print("LOA Cleanup started.")


        await start_server(bot, port=8019)
        await start_server_sub(bot, port=8134)
        await bot.add_cog(AIChatCog(bot))


    except Exception as e:
        print(f"Error syncing commands: {e}")


async def setup_hook():
    bot.add_view(HRPanelView())               # For the panel to create new HR tickets
    bot.add_view(ConfirmCloseView(None))      # For the "Confirm Close" button
    bot.add_view(HRChannelControlsView(None)) # For the "Close/Lock to HR Supervision/Heads" buttons

    # Register persistent views for background check Pass/Fail buttons
    setup_persistent_views(bot)

    await register_dual_clan_detector(bot)
    register_dm_logger(bot)
    start_weekly_schedule_reset(bot)
    print("DM logger registered.")
    print("Dual clanning detector started.")
    print("Persistent views registered.")

bot.setup_hook = setup_hook


# List of role IDs allowed to use these commands
ALLOWED_ROLE_IDS = [
    1047612711099441182,  # Heads role (leadership discord)
    1047611161245397009,  # Heads role (CSSO HQ)
    # ... add more if needed
]


def has_required_roles(interaction: discord.Interaction) -> bool:
    user = interaction.user
    if isinstance(user, discord.Member):
        user_role_ids = [role.id for role in user.roles]
        return any(role_id in ALLOWED_ROLE_IDS for role_id in user_role_ids)
    return False


def register_sync(tree: app_commands.CommandTree):
    @tree.command(name="sync", description="Force-sync global slash commands (updates existing and adds new commands).")
    async def sync_command(interaction: discord.Interaction):
        if not has_required_roles(interaction):
            await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )
            await log_message(
                interaction.client,
                title="Unauthorized Global Sync Attempt",
                description=(
                    f"User: {interaction.user.mention} (`{interaction.user.id}`) attempted to sync commands without permission."
                ),
                color=discord.Color.red()
            )
            return

        await interaction.response.defer(ephemeral=True)
        try:
            synced_commands = await tree.sync()
            count = len(synced_commands)
            await interaction.followup.send(
                f"✅ Successfully synced {count} global commands.",
                ephemeral=True
            )
            await log_message(
                interaction.client,
                title="Global Sync Executed",
                description=f"Synced {count} global commands by {interaction.user.mention}.",
                color=discord.Color.green()
            )
        except Exception as e:
            await log_message(
                interaction.client,
                title="Global Sync Failed",
                description=f"Error: {str(e)}\nUser: {interaction.user.mention} (`{interaction.user.id}`)",
                color=discord.Color.red()
            )
            await interaction.followup.send(
                f"⚠️ Failed to sync global commands: {str(e)}",
                ephemeral=True
            )


if __name__ == "__main__":
    # Register all commands
    register_promote(tree)
    register_demote(tree)
    register_commands_backend(tree)
    register_fun(tree)
    register_misc(tree)
    register_moderation(tree)
    register_unban(tree)
    register_blacklist(tree)
    register_application(tree)
    register_training(tree)
    register_LOA(tree)
    register_badgecreate(tree)
    register_blacklistreview(tree)
    register_leadershipverify(tree)
    register_transfers(tree)
    register_humanresources(tree)
    register_clockify(tree)
    register_alt_checker(bot)
    register_welcome_goodbye(bot)
    register_bg_check(tree)
    register_hr_review(tree)
    register_ridealong(tree)
    register_schedule(tree)
    register_sync(tree)
    register_status(tree)
    register_loaconclude(tree)
    register_leadershipapplication(tree)
    register_role_commands(tree)
    register_fetch_guilds(tree)
    register_request_blacklist(tree)
    register_activewarrants(tree)


    try:
        bot.run(os.environ["DISCORD_TOKEN"])
    except Exception as e:
        print(f"Error occurred: {e}")
        input("Press Enter to close...")
