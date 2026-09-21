# moderation.py

import discord
from discord import app_commands
from datetime import datetime
import pytz

# Import your custom logger from utils.py
from utils import log_message

# Timezone (optional, if you want timestamps in EST)
EST = pytz.timezone("US/Eastern")

# List of guild IDs for global bans/unbans
GLOBAL_BAN_GUILD_IDS = [
    1047607743940395119,  # CSSO HQ
    1047610191711051866,  # CSSO Subdivision
    1047610330693509272,# CSSO Leadership
]

MOD_ROLE_ID = 1047612731425038356

def register_commands(tree: app_commands.CommandTree):
    """
    Call this function from your main bot file (e.g. bot.py)
    to register the moderation slash commands, then sync in on_ready().

    Commands:
      /kick
      /ban
      /unban
      /global-ban
      /global-unban
    """

    # ------------------------------------------------------------------
    # /kick
    # ------------------------------------------------------------------
    @tree.command(name="kick", description="Kick a user from the server.")
    @app_commands.describe(
        user="The user to kick",
        reason="Reason for the kick"
    )
    async def kick(
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str = "No reason provided"
    ):
            # --- Permission Check ---
        # Allow if the user has admin ban permissions OR the designated mod role.
        if not (interaction.user.guild_permissions.ban_members or any(role.id == MOD_ROLE_ID for role in interaction.user.roles)):
            await interaction.response.send_message(
                "You lack permission to run /kick.",
                ephemeral=True
            )
            # Log unauthorized attempt
            await log_message(
                bot=interaction.client,
                title="Unauthorized /kick Attempt",
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

        try:
            await user.kick(reason=reason)
            await interaction.response.send_message(
                f"✅ {user.mention} has been kicked.\n**Reason:** {reason}",
                ephemeral=False
            )
            # LOG success
            await log_message(
                bot=interaction.client,
                title="/kick Used",
                description=(
                    f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"**Kicked:** {user.mention} (`{user.id}`)\n"
                    f"**Reason:** {reason}\n"
                    "**Status:** Success"
                ),
                color=discord.Color.green()
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to kick {user.mention}: {e}",
                ephemeral=True
            )
            # LOG failure
            await log_message(
                bot=interaction.client,
                title="/kick Failure",
                description=(
                    f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"**Target:** {user.mention} (`{user.id}`)\n"
                    f"**Reason:** {reason}\n"
                    f"**Error:** {str(e)}"
                ),
                color=discord.Color.red()
            )

    # ------------------------------------------------------------------
    # /ban
    # ------------------------------------------------------------------
    @tree.command(name="ban", description="Ban a user from the server.")
    @app_commands.describe(
        user="The user to ban",
        reason="Reason for the ban"
    )
    async def ban(
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str = "No reason provided"
    ):
            # --- Permission Check ---
        # Allow if the user has admin ban permissions OR the designated mod role.
        if not (interaction.user.guild_permissions.ban_members or any(role.id == MOD_ROLE_ID for role in interaction.user.roles)):
            await interaction.response.send_message(
                "You lack permission to run /ban.",
                ephemeral=True
            )
            # Log unauthorized attempt
            await log_message(
                bot=interaction.client,
                title="Unauthorized /ban Attempt",
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

        try:
            await user.ban(reason=reason)
            await interaction.response.send_message(
                f"✅ {user.mention} has been banned.\n**Reason:** {reason}",
                ephemeral=False
            )
            # LOG success
            await log_message(
                bot=interaction.client,
                title="/ban Used",
                description=(
                    f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"**Banned:** {user.mention} (`{user.id}`)\n"
                    f"**Reason:** {reason}\n"
                    "**Status:** Success"
                ),
                color=discord.Color.green()
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to ban {user.mention}: {e}",
                ephemeral=True
            )
            # LOG failure
            await log_message(
                bot=interaction.client,
                title="/ban Failure",
                description=(
                    f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"**Target:** {user.mention} (`{user.id}`)\n"
                    f"**Reason:** {reason}\n"
                    f"**Error:** {str(e)}"
                ),
                color=discord.Color.red()
            )

    # ------------------------------------------------------------------
    # /unban
    # ------------------------------------------------------------------
    @tree.command(name="unban", description="Unban a user in this server (by mention or ID).")
    @app_commands.describe(
        user="The user you want to unban",
        reason="Reason for unbanning (optional)"
    )
    async def unban(
        interaction: discord.Interaction,
        user: discord.User,
        reason: str = "No reason provided"
    ):
        """Unbans a user from the current guild, if you have Ban Members permission."""
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server (guild).",
                ephemeral=True
            )
            return

        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(
                "You do not have permission to unban members.",
                ephemeral=True
            )
            # LOG unauthorized
            await log_message(
                bot=interaction.client,
                title="Unauthorized /unban Attempt",
                description=(
                    f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"Tried to unban: {user.mention} (`{user.id}`)\n"
                    f"Reason: {reason}\n"
                    "**Status:** Failed (no permission)"
                ),
                color=discord.Color.red()
            )
            return

        try:
            await guild.unban(user, reason=reason)
            await interaction.response.send_message(
                f"✅ {user.mention} has been unbanned.\n**Reason:** {reason}",
                ephemeral=False
            )
            # LOG success
            await log_message(
                bot=interaction.client,
                title="/unban Used",
                description=(
                    f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"**Unbanned:** {user.mention} (`{user.id}`)\n"
                    f"**Reason:** {reason}\n"
                    "**Status:** Success"
                ),
                color=discord.Color.green()
            )
        except discord.NotFound:
            await interaction.response.send_message(
                f"❌ {user.mention} is not currently banned in this guild.",
                ephemeral=True
            )
            # LOG attempt
            await log_message(
                bot=interaction.client,
                title="/unban: NotFound",
                description=(
                    f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"Tried to unban: {user.mention} (`{user.id}`)\n"
                    f"Reason: {reason}\n"
                    "**Status:** Not Banned"
                ),
                color=discord.Color.orange()
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to unban members.",
                ephemeral=True
            )
            # LOG permission issue
            await log_message(
                bot=interaction.client,
                title="/unban Forbidden",
                description=(
                    f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"**Target:** {user.mention} (`{user.id}`)\n"
                    f"Reason: {reason}\n"
                    "**Status:** Bot lacks unban permission"
                ),
                color=discord.Color.red()
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"❌ Failed to unban {user.mention}: {str(e)}",
                ephemeral=True
            )
            # LOG failure
            await log_message(
                bot=interaction.client,
                title="/unban Failure",
                description=(
                    f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"**Target:** {user.mention} (`{user.id}`)\n"
                    f"**Reason:** {reason}\n"
                    f"**Error:** {str(e)}"
                ),
                color=discord.Color.red()
            )

    # ------------------------------------------------------------------
    # /global-ban
    # ------------------------------------------------------------------
    @tree.command(name="global-ban", description="Ban a user (by Discord ID) from multiple guilds.")
    @app_commands.describe(
        user_id="The Discord ID of the user you want to ban globally.",
        reason="Reason for the ban."
    )
    async def global_ban(
        interaction: discord.Interaction,
        user_id: str,
        reason: str = "No reason provided."
    ):
        """
        Bans a user ID from each guild in GLOBAL_BAN_GUILD_IDS,
        then sends an embed with ✅/❌ results, and logs usage.
        """
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(
                "You do not have permission to ban members.",
                ephemeral=True
            )
            # LOG unauthorized
            await log_message(
                bot=interaction.client,
                title="Unauthorized /global-ban Attempt",
                description=(
                    f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"Tried to global-ban user ID `{user_id}`\n"
                    f"Reason: {reason}\n"
                    "**Status:** Failed (no permission)"
                ),
                color=discord.Color.red()
            )
            return

        # Acknowledge ephemeral
        await interaction.response.send_message(
            f"Banning user ID `{user_id}` from {len(GLOBAL_BAN_GUILD_IDS)} guild(s)...",
            ephemeral=True
        )

        successes = []
        failures = []

        for guild_id in GLOBAL_BAN_GUILD_IDS:
            guild = interaction.client.get_guild(guild_id)
            if guild is None:
                failures.append((guild_id, "Bot not in this guild / invalid ID"))
                continue

            try:
                await guild.ban(
                    discord.Object(id=user_id),
                    reason=f"[Global Ban] {reason}"
                )
                successes.append(guild_id)
            except discord.Forbidden:
                failures.append((guild_id, "Missing ban permissions"))
            except discord.HTTPException as e:
                failures.append((guild_id, f"HTTP error: {e}"))

        # Build the lines for embed
        lines = []
        for g_id in successes:
            g = interaction.client.get_guild(g_id)
            name = g.name if g else f"Unknown ({g_id})"
            lines.append(f"✅ {name}")
        for g_id, err in failures:
            g = interaction.client.get_guild(g_id)
            name = g.name if g else f"Unknown ({g_id})"
            lines.append(f"❌ {name}")

        results_str = "\n".join(lines) if lines else "No guilds processed."

        # Create the embed
        embed = discord.Embed(
            title="Ban Status",
            color=discord.Color.red(),
            timestamp=datetime.now(EST)
        )
        embed.add_field(name="User", value=f"<@{user_id}>", inline=False)
        embed.add_field(name="User ID", value=user_id, inline=False)
        embed.add_field(name="Guild Results", value=results_str, inline=False)
        embed.set_footer(text="Carolina State Sheriff's Office Administration®")

        # Follow-up
        await interaction.followup.send(embed=embed)

        # LOG usage
        await log_message(
            bot=interaction.client,
            title="/global-ban Used",
            description=(
                f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                f"**User ID:** {user_id}\n"
                f"**Reason:** {reason}\n"
                f"**Guilds Banned (✅):** {', '.join(str(g) for g in successes)}\n"
                f"**Failed (❌):** {', '.join(f'{gid} ({err})' for gid,err in failures)}\n"
                "**Status:** Completed"
            ),
            color=discord.Color.dark_red()
        )

    # ------------------------------------------------------------------
    # /global-unban
    # ------------------------------------------------------------------
    @tree.command(name="global-unban", description="Unban a user (by Discord ID) from multiple guilds.")
    @app_commands.describe(
        user_id="The Discord ID of the user you want to unban globally.",
        reason="Reason for the unban."
    )
    async def global_unban(
        interaction: discord.Interaction,
        user_id: str,
        reason: str = "No reason provided."
    ):
        """
        Unbans a user ID from each guild in GLOBAL_BAN_GUILD_IDS,
        then sends an embed with ✅/❌ results, and logs usage.
        """
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(
                "You do not have permission to unban members.",
                ephemeral=True
            )
            # LOG unauthorized
            await log_message(
                bot=interaction.client,
                title="Unauthorized /global-unban Attempt",
                description=(
                    f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"Tried to global-unban ID `{user_id}`\n"
                    f"Reason: {reason}\n"
                    "**Status:** Failed (no permission)"
                ),
                color=discord.Color.red()
            )
            return

        await interaction.response.send_message(
            f"Unbanning user ID `{user_id}` from {len(GLOBAL_BAN_GUILD_IDS)} guild(s)...",
            ephemeral=True
        )

        successes = []
        failures = []

        for guild_id in GLOBAL_BAN_GUILD_IDS:
            guild = interaction.client.get_guild(guild_id)
            if guild is None:
                failures.append((guild_id, "Bot not in guild / invalid ID"))
                continue

            try:
                await guild.unban(
                    discord.Object(id=user_id),
                    reason=f"[Global Unban] {reason}"
                )
                successes.append(guild_id)
            except discord.Forbidden:
                failures.append((guild_id, "Missing ban/unban permissions"))
            except discord.HTTPException as e:
                failures.append((guild_id, f"HTTP error: {e}"))

        # Build lines for embed
        lines = []
        for g_id in successes:
            g = interaction.client.get_guild(g_id)
            name = g.name if g else f"Unknown ({g_id})"
            lines.append(f"✅ {name}")
        for g_id, err in failures:
            g = interaction.client.get_guild(g_id)
            name = g.name if g else f"Unknown ({g_id})"
            lines.append(f"❌ {name}")

        results_str = "\n".join(lines) if lines else "No guilds processed."

        embed = discord.Embed(
            title="Unban Status",
            color=discord.Color.green(),
            timestamp=datetime.now(EST)
        )
        embed.add_field(name="User", value=f"<@{user_id}>", inline=False)
        embed.add_field(name="User ID", value=user_id, inline=False)
        embed.add_field(name="Guild Results", value=results_str, inline=False)
        embed.set_footer(text="Carolina State Sheriff's Office Administration®")

        await interaction.followup.send(embed=embed)

        # LOG usage
        await log_message(
            bot=interaction.client,
            title="/global-unban Used",
            description=(
                f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                f"**User ID:** {user_id}\n"
                f"**Reason:** {reason}\n"
                f"**Guilds Unbanned (✅):** {', '.join(str(g) for g in successes)}\n"
                f"**Failed (❌):** {', '.join(f'{gid} ({err})' for gid,err in failures)}\n"
                "**Status:** Completed"
            ),
            color=discord.Color.dark_green()
        )
