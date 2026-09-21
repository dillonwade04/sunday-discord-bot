# blacklist.py

import discord
from discord import app_commands
import aiohttp
from datetime import datetime

from config import DISCORD_TAGS_WEBHOOK_URL

# Shared command logging helper.
from utils import log_message  # log_message(bot: discord.Client, title: str, description: str, color: discord.Color)

##############################
# Configuration
##############################

# The list of guild IDs where you want to globally ban/unban the user
GUILDS_TO_BAN = [
    1047607743940395119,  # CSSO HQ
    1047610191711051866,  #CSSO Subdivisions
    1047610330693509272,  # CSSO leadership
]

# Channels for /terminate
TERMINATION_TEXT_CHANNEL_ID = 1047612860899004518
TERMINATION_EMBED_CHANNEL_ID = 1047612853856780339

# Channels for /blacklist
BLACKLIST_TEXT_CHANNEL_ID = 1047612860899004518
BLACKLIST_EMBED_CHANNEL_ID = 1047612844012732476

# CSSO High command role ID (DO NOT MODIFY)
ROLE_ID_TO_MENTION = 1215107073893998592  # CSSO High Command


MOD_ROLE_ID = 1047612731425038356  # SUNDAY Perms

# Webhook URL for the third message
WEBHOOK_URL = DISCORD_TAGS_WEBHOOK_URL

##############################
# Register the Commands
##############################

def register_commands(tree: app_commands.CommandTree):
    """
    Call register_commands(tree) in your main bot.py, then sync in on_ready().
    """

    @tree.command(name="terminate", description="Terminates (global-ban) a user and sends multiple messages.")
    @app_commands.describe(
        discord_id="The numeric Discord ID of the user",
        name="The user's name",
        reason="Reason for termination"
    )
    async def terminate(
        interaction: discord.Interaction,
        discord_id: str,
        name: str,
        reason: str
    ):
        """
        1) Global-ban user from GUILDS_TO_BAN.
        2) Send a plain-text message in TERMINATION_TEXT_CHANNEL_ID.
        3) Send an embed in TERMINATION_EMBED_CHANNEL_ID.
        4) Send a third message via webhook.
        5) Log all usage with log_message.
        """

        # --- Permission Check ---
        # Allow if the user has admin ban permissions OR the designated mod role.
        if not (interaction.user.guild_permissions.ban_members or any(role.id == MOD_ROLE_ID for role in interaction.user.roles)):
            await interaction.response.send_message(
                "You lack permission to run /terminate.",
                ephemeral=True
            )
            # Log unauthorized attempt
            await log_message(
                bot=interaction.client,
                title="Unauthorized /terminate Attempt",
                description=(
                    f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"**Target ID:** {discord_id}\n"
                    f"**Name:** {name}\n"
                    f"**Reason:** {reason}\n"
                    "**Status:** Failed (no permission)"
                ),
                color=discord.Color.red()
            )
            return

        # Respond (ephemeral) so the user knows we started
        await interaction.response.send_message(f"Processing termination for `{discord_id}`...", ephemeral=True)

        # --- Global Ban ---
        successes = []
        failures = []
        for guild_id in GUILDS_TO_BAN:
            guild = interaction.client.get_guild(guild_id)
            if not guild:
                failures.append((guild_id, "Bot not in guild or invalid guild ID"))
                continue
            try:
                await guild.ban(discord.Object(id=discord_id), reason=f"Terminated: {reason}")
                successes.append(guild_id)
            except discord.Forbidden:
                failures.append((guild_id, "Missing ban perms."))
            except discord.HTTPException as e:
                failures.append((guild_id, f"HTTP error: {e}"))

        # 1) Plain-text message in TERMINATION_TEXT_CHANNEL_ID
        channel_text = interaction.client.get_channel(TERMINATION_TEXT_CHANNEL_ID)
        if channel_text:
            message_text = (
                "**CSSO Termination**\n"
                f"> *Name:* {name}\n"
                f"> *Discord-ID:* {discord_id}\n"
                f"> *Reason:* {reason}\n"
                f"> *Approved By:* <@{interaction.user.id}>"
            )
            await channel_text.send(message_text)

        # 2) Embed in TERMINATION_EMBED_CHANNEL_ID
        channel_embed = interaction.client.get_channel(TERMINATION_EMBED_CHANNEL_ID)
        if channel_embed:
            embed = discord.Embed(
                title="Carolina State Sheriff's Office Log",
                description=(
                "**__CSSO Termination__**\n"
                f"> **Name**: {name}\n"
                f"> **Discord ID**: {discord_id}\n"
                f"> **Reason**: {reason}\n"
                f"> **Validated By**: <@{interaction.user.id}>"
                ),
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text="Carolina State Sheriff's Office Administration®", icon_url="https://i.imgur.com/wRbvz3o.png")
            await channel_embed.send(embed=embed)

        # 3) Third message via webhook
        # e.g. <@>\n-All CSSO Roles.\n<@&...>
       # third_message = (
       #     f"<@{discord_id}>\n"
       #     "-All CSSO Roles.\n"
       #     f"<@&{ROLE_ID_TO_MENTION}>"
       # )
       # async with aiohttp.ClientSession() as session:
       #     webhook = discord.Webhook.from_url(WEBHOOK_URL, session=session)
       #     await webhook.send(content=third_message)

      # ^ removed to avoid double pings

        # LOG usage
        # Summarize the ban attempts
        success_str = ", ".join(str(g) for g in successes) if successes else "None"
        fail_str = ", ".join(f"{gid} ({err})" for gid, err in failures) if failures else "None"
        await log_message(
            bot=interaction.client,
            title="/terminate Used",
            description=(
                f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                f"**Name:** {name}\n"
                f"**Discord ID:** {discord_id}\n"
                f"**Reason:** {reason}\n"
                f"**Guilds Banned:** {success_str}\n"
                f"**Ban Failures:** {fail_str}\n"
                "**Status:** Completed"
            ),
            color=discord.Color.red()
        )

    @tree.command(name="blacklist", description="Blacklist (global-ban) a user and sends multiple messages.")
    @app_commands.describe(
        discord_id="The numeric Discord ID of the user",
        name="The user's name",
        reason="Reason for blacklist"
    )
    async def blacklist(
        interaction: discord.Interaction,
        discord_id: str,
        name: str,
        reason: str
    ):

        # --- Permission Check ---
        if not (interaction.user.guild_permissions.ban_members or any(role.id == MOD_ROLE_ID for role in interaction.user.roles)):
            await interaction.response.send_message(
                "You lack permission to run /blacklist.",
                ephemeral=True
            )
            # Log unauthorized attempt
            await log_message(
                bot=interaction.client,
                title="Unauthorized /blacklist Attempt",
                description=(
                    f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"**Target ID:** {discord_id}\n"
                    f"**Name:** {name}\n"
                    f"**Reason:** {reason}\n"
                    "**Status:** Failed (no permission)"
                ),
                color=discord.Color.red()
            )
            return

        await interaction.response.send_message(f"Processing blacklist for `{discord_id}`...", ephemeral=True)

        # Global Ban
        successes = []
        failures = []
        for guild_id in GUILDS_TO_BAN:
            guild = interaction.client.get_guild(guild_id)
            if not guild:
                failures.append((guild_id, "Bot not in guild or invalid ID"))
                continue
            try:
                await guild.ban(discord.Object(id=discord_id), reason=f"Blacklist: {reason}")
                successes.append(guild_id)
            except discord.Forbidden:
                failures.append((guild_id, "Missing ban perms."))
            except discord.HTTPException as e:
                failures.append((guild_id, f"HTTP error: {e}"))

        # 1) Plain-text message in BLACKLIST_TEXT_CHANNEL_ID
        channel_text = interaction.client.get_channel(BLACKLIST_TEXT_CHANNEL_ID)
        if channel_text:
            message_text = (
                "**CSSO Termination & Blacklist**\n"
                f"> *Name:* {name}\n"
                f"> *Discord-ID:* {discord_id}\n"
                f"> *Reason:* {reason}\n"
                f"> *Approved By:* <@{interaction.user.id}>"
            )
            await channel_text.send(message_text)

        # 2) Embed in BLACKLIST_EMBED_CHANNEL_ID
        channel_embed = interaction.client.get_channel(BLACKLIST_EMBED_CHANNEL_ID)
        if channel_embed:
            embed = discord.Embed(
                title="Carolina State Sheriff's Office Log",
                description=(
                "**__CSSO Blacklist__**\n"
                f"> **Name**: {name}\n"
                f"> **Discord ID**: {discord_id}\n"
                f"> **Reason**: {reason}\n"
                f"> **Validated By**: <@{interaction.user.id}>"
                ),
                color=discord.Color.dark_red(),
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text="Carolina State Sheriff's Office Administration®", icon_url="https://i.imgur.com/wRbvz3o.png")
            await channel_embed.send(embed=embed)

        # 3) Third message via webhook
        # <@738542682170720278>\n-All CSSO Roles\n+CSSO Blacklist\n<@&...>
        third_message = (
            f"<@{discord_id}>\n"
            "-All CSSO Roles\n"
            "+CSSO Blacklist\n"
            f"<@&{ROLE_ID_TO_MENTION}>"
        )
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(WEBHOOK_URL, session=session)
            await webhook.send(content=third_message)

        # LOG usage
        success_str = ", ".join(str(g) for g in successes) if successes else "None"
        fail_str = ", ".join(f"{gid} ({err})" for gid, err in failures) if failures else "None"
        await log_message(
            bot=interaction.client,
            title="/blacklist Used",
            description=(
                f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                f"**Name:** {name}\n"
                f"**Discord ID:** {discord_id}\n"
                f"**Reason:** {reason}\n"
                f"**Guilds Banned:** {success_str}\n"
                f"**Ban Failures:** {fail_str}\n"
                "**Status:** Completed"
            ),
            color=discord.Color.dark_red()
        )
