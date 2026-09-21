import discord
from discord import app_commands
from datetime import datetime
import json
import os

# Constants
REQUIRED_ROLE_ID   = 1047611188957151362  # Human resources role
LOA_LOG_CHANNEL_ID = 1047612845149397025  # Leadership LOA log channel
LOA_DATA_FILE      = "loa_data.json"

# Utility functions
def load_loa_data():
    if os.path.exists(LOA_DATA_FILE):
        try:
            with open(LOA_DATA_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[DEBUG] Error loading LOA data: {e}")
    return []

def save_loa_data(data):
    try:
        with open(LOA_DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[DEBUG] Error saving LOA data: {e}")

async def remove_loa_roles(bot: discord.Client, user_id: int, guild_role_pairs: list):
    for gr in guild_role_pairs:
        guild = bot.get_guild(gr["guild_id"])
        if not guild:
            continue
        try:
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
        except discord.NotFound:
            continue

        role = guild.get_role(gr["role_id"])
        if role and role in member.roles:
            try:
                await member.remove_roles(role, reason="LOA concluded manually.")
            except discord.Forbidden:
                pass

def register_commands(tree: app_commands.CommandTree):
    @tree.command(
        name="loa-conclude",
        description="Conclude a user's LOA and remove their LOA roles."
    )
    @app_commands.describe(discord_id="The user's Discord ID to conclude LOA for.")
    async def loa_conclude(interaction: discord.Interaction, discord_id: str):
        # Permission check
        if not any(r.id == REQUIRED_ROLE_ID for r in interaction.user.roles):
            return await interaction.response.send_message(
                "You lack permission to use this command.",
                ephemeral=True
            )

        await interaction.response.send_message(
            "Processing LOA conclusion...", ephemeral=False
        )

        # Parse & look up record
        try:
            user_id = int(discord_id)
        except ValueError:
            return await interaction.followup.send(
                "Invalid Discord ID format.", ephemeral=True
            )

        data = load_loa_data()
        record = next((e for e in data if e["discord_id"] == user_id), None)
        if not record:
            return await interaction.followup.send(
                "No active LOA record found for this user.", ephemeral=True
            )

        # Remove roles and save
        await remove_loa_roles(interaction.client, user_id, record["guilds"])
        data.remove(record)
        save_loa_data(data)

        # Find the original embed in the log channel
        log_channel = interaction.client.get_channel(LOA_LOG_CHANNEL_ID)
        if not isinstance(log_channel, discord.TextChannel):
            return await interaction.followup.send(
                "Could not access LOA log channel.", ephemeral=True
            )

        async for message in log_channel.history(limit=50):
            if not message.embeds:
                continue
            embed = message.embeds[0]
            if discord_id in embed.description:
                # Make a copy, append status + timestamp, and edit
                edited = embed.copy()
                now = datetime.utcnow()
                time_str = now.strftime("%m/%d/%Y %I:%M %p UTC")

                edited.description = (
                    embed.description.strip()
                    + f"\n**Status:** ✅ Concluded\n"
                    + f"> **Concluded by:** {interaction.user.mention} at {time_str}"
                )
                edited.color     = discord.Color.dark_gray()
                edited.timestamp = now

                await message.edit(embed=edited)
                break

        await interaction.followup.send(
            f"LOA concluded and roles removed for <@{discord_id}>.",
            ephemeral=False
        )
