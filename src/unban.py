# unban.py

import discord
from discord.ext import tasks
from discord import app_commands
import pytz
import os
import sys
import asyncio
from datetime import datetime
from utils import log_message


# The channel ID where unban requests are posted
REQUEST_UNBAN_CHANNEL_ID = 1116890110009561128

# The role ID to mention when a request is made
REQUEST_UNBAN_ROLE_ID = 1047612711099441182

def register_commands(tree: app_commands.CommandTree):
    @tree.command(name="request-unban", description="Request an unban for a user.")
    @app_commands.describe(
        name="The name (in-game name or user nickname) of the person to unban",
        user_id="The person's Discord user ID",
        reason="Reason for requesting this unban"
    )
    async def request_unban(
        interaction: discord.Interaction,
        name: str,
        user_id: str,
        reason: str
    ):
        """
        Sends an embed to REQUEST_UNBAN_CHANNEL_ID, pings REQUEST_UNBAN_ROLE_ID,
        and includes details about the user to be unbanned.
        """

        # 1) Acknowledge the command (ephemeral so only the invoker sees it)
        await interaction.response.send_message(
            f"**Request sent** for unbanning `{name}`. Thank you!",
            ephemeral=True
        )

        # 2) Build the embed
        embed = discord.Embed(
            title="Unban Request",
            description="A request to unban someone has been submitted.",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Name to Unban",   value=name,          inline=False)
        embed.add_field(name="Discord ID",      value=user_id,       inline=False)
        embed.add_field(name="Reason",          value=reason,        inline=False)
        embed.add_field(
            name="Requested By",
            value=f"{interaction.user.mention} (`{interaction.user.id}`)",
            inline=False
        )
        embed.set_footer(text="Unban Request")

        # 3) Fetch the target channel
        channel = interaction.client.get_channel(REQUEST_UNBAN_CHANNEL_ID)
        if channel is None:
            # If we can't find the channel, there's not much we can do
            return

        # 4) Mention the role and send the embed
        await channel.send(
            content=f"<@&{REQUEST_UNBAN_ROLE_ID}>",  # Ping the role
            embed=embed
        )

        await log_message(
            interaction.client,
            title="/unban request used.",
            description=(
                f"User {interaction.user.mention} (`{interaction.user.id}`)\n"
            ),
            color=discord.Color.orange()
        )
