
import discord
from discord import app_commands
from datetime import datetime
import pytz
import asyncio
import aiohttp
import json
from pathlib import Path

from config import DISCORD_TAGS_WEBHOOK_URL
from utils import log_message

# ----- CONFIGURATION CONSTANTS -----
ALLOWED_BG_CHECK_CHANNEL_IDS = [1047612785716101231]
ALLOWED_BG_CHECK_ROLE_IDS = [1047612741235523654]
BACKGROUND_CHECKER_ROLE_ID = 1250678335445663804
TARGET_GUILD_ID = 1047607743940395119
BG_CHECK_PENDING_ROLE_ID = 1047611179746476052
BG_CHECK_PENDING2_ROLE_ID = 1341942242142851162
BG_CHECK_APPROVED_ROLE_ID = 1047611224789110874
WEBHOOK_URL = DISCORD_TAGS_WEBHOOK_URL

# Files
SUBMISSIONS_FILE = Path("bg_submissions.json")
PERSISTENT_VIEWS_FILE = Path("bg_persistent_views.json")

def load_submissions() -> dict:
    if SUBMISSIONS_FILE.exists():
        try:
            return json.loads(SUBMISSIONS_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}

def save_submissions(data: dict):
    SUBMISSIONS_FILE.write_text(json.dumps(data, indent=2))

def load_persistent_views() -> list:
    if PERSISTENT_VIEWS_FILE.exists():
        try:
            return json.loads(PERSISTENT_VIEWS_FILE.read_text())
        except json.JSONDecodeError:
            return []
    return []

def save_persistent_views(data: list):
    PERSISTENT_VIEWS_FILE.write_text(json.dumps(data, indent=2))

async def handle_review_action(interaction: discord.Interaction, discord_id: str, result: str):
    await interaction.response.defer()

    if interaction.channel_id not in ALLOWED_BG_CHECK_CHANNEL_IDS:
        return await interaction.followup.send(
            "This command can only be used in the designated <#1047612785716101231> channel.",
            ephemeral=True
        )
    if BACKGROUND_CHECKER_ROLE_ID not in [r.id for r in interaction.user.roles]:
        return await interaction.followup.send(
            "You do not have permission to review background checks.",
            ephemeral=True
        )

    guild = interaction.client.get_guild(TARGET_GUILD_ID)
    if not guild:
        return await interaction.followup.send("Target guild not found.", ephemeral=True)
    try:
        member = await guild.fetch_member(int(discord_id))
    except Exception:
        return await interaction.followup.send(
            "Applicant not found in CSSO HQ. Leadership has not invited them.",
            ephemeral=False
        )

    subs = load_submissions()
    submitter_id = subs.pop(discord_id, None)
    if submitter_id is not None:
        save_submissions(subs)

    if result == "passed":
        pending = guild.get_role(BG_CHECK_PENDING_ROLE_ID)
        pending2 = guild.get_role(BG_CHECK_PENDING2_ROLE_ID)
        approved = guild.get_role(BG_CHECK_APPROVED_ROLE_ID)
        try:
            roles_to_remove = [r for r in [pending, pending2] if r and r in member.roles]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="Background check passed")
            if approved:
                await member.add_roles(approved, reason="Background check passed")
        except Exception as e:
            await interaction.followup.send(f"Role update failed: {e}", ephemeral=True)

        try:
            await member.send(
                f"Howdy! {member.mention} and welcome to the Sheriff's Office! Your background check has been cleared!\n"
                "Below you will find many important channels.\n\n"
                "<#1047611411951521822> Basic Training Info\n"
                "<#1047611300416585870> Important Information\n"
                "<#1047611306255077548> Rules\n"
                "<#1047611305223258243> Subdivision Applications\n\n"
                "*If you have any questions, please DM a Leadership member or create a CSSO HR Ticket!*"
            )
        except:
            pass

        await interaction.followup.send(
              f"Background check passed. <@{discord_id}> has been given the Cadet role and is ready for training!.\n-# **Cleared by:** <@{interaction.user.id}>",
            ephemeral=False
        )

        payload = {
            "content": f"<@{discord_id}>\n-CSSO Recruit\n+LEO Cert\n<@&1215107073893998592>",
            "allowed_mentions": {"parse": ["users", "roles"]}
        }
        async with aiohttp.ClientSession() as session:
            await session.post(WEBHOOK_URL, json=payload)

    else:
        if submitter_id:
            await interaction.followup.send(
                f"Background check failed. Kicked <@{discord_id}> from CSSO HQ, <@{submitter_id}> please remove them from roster",
                allowed_mentions=discord.AllowedMentions(users=True),
                ephemeral=False
            )

        try:
            await member.send(
                "Your background check has failed and you have been removed from the Carolina State Sheriff's Office. If you feel as if this was a mistake contact a CSSO leadership member."
            )
        except:
            pass

        await asyncio.sleep(1)
        try:
            await member.kick(reason="Background check failed")
        except Exception as e:
            return await interaction.followup.send(f"Failed to kick user: {e}", ephemeral=True)

class BackgroundCheckReviewView(discord.ui.View):
    def __init__(self, discord_id: str):
        super().__init__(timeout=None)  # Must be None for persistence
        self.discord_id = discord_id

    @discord.ui.button(label="Pass", style=discord.ButtonStyle.success, custom_id="bg_pass_button")
    async def pass_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_review_action(interaction, self.discord_id, "passed")

    @discord.ui.button(label="Fail", style=discord.ButtonStyle.danger, custom_id="bg_fail_button")
    async def fail_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_review_action(interaction, self.discord_id, "failed")

def setup_persistent_views(bot: discord.Client):
    data = load_persistent_views()
    for discord_id in data:
        bot.add_view(BackgroundCheckReviewView(discord_id))

def register_commands(tree: app_commands.CommandTree):
    @tree.command(name="background-check", description="Submit background check info.")
    @app_commands.describe(
        steam_hex="Your Steam Hex value",
        discord_id="The Discord ID of the applicant",
        in_game_name="The in-game name of the applicant"
    )
    async def background_check(interaction: discord.Interaction, steam_hex: str, discord_id: str, in_game_name: str):
        if interaction.channel_id not in ALLOWED_BG_CHECK_CHANNEL_IDS:
            return await interaction.response.send_message(
                "This command can only be used in the designated <#1047612785716101231> channel.",
                ephemeral=True
            )
        if not any(role.id in ALLOWED_BG_CHECK_ROLE_IDS for role in interaction.user.roles):
            return await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )

        subs = load_submissions()
        subs[discord_id] = interaction.user.id
        save_submissions(subs)

        embed = discord.Embed(
            title="Background Check Submission",
            color=discord.Color.pink(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Steam Hex", value=steam_hex, inline=False)
        embed.add_field(name="Discord ID", value=discord_id, inline=False)
        embed.add_field(name="In-game Name", value=in_game_name, inline=False)
        embed.set_footer(
            text="Carolina State Sheriff's Office Administration®",
            icon_url="https://i.imgur.com/wRbvz3o.png"
        )

        view = BackgroundCheckReviewView(discord_id)
        await interaction.response.send_message(
            content=f"<@&{BACKGROUND_CHECKER_ROLE_ID}>",
            embed=embed,
            view=view,
            allowed_mentions=discord.AllowedMentions(roles=True)
        )

        # Save view for persistence
        persistent_views = load_persistent_views()
        if discord_id not in persistent_views:
            persistent_views.append(discord_id)
            save_persistent_views(persistent_views)

        payload = {
            "content": f"<@{discord_id}>\n+CSSO\n+CSSO Recruit\n<@&1215107073893998592>",
            "allowed_mentions": {"parse": ["users", "roles"]}
        }
        async with aiohttp.ClientSession() as session:
            await session.post(WEBHOOK_URL, json=payload)

    @tree.command(name="review-background-check", description="Review background check results.")
    @app_commands.describe(
        discord_id="The Discord ID of the applicant",
        result="Background check result: Passed or Failed"
    )
    @app_commands.choices(result=[
        app_commands.Choice(name="Passed", value="passed"),
        app_commands.Choice(name="Failed", value="failed")
    ])
    async def review_background_check(interaction: discord.Interaction, discord_id: str, result: app_commands.Choice[str]):
        await handle_review_action(interaction, discord_id, result.value)
