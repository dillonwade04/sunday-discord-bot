# backend.py

import discord
from discord import app_commands
import sys
import datetime
import os

# Import log_message from utils.py
from utils import log_message

# List of role IDs allowed to use these commands
ALLOWED_ROLE_IDS = [
    1047611161245397009,  # Heads role (leadership discord)
    1047611157965455502,    #heads role subdivision
    1047612711099441182,# Heads role (CSSO HQ)
    1047611180715348060, # pink Bots roles
    1047611169990516887,
    1047612707576221746

  # ... add more if needed
]

# Save the bot's start time
START_TIME = datetime.datetime.now()


def has_required_roles(interaction: discord.Interaction) -> bool:
    """
    Checks if the user invoking the command has any of the roles
    specified in ALLOWED_ROLE_IDS.
    """
    user = interaction.user
    if isinstance(user, discord.Member):
        user_role_ids = [role.id for role in user.roles]
        return any(role_id in ALLOWED_ROLE_IDS for role_id in user_role_ids)
    return False


def register_commands(tree: app_commands.CommandTree):
    @tree.command(name="ping", description="Check the bot's latency.")
    async def ping_command(interaction: discord.Interaction):
        if not has_required_roles(interaction):
            await interaction.response.send_message(
                "You lack permission to use this command.",
                ephemeral=True  # Changed to True for consistency
            )
            # Log unauthorized attempt
            await log_message(
                interaction.client,  # pass the bot client
                title="Unauthorized /ping Attempt",
                description=(
                    f"User: {interaction.user.mention} (`{interaction.user.id}`)\n"
                    "Tried to use `/ping` but does not have an allowed role."
                ),
                color=discord.Color.red()
            )
            return

        # Authorized usage
        latency_ms = round(interaction.client.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! **Latency:** {latency_ms}ms")

        # Log successful usage
        await log_message(
            interaction.client,
            title="Ping Command Used",
            description=(
                f"User: {interaction.user.mention} (`{interaction.user.id}`)\n"
                f"Latency: {latency_ms}ms"
            ),
            color=discord.Color.green()
        )

    @tree.command(name="restart", description="Restart the bot. DO NOT USE.")
    async def restart_command(interaction: discord.Interaction):
        """
        Shuts down the bot with exit code 0.
        Rely on your hosting environment to auto-restart.
        """
        if not has_required_roles(interaction):
            await interaction.response.send_message(
                "You lack permission to use this command.",
                ephemeral=True  # Changed to True for consistency
            )
            # Log unauthorized attempt
            await log_message(
                interaction.client,
                title="Unauthorized /restart Attempt",
                description=(
                    f"User: {interaction.user.mention} (`{interaction.user.id}`)\n"
                    "Tried to use `/restart` but does not have an allowed role."
                ),
                color=discord.Color.red()
            )
            return

        # Authorized usage
        await interaction.response.send_message("Bot is restarting...", ephemeral=True)

        # Log the restart
        await log_message(
            interaction.client,
            title="Restart Command Used",
            description=(
                f"User: {interaction.user.mention} (`{interaction.user.id}`)\n"
                "Bot is shutting down..."
            ),
            color=discord.Color.green()
        )

        # Close the bot (logout), then exit the process
        await interaction.client.close()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    @tree.command(name="clear", description="Delete a specified number of messages in the channel.")
    @app_commands.describe(amount="The number of messages to delete (1-100).")
    async def clear(interaction: discord.Interaction, amount: int):
        # Check if the user has Manage Messages permission
        if not interaction.channel.permissions_for(interaction.user).manage_messages:
            await interaction.response.send_message(
                "⚠️ You don't have the required permissions to use this command.",
                ephemeral=True
            )
            return

        # Validate the amount
        if amount < 1 or amount > 100:
            await interaction.response.send_message(
                "⚠️ Please specify a number between 1 and 100.",
                ephemeral=True
            )
            return

        # Try to delete the messages
        try:
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.response.send_message(
                f"✅ Successfully deleted {len(deleted)} messages.",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "⚠️ I don't have the required permissions to delete messages in this channel.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"⚠️ An error occurred: {e}",
                ephemeral=True
            )



# Legacy helper retained for compatibility.
async def on_message(message: discord.Message):
    # DM Logs
    # Ignore messages from other bots
    if message.author.bot:
        return

    # Check if the message is a DM (i.e., not from a guild)
    if message.guild is None:
        # Define your log channel ID here (replace with your actual channel ID)
        LOG_CHANNEL_ID = 1325715850434707517
        log_channel = message.client.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            content = message.content or "No text content"
            dm_log = (
                f"**DM received from {message.author} (`{message.author.id}`):**\n"
                f"{content}"
            )
            await log_channel.send(dm_log)
            # If there are attachments, log their URLs as well
            if message.attachments:
                attachments = "\n".join(attachment.url for attachment in message.attachments)
                await log_channel.send(f"Attachments:\n{attachments}")
