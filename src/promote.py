# promote.py
import discord
from discord import app_commands
from datetime import datetime
import pytz
import aiohttp  # Needed for sending webhook payloads

from config import DISCORD_TAGS_WEBHOOK_URL
from utils import log_message

# Timezone setup
EST = pytz.timezone("US/Eastern")

# Channel IDs
PROMOTION_CHANNEL_ID = 1047611317487411260  # CSSO HQ Needs tags
PROMOTION_LOG_CHANNEL_ID = 1047612834118381640  # Leadership promotion logs channel
LEADERSHIP_CONGRATS_CHANNEL_ID = 1047612776580911236  # CSSO leadership general chat
LEADERSHIP_TAG_REQUEST_CHANNEL_ID = 1047612779097497631  # CSSO Leadership needs tags channel

# Roles allowed to use /promote
PROMOTION_ROLE_IDS = [1047612736823099484]  # CSSO promotion discord supervisor role only
ALLOWED_PROMOTE_CHANNEL_IDS = [1057463427985047594, 1117978175771787406, 1116890110009561128]  # Leadership bot commands, Command bot commands, and heads bot commands

# Webhook URL for additional promotion messages.
PROMOTION_ADDITIONAL_WEBHOOK_URL = DISCORD_TAGS_WEBHOOK_URL

RANK_CHOICES = [
    app_commands.Choice(name="Cadet",               value="Cadet"),
    app_commands.Choice(name="Probationary Deputy", value="Probationary Deputy"),
    app_commands.Choice(name="Deputy I",            value="Deputy I"),
    app_commands.Choice(name="Deputy II",           value="Deputy II"),
    app_commands.Choice(name="Deputy III",          value="Deputy III"),
    app_commands.Choice(name="Senior Deputy",       value="Senior Deputy"),
    app_commands.Choice(name="Trial Corporal",      value="Trial Corporal"),
    app_commands.Choice(name="Corporal",            value="Corporal"),
    app_commands.Choice(name="Senior Corporal",     value="Senior Corporal"),
    app_commands.Choice(name="Sergeant",            value="Sergeant"),
    app_commands.Choice(name="Staff Sergeant",      value="Staff Sergeant"),
    app_commands.Choice(name="Master Sergeant",     value="Master Sergeant"),
    app_commands.Choice(name="Lieutenant",          value="Lieutenant"),
    app_commands.Choice(name="Captain",             value="Captain"),
    app_commands.Choice(name="Major",               value="Major"),
    app_commands.Choice(name="Colonel",             value="Colonel"),
]

def can_promote(interaction: discord.Interaction) -> bool:
    return any(role.id in PROMOTION_ROLE_IDS for role in interaction.user.roles)

def register_commands(tree: app_commands.CommandTree):
    @tree.command(name="promote", description="Promote a Deputy.")
    @app_commands.describe(
        discord_id="The Deputy's Discord ID to ping (numeric ID)",
        name="The Deputy's name (e.g., R. Dillon)",
        reason="Why they are being promoted",
        new_rank="New rank (e.g., Corporal, Sergeant, etc.)",
        old_rank="Old rank (e.g., Deputy III, Senior Deputy, etc.)"
    )
    @app_commands.choices(new_rank=RANK_CHOICES, old_rank=RANK_CHOICES)
    async def promote(
        interaction: discord.Interaction,
        discord_id: str,
        name: str,
        reason: str,
        new_rank: app_commands.Choice[str],
        old_rank: app_commands.Choice[str]
    ):
        if interaction.channel_id not in ALLOWED_PROMOTE_CHANNEL_IDS:
            return await interaction.response.send_message(
                "This command can only be used in <#1057463427985047594>", ephemeral=True
            )

        if not can_promote(interaction):
            await interaction.response.send_message(
                "You do not have the required role to use this command. (You need the Supervisor role, contact a Sergeant to promote people.)", ephemeral=True
            )
            # Log unauthorized usage
            await log_message(
                interaction.client,
                title="Unauthorized /promote Attempt",
                description=(
                    f"User {interaction.user.mention} (`{interaction.user.id}`) tried to promote <@{discord_id}> ({name}) "
                    "but lacks the required role."
                ),
                color=discord.Color.red()
            )
            return

        # Build the main promotion embed
        extra_lines = []
        if new_rank.value == "Trial Corporal":
            extra_lines.append("+CSSO Leadership\n+Mandatory Ride Along")
        if new_rank.value == "Corporal":
            extra_lines.append("+CSSO Leadership")
        if new_rank.value == "Deputy I":
            extra_lines.append("+Basic Training Certification")
        if new_rank.value == "Deputy III":
            extra_lines.append("+Mandatory Ride Along")
        if new_rank.value == "Sergeant":
            extra_lines.append("+CSSO Supervisor")
        if new_rank.value == "Lieutenant":
            extra_lines.append("+CSSO Command")
        if new_rank.value == "Major":
            extra_lines.append("+CSSO High Command")

        announcement_description = (
            f"> **Promotion**\n"
            f"<@{discord_id}>\n"
            f"-{old_rank.value}\n"
            f"+{new_rank.value}"
        )
        if extra_lines:
            announcement_description += "\n" + "\n".join(extra_lines)

        embed_announcement = discord.Embed(
            title="Carolina State Sheriff's Office | Needs Tags",
            description=announcement_description,
            color=discord.Color.blue(),
            timestamp=datetime.now(EST)
        )
        embed_announcement.set_footer(text="Carolina State Sheriff's Office Administration®", icon_url="https://i.imgur.com/wRbvz3o.png")

        info_str = (
            f"**Name:** {name}\n"
            f"**Discord:** {discord_id}\n"
            f"**Reason:** {reason}\n"
            f"**New-Rank:** {new_rank.value}\n"
            f"**Old-Rank:** {old_rank.value}\n"
            f"**Promoted By:** <@{interaction.user.id}>"
        )
        embed_logging = discord.Embed(
            title="Sheriff Promotion Logging",
            color=discord.Color.green(),
            timestamp=datetime.now(EST)
        )
        embed_logging.add_field(name="> **Promotion**", value=info_str, inline=False)
        embed_logging.set_footer(text="Carolina State Sheriff's Office Administration®", icon_url="https://i.imgur.com/wRbvz3o.png")

        # Fetch the channels
        promotion_channel = interaction.client.get_channel(PROMOTION_CHANNEL_ID)
        logging_channel = interaction.client.get_channel(PROMOTION_LOG_CHANNEL_ID)
        congrats_channel = interaction.client.get_channel(LEADERSHIP_CONGRATS_CHANNEL_ID)
        tag_request_channel = interaction.client.get_channel(LEADERSHIP_TAG_REQUEST_CHANNEL_ID)

        if not promotion_channel or not logging_channel:
            return await interaction.response.send_message(
                "Error: One or more required channels are missing. Please contact an admin.", ephemeral=True
            )

        # Send the main promotion announcement and logging embeds
        await promotion_channel.send(content="<@&1047611191851221023>", embed=embed_announcement)
        await logging_channel.send(embed=embed_logging)

        # Leadership Needs Tags logic
        leadership_needs_tags = None
        if new_rank.value == "Trial Corporal":
            leadership_needs_tags = (
                f"+{new_rank.value}\n"
                f"+Leadership"
            )
        if new_rank.value == "Corporal":
            leadership_needs_tags = (
                f"+{new_rank.value}\n"
                f"+Leadership"
            )
        elif new_rank.value == "Senior Corporal":
            leadership_needs_tags = (
                f"-{old_rank.value}\n"
                f"+{new_rank.value}"
            )
        elif new_rank.value == "Sergeant":
            leadership_needs_tags = (
                f"-{old_rank.value}\n"
                f"+{new_rank.value}\n"
                f"+Supervisor"
            )
        elif new_rank.value == "Staff Sergeant":
            leadership_needs_tags = (
                f"-{old_rank.value}\n"
                f"+{new_rank.value}"
            )
        elif new_rank.value == "Master Sergeant":
            leadership_needs_tags = (
                f"-{old_rank.value}\n"
                f"+{new_rank.value}"
            )
        elif new_rank.value == "Lieutenant":
            leadership_needs_tags = (
                f"-{old_rank.value}\n"
                f"+{new_rank.value}\n"
                f"+Command"
            )
        elif new_rank.value == "Captain":
            leadership_needs_tags = (
                f"-{old_rank.value}\n"
                f"+{new_rank.value}"
            )
        elif new_rank.value == "Major":
            leadership_needs_tags = (
                f"-{old_rank.value}\n"
                f"+{new_rank.value}"
            )
        elif new_rank.value == "Colonel":
            leadership_needs_tags = (
                f"-{old_rank.value}\n"
                f"+{new_rank.value}"
            )

        if leadership_needs_tags and tag_request_channel:
            tag_request_embed = discord.Embed(
                title="Carolina State Sheriff's Office | Needs Tags Request",
                description=f"> Leadership promotion\n<@{discord_id}>\n{leadership_needs_tags}",
                color=discord.Color.dark_red(),
                timestamp=datetime.now(EST)
            )
            tag_request_embed.set_footer(text="Carolina State Sheriff's Office Administration®", icon_url="https://i.imgur.com/wRbvz3o.png")
            await tag_request_channel.send(content="<@&1047612726433816668>", embed=tag_request_embed)

        # If promoted to Corporal, send congrats message in congrats channel
        if new_rank.value == "Trial Corporal" and congrats_channel:
            congrats_message = f"👏 Congratulations <@{discord_id}> and welcome to **CSSO Leadership!** 👏"
            await congrats_channel.send(congrats_message)
        elif new_rank.value == "Corporal" and congrats_channel:
            congrats_message = f"👏 Congratulations <@{discord_id}> and welcome to **CSSO Leadership!** 👏"
            await congrats_channel.send(congrats_message)


        # Send additional webhook message based on the new rank
        additional_payload = None
        if new_rank.value == "Trial Corporal":
              additional_payload = {
                "content": (
                    f"<@{discord_id}>\n"
                    "+CSSO Leadership\n"
                    f"<@&1215107073893998592>"
                ),
                "allowed_mentions": {"parse": ["users", "roles"]}
              }
        elif new_rank.value == "Corporal":
            additional_payload = {
                "content": (
                    f"<@{discord_id}>\n"
                    "+CSSO Leadership\n"
                    f"<@&1215107073893998592>"
                ),
                "allowed_mentions": {"parse": ["users", "roles"]}
            }
        elif new_rank.value == "Sergeant":
            additional_payload = {
                "content": (
                    f"<@{discord_id}>\n"
                    "+CSSO Supervisor\n"
                    f"<@&1215107073893998592>"
                ),
                "allowed_mentions": {"parse": ["users", "roles"]}
            }
        elif new_rank.value == "Lieutenant":
            additional_payload = {
                "content": (
                    f"<@{discord_id}>\n"
                    "+CSSO Command\n"
                    f"<@&1215107073893998592>"
                ),
                "allowed_mentions": {"parse": ["users", "roles"]}
            }
        elif new_rank.value == "Major":
            additional_payload = {
                "content": (
                    f"<@{discord_id}>\n"
                    "+CSSO High Command\n"
                    f"<@&843987082560012298>"
                ),
                "allowed_mentions": {"parse": ["users", "roles"]}
            }

        if additional_payload:
            async with aiohttp.ClientSession() as session:
                try:
                    await session.post(PROMOTION_ADDITIONAL_WEBHOOK_URL, json=additional_payload)
                except Exception as e:
                    print("Failed to send additional promotion webhook:", e)

        # Log successful promotion
        await log_message(
            interaction.client,
            title="Promotion Command Used",
            description=(
                f"User {interaction.user.mention} (`{interaction.user.id}`)\n"
                f"Promoted <@{discord_id}> ({name}) from {old_rank.value} to {new_rank.value}\n"
                f"Reason: {reason}"
            ),
            color=discord.Color.green()
        )

        # Acknowledge success to the command invoker
        await interaction.response.send_message(f"**Success!** Promotion posted for {name}.", ephemeral=False)
