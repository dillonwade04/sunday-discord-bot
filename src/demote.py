# demote.py
import discord
from discord import app_commands
from datetime import datetime
import pytz

from utils import log_message


# EST TIMZONE FOR EMBEDS TIMESTAMP
EST = pytz.timezone("US/Eastern")

# CSSO HQ NEEDS TAG CHANNEL
DEMOTION_CHANNEL_ID = 1047611317487411260

# DEMOTION LOG CHANNEL CSSO LEADERSHIP
DEMOTION_LOG_CHANNEL_ID = 1047612840493719563

# Roles allowed to use /demote
DEMOTION_ROLE_IDS = [
    1047612736823099484,  # Example: Supervisor
    # ... add more role IDs if needed
]

ALLOWED_PROMOTE_CHANNEL_IDS = [1057463427985047594, 1117978175771787406, 1116890110009561128]  # e.g., multiple channel IDs
#Leadership Command, Heads, bot commands channels

# Define your rank choices (as a Python list of app_commands.Choice objects)
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

def can_demote(interaction: discord.Interaction) -> bool:
    """Returns True if the user has any of the allowed role IDs."""
    return any(role.id in DEMOTION_ROLE_IDS for role in interaction.user.roles)

def register_commands(tree: app_commands.CommandTree):
    """
    Call this function from your main bot file (e.g. bot.py)
    to register the /demote slash command.
    """

    @tree.command(name="demote", description="Demote a Deputy.")
    @app_commands.describe(
        discord_id = "The Deputy's Discord ID to ping (numeric ID)",
        name      = "The Deputy's name (e.g. R. Dillon)",
        reason    = "Why they are being demoted",
        new_rank  = "New rank (e.g. Corporal, Sergeant, etc.)",
        old_rank  = "Old rank (e.g. Deputy III, Senior Deputy, etc.)"
    )
    @app_commands.choices(new_rank=RANK_CHOICES, old_rank=RANK_CHOICES)
    async def demote(
        interaction: discord.Interaction,
        discord_id: str,
        name: str,
        reason: str,
        new_rank: app_commands.Choice[str],
        old_rank: app_commands.Choice[str]
    ):
        """
        demotes a Deputy if the user has the required roles.
        Sends two embeds:
          1) "Needs Tags" embed in DEMOTION_CHANNEL_ID
          2) "Sheriff Demotion Logging" embed in DEMOTION_LOG_CHANNEL_ID
        """

        # 1. Check if correct channel
        if interaction.channel_id not in ALLOWED_PROMOTE_CHANNEL_IDS:
            await interaction.response.send_message(
                "This command can only be used in specific channels!",
                ephemeral=True)

            return


        # Check permission
        if not can_demote(interaction):
            await interaction.response.send_message(
                "You do not have the required role to use this command. The Administration team has been notified.",
                ephemeral=False
            )
            # (Optional) log unauthorized usage if you have log_message
            await log_message(
                interaction.client,
                title="Unauthorized /demote Attempt",
                 description=(
                     f"User {interaction.user.mention} (`{interaction.user.id}`) tried to demote <@{discord_id}> ({name}) "
                     "but lacks the required role."
                 ),
                 color=discord.Color.red()
             )
            return

        # Build the first embed (Needs Tags)
        # Add conditional lines if new_rank is one of the special cases
        extra_lines = []
        if new_rank.value == "Cadet":
            extra_lines.append("-Basic Training Certification")
        if new_rank.value == "Probationary Deputy":
            extra_lines.append("-Basic Training Certification")
        if old_rank.value == "Corporal":
            extra_lines.append("-All Leadership roles")
        if old_rank.value == "Trial Corporal":
            extra_lines.append("-All Leadership roles")
        if old_rank.value == "Lieutenant":
            extra_lines.append("-CSSO Command roles")
        if old_rank.value == "Sergeant":
            extra_lines.append("-CSSO Supervisor roles")

        announcement_description = (
            "> **Demotion**\n"
            f"<@{discord_id}>\n"
            f"+{new_rank.value}\n"
            f"-{old_rank.value}"

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

        # Build the second embed (Logging)
        info_str = (
        f"**Name:** {name}\n"
        f"**Discord:** {discord_id}\n"
        f"**Reason:** {reason}\n"
        f"**New-Rank:** {new_rank.value}\n"
        f"**Old-Rank:** {old_rank.value}\n"
        f"**Demoted By:** <@{interaction.user.id}>"
        )
        # Logging embed
        embed_logging = discord.Embed(
            title="Sheriff Demotion Logging",
            color=discord.Color.red(),
            timestamp=datetime.now(EST)
        )
        embed_logging.add_field(name="> **Demotion**", value=info_str, inline=False)
        embed_logging.set_footer(text="Carolina State Sheriff's Office Administration®", icon_url="https://i.imgur.com/wRbvz3o.png")

        # Get the channels
        channel_announcement = interaction.client.get_channel(DEMOTION_CHANNEL_ID)
        channel_logging = interaction.client.get_channel(DEMOTION_LOG_CHANNEL_ID)

        if not channel_announcement:
            await interaction.response.send_message(
                "Error: I cannot find the main demotion channel! Please contact an admin.",
                ephemeral=False
            )
            return

        if not channel_logging:
            await interaction.response.send_message(
                "Error: I cannot find the logging channel! Please contact an admin.",
                ephemeral=False
            )
            return

        # Send to the "Needs Tags" channel
        await channel_announcement.send(
            content="<@&1047611191851221023>",
            embed=embed_announcement
        )


        # Leadership tag request logic
        LEADERSHIP_TAG_REQUEST_CHANNEL_ID = 1047612779097497631  # Same as in promote.py
        tag_request_channel = interaction.client.get_channel(LEADERSHIP_TAG_REQUEST_CHANNEL_ID)

        # Leadership Needs Tags logic (removing roles)
        leadership_needs_tags = None
        if old_rank.value == "Trial Corporal":
            leadership_needs_tags = (
                f"-{old_rank.value}\n"
                f"-Leadership\n"
                f"Removal from leadership discord"
            )
        elif old_rank.value == "Corporal":
            leadership_needs_tags = (
                f"-{old_rank.value}\n"
                f"-Leadership\n"
                f"Removal from leadership discord"
            )
        elif old_rank.value == "Senior Corporal":
            leadership_needs_tags = f"-{old_rank.value}"
        elif old_rank.value == "Sergeant":
            leadership_needs_tags = (
                f"-{old_rank.value}\n"
                f"-Supervisor"
            )
        elif old_rank.value == "Lieutenant":
            leadership_needs_tags = (
                f"-{old_rank.value}\n"
                f"-Command"
            )
        elif old_rank.value == "Major":
            leadership_needs_tags = (
                f"-{old_rank.value}\n"
                f"-High Command"
            )

        # Send Leadership Needs Tags request if applicable
        if leadership_needs_tags and tag_request_channel:
            tag_request_embed = discord.Embed(
                title="Carolina State Sheriff's Office | Needs Tags Removal",
                description=f"> Leadership demotion\n<@{discord_id}>\n{leadership_needs_tags}",
                color=discord.Color.dark_red(),
                timestamp=datetime.now(EST)
            )
            tag_request_embed.set_footer(
                text="Carolina State Sheriff's Office Administration®",
                icon_url="https://i.imgur.com/wRbvz3o.png"
            )
            await tag_request_channel.send(content="<@&1047612726433816668>", embed=tag_request_embed)

        # Send to the logging channel
        await channel_logging.send(embed=embed_logging)

        # Acknowledge success in ephemeral
        await interaction.response.send_message(
            f"**Success!** Demotion posted for {name}.",
            ephemeral=False
        )

        #Optional) log success if you have log_message
        await log_message(
            interaction.client,
            title="Demotion Command Used",
            description=(
            f"User {interaction.user.mention} (`{interaction.user.id}`)\n"
            f"Demoted <@{discord_id}> ({name}) from {old_rank.value} to {new_rank.value}\n"
            f"Reason: {reason}"
             ),
             color=discord.Color.green()
         )
