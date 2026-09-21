import discord
from discord import app_commands
import aiohttp
from datetime import datetime, timezone

API_URL = "https://ccd.bureauofcivilians.com/api/public/active-warrants"

ALLOWED_ROLE_NAMES = ["Deputy I", "Sheriff's Deputy", "Leadership", "Basic Training Certification"]

def can_use(interaction: discord.Interaction) -> bool:
    return any(role.name in ALLOWED_ROLE_NAMES for role in interaction.user.roles)

def format_discord_time(iso_string: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        unix_time = int(dt.timestamp())
        return f"<t:{unix_time}:F>"
    except:
        return iso_string

async def fetch_active_warrants():
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as resp:
            if resp.status != 200:
                raise Exception(f"API returned status {resp.status}")
            return await resp.json()

def register_commands(tree: app_commands.CommandTree):
    @tree.command(name="activewarrants", description="View currently active warrants.")
    async def activewarrants(interaction: discord.Interaction):
        if not can_use(interaction):
            return await interaction.response.send_message(
                "❌ You do not have permission to use this command.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        try:
            data = await fetch_active_warrants()

            if not data.get("success"):
                return await interaction.followup.send(
                    "❌ Failed to fetch active warrants."
                )

            warrants = data.get("warrants", [])

            if not warrants:
                embed = discord.Embed(
                    title="Active Warrants",
                    description="There are currently no active warrants.",
                    color=discord.Color.green()
                )
                embed.set_footer(text="S.U.N.D.A.Y.")
                return await interaction.followup.send(embed=embed, ephemeral=True)

            embed = discord.Embed(
                title="Active Warrants",
                description=f"Found **{len(warrants)}** active warrant(s).",
                color=discord.Color.orange()
            )

            for i, warrant in enumerate(warrants[:10], start=1):
                warrant_type = warrant.get("type", "Unknown")
                requested_by = warrant.get("requested_by", "Unknown")
                requested_on = format_discord_time(warrant.get("requested_on", "Unknown"))
                public_url = warrant.get("public_url", None)
                warrant_id = warrant.get("warrant_id", "Unknown")

                value = (
                    f"**Type:** {warrant_type}\n"
                    f"**Requested By:** {requested_by}\n"
                    f"**Requested On:** {requested_on}\n"
                    f"**Warrant ID:** `{warrant_id}`\n"
                )

                if public_url:
                    value += f"[View Warrant]({public_url})"

                embed.add_field(
                    name=f"Warrant #{i}",
                    value=value,
                    inline=False
                )

            if len(warrants) > 10:
                embed.set_footer(
                    text=f"S.U.N.D.A.Y. • Showing first 10 of {len(warrants)} warrants"
                )
            else:
                embed.set_footer(text="S.U.N.D.A.Y.")

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error fetching active warrants: `{str(e)}`"
            )
