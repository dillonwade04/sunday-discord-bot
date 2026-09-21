# misc.py
import discord
from discord import app_commands
from datetime import datetime
import pytz
import asyncio

from utils import log_message

# Roles allowed to use /promote
ROLE_IDS = [
    1047611216580849664,
    1047612741235523654,
    1047611180715348060, # pink Bots roles
    1047611169990516887,
    1047612707576221746
# CSSO Leadership roles from both discords.
    # ... add more role IDs if needed
]

def can_use(interaction: discord.Interaction) -> bool:
    """Returns True if the user has any of the allowed role IDs."""
    return any(role.id in ROLE_IDS for role in interaction.user.roles)

def register_commands(tree: app_commands.CommandTree):
    """
    Call this function from your main bot file (e.g. bot.py)
    to register the /promote slash command.
    """

    @tree.command(name="generate-invite", description="Generate a one-use, 30-minute invite link.")
    async def generate_invite(interaction: discord.Interaction):
        """
        Creates an invite link that can only be used once,
        and expires after 30 minutes (1800 seconds).
        """
        if not can_use(interaction):
            await interaction.response.send_message(
                "You do not have the required role to use this command. The Administration team has been notified.",
                ephemeral=True
            )
            return

        # Ensure the bot/user has "Create Invite" permission in the current channel
        channel = interaction.channel

        try:
            invite = await channel.create_invite(
                max_uses=1,        # The invite can only be used once
                max_age=1800,      # Invite link expires after 1800 seconds (30 minutes)
                unique=True,
                reason=f"Slash command /generate-invite used by {interaction.user}"
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                "I don't have permission to create invites here!",
                ephemeral=True
            )
        except discord.HTTPException:
            return await interaction.response.send_message(
                "Something went wrong while creating the invite. Please try again later.",
                ephemeral=True
            )

        # Respond with the invite link
        # Shown publicly, so ephemeral=False
        await interaction.response.send_message(
            content=(
                "**Here is a ONE use 30 Minute invite!**\n"
                f"{invite.url}"
            ),
            ephemeral=True
        )

    @tree.command(name="echo", description="Repeats the provided text back to you.")
    @app_commands.describe(message="The text you want the bot to echo.")
    async def echo(interaction: discord.Interaction, message: str):
        """A simple echo command that repeats your input."""
        await interaction.response.send_message(f"You said: {message}", ephemeral=False)

    @tree.command(name="reminder", description="Set a reminder for yourself.")
    @app_commands.describe(
        minutes="How many minutes from now to remind you?",
        message="What do you want to be reminded about?"
    )
    async def reminder(
        interaction: discord.Interaction,
        minutes: int,
        message: str
    ):
        """
        Schedules a reminder for 'minutes' from now with the given 'message'.
        After the time elapses, the bot sends a follow-up message (pinging the user).
        """
        # 1. Respond immediately (ephemeral so only the user sees it).
        await interaction.response.send_message(
            f"Okay, I'll remind you in {minutes} minute(s) about: {message}",
            ephemeral=True
        )

        # 2. Sleep for the specified amount of minutes.
        await asyncio.sleep(minutes * 60)

        # 3. Send the reminder. You could either:
        #    - ping them in the same channel, or
        #    - DM them directly.
        # Here, we'll ping them in the same channel if possible.
        channel = interaction.channel
        if channel is not None:
            await channel.send(
                f"{interaction.user.mention} Reminder: {message}"
            )
        else:
            # If for some reason we don't have the channel reference,
            # try sending them a DM.
            await interaction.user.send(
                f"Reminder from {interaction.guild.name}:\n{message}"
        )
