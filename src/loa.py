import discord
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import json
import os

REQUIRED_ROLE_ID = 1047611188957151362
LOA_ROLE_ID = 1047611213296709652

ADDITIONAL_LOA_GUILDS = {
    1047610191711051866: 1047611175690588211,
    1047610330693509272: 1286773943490969651
}

LOA_LOG_CHANNEL_IDS = [
    1047611344041558117,
    1047611869977919648,
    1047612845149397025
]

LOA_DATA_FILE = "loa_data.json"


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
        guild_id = gr["guild_id"]
        role_id = gr["role_id"]
        guild = bot.get_guild(guild_id)
        if not guild:
            continue
        try:
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
        except discord.NotFound:
            continue
        role = guild.get_role(role_id)
        if role and role in member.roles:
            try:
                await member.remove_roles(role, reason="LOA period expired.")
            except discord.Forbidden:
                pass


async def loa_cleanup_task(bot: discord.Client):
    await bot.wait_until_ready()

    while not bot.is_closed():
        now = datetime.now()
        data = load_loa_data()
        changed = False

        for record in data[:]:
            end_time = datetime.fromisoformat(record["end_time"])
            if now >= end_time:
                user_id = record["discord_id"]
                guild_role_pairs = record["guilds"]
                await remove_loa_roles(bot, user_id, guild_role_pairs)

                concluded_by = bot.user.mention if bot.user else "System"

                for channel_id in LOA_LOG_CHANNEL_IDS:
                    channel = bot.get_channel(channel_id)
                    if channel:
                        async for msg in channel.history(limit=100):
                            if msg.embeds:
                                embed = msg.embeds[0]
                                if str(user_id) in embed.description:
                                    new_embed = embed.copy()
                                    new_embed.color = discord.Color.dark_gray()
                                    new_embed.description += f"\n**Status:** ✅ Concluded\n> **Concluded by:** {concluded_by}"
                                    await msg.edit(embed=new_embed)
                                    break

                data.remove(record)
                changed = True

        if changed:
            save_loa_data(data)

        await asyncio.sleep(60)


def register_commands(tree: app_commands.CommandTree):
    @tree.command(name="loa", description="Put a user on LOA for a specified number of days.")
    @app_commands.describe(
        name="The user's name (e.g., R. Dillon)",
        discord_id="The user's Discord ID (numeric)",
        reason="Reason for LOA",
        time_in_days="Duration in days"
    )
    async def loa(
        interaction: discord.Interaction,
        name: str,
        discord_id: str,
        reason: str,
        time_in_days: int
    ):
        if not any(r.id == REQUIRED_ROLE_ID for r in interaction.user.roles):
            return await interaction.response.send_message(
                "You do not have permission to use this command. This command only works in the HQ discord.",
                ephemeral=True
            )

        await interaction.response.send_message(
            f"Processing LOA for `{name}` (ID: {discord_id}).",
            ephemeral=False
        )

        current_guild = interaction.guild
        if not current_guild:
            return await interaction.followup.send(
                "This command must be used in a guild (server).",
                ephemeral=True
            )

        try:
            user_id = int(discord_id)
        except ValueError:
            return await interaction.followup.send(
                "Invalid Discord ID (must be numeric).",
                ephemeral=True
            )

        member = current_guild.get_member(user_id)
        if not member:
            try:
                member = await current_guild.fetch_member(user_id)
            except discord.NotFound:
                return await interaction.followup.send(
                    f"User with ID {discord_id} not found in this server.",
                    ephemeral=True
                )

        loa_role = current_guild.get_role(LOA_ROLE_ID)
        if not loa_role:
            return await interaction.followup.send(
                "LOA role not found in this server. Please check LOA_ROLE_ID.",
                ephemeral=True
            )
        try:
            await member.add_roles(loa_role, reason=f"LOA assigned by {interaction.user} for {time_in_days} days.")
        except discord.Forbidden:
            return await interaction.followup.send(
                "I do not have permission to assign the LOA role in this server.",
                ephemeral=True
            )

        guild_role_pairs = []
        guild_role_pairs.append({"guild_id": current_guild.id, "role_id": LOA_ROLE_ID})

        for g_id, r_id in ADDITIONAL_LOA_GUILDS.items():
            target_guild = interaction.client.get_guild(g_id)
            if not target_guild:
                continue
            try:
                target_member = target_guild.get_member(user_id) or await target_guild.fetch_member(user_id)
            except discord.NotFound:
                continue

            target_role = target_guild.get_role(r_id)
            if target_role:
                try:
                    await target_member.add_roles(target_role, reason=f"LOA assigned by {interaction.user} for {time_in_days} days.")
                    guild_role_pairs.append({"guild_id": g_id, "role_id": r_id})
                except discord.Forbidden:
                    pass

        start_date = datetime.now()
        end_date = start_date + timedelta(days=time_in_days)
        embed = discord.Embed(
            title="LOA Assignment",
            description=(
                f"> **Name:** {name}\n"
                f"> **Discord ID:** {discord_id}\n"
                f"> **Reason:** {reason}\n"
                f"> **Duration:** {start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}\n"
                f"> **Approved by:** {interaction.user.mention}\n\n"
            ),
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_footer(text="Carolina State Sheriff's Office Administration®", icon_url="https://i.imgur.com/wRbvz3o.png")

        for channel_id in LOA_LOG_CHANNEL_IDS:
            log_channel = interaction.client.get_channel(channel_id)
            if log_channel and isinstance(log_channel, discord.TextChannel):
                await log_channel.send(embed=embed)

        start_time = datetime.now().isoformat()
        end_time = (datetime.now() + timedelta(days=time_in_days)).isoformat()

        data = load_loa_data()
        data.append({
            "discord_id": user_id,
            "name": name,
            "reason": reason,
            "start_time": start_time,
            "end_time": end_time,
            "guilds": guild_role_pairs
        })
        save_loa_data(data)
