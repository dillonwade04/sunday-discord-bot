import discord
from discord import app_commands
import requests

from config import OAUTH_API_SECRET

OAUTH_SERVER = "https://auth.joincsso.org"
# List of Discord user IDs allowed to use this command
ALLOWED_USER_IDS = [971112440563650580, 333863427812491266, 425063639129522187, 707827105785839646, 825194202479460362, 605710549472247809, 502093975117627423, 846954987334271056, 811387676807790592, 1050918157252051045]

def register_commands(tree: app_commands.CommandTree):
    @tree.command(name="fetch-guilds", description="Fetch a user's joined servers using OAuth2.")
    @app_commands.describe(user="The user to fetch guilds for.")
    async def fetch_guilds(interaction: discord.Interaction, user: discord.User):
        # Permission check: only allow whitelisted users
        if interaction.user.id not in ALLOWED_USER_IDS:
            return await interaction.response.send_message(
                "❌ You do not have permission to use this command.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=False)
        user_id = str(user.id)

        try:
            # Step 1: Check authorization and get token
            check_resp = requests.get(
                f"{OAUTH_SERVER}/check",
                params={"user_id": user_id},
                headers={"X-API-Key": OAUTH_API_SECRET},
                timeout=5,
            )
            if check_resp.status_code != 200:
                return await interaction.followup.send(
                    "⚠️ Failed to contact OAuth server.", ephemeral=True
                )

            data = check_resp.json()
            if not data.get("authorized"):
                return await interaction.followup.send(
                    "❌ That user hasn't completed OAuth2 verification.", ephemeral=True
                )

            token = data.get("token")
            if not token:
                return await interaction.followup.send(
                    "🚫 No access token found for that user.", ephemeral=True
                )

            # Step 2: Fetch the user's guilds from Discord
            headers = {"Authorization": f"Bearer {token}"}
            guild_resp = requests.get(
                "https://discord.com/api/users/@me/guilds", headers=headers, timeout=5
            )
            if guild_resp.status_code != 200:
                return await interaction.followup.send(
                    f"⚠️ Failed to fetch guilds. (HTTP {guild_resp.status_code})", ephemeral=True
                )

            guilds = guild_resp.json()
            if not guilds:
                return await interaction.followup.send(
                    "🕵️ That user is not in any servers (or none are visible).", ephemeral=True
                )

            # Build embed with chunked field values to respect Discord's 1024-char limit
            embed = discord.Embed(
                title=f"Guilds for {user.mention}",
                color=discord.Color.green()
            )

            # Prepare lines and chunk them
            lines = [f"**{g.get('name', 'Unknown')}** (`{g.get('id')}`)" for g in guilds]
            chunks = []
            current = ""
            for line in lines:
                if len(current) + len(line) + 1 > 1024:
                    chunks.append(current)
                    current = ""
                current += line + "\n"
            if current:
                chunks.append(current)

            # Add each chunk as its own field
            for idx, chunk in enumerate(chunks):
                name = "Servers" if idx == 0 else "​"
                embed.add_field(name=name, value=chunk, inline=False)

            await interaction.followup.send(embed=embed, ephemeral=False)

        except Exception as e:
            await interaction.followup.send(
                f"🚨 Unexpected error: `{e}`", ephemeral=True
            )
