import discord
from discord import app_commands
from datetime import datetime, timedelta
import asyncio

# Set this when the bot starts
START_TIME = datetime.now()


REQUIRED_ROLE_IDS = [
  1047611161245397009,
  1047611157965455502,   #heads role in all discords
  1047612711099441182,
  1047611180715348060, # pink Bots roles
  1047611169990516887,
  1047612707576221746

]  # Replace with actual role IDs

def has_required_roles(interaction: discord.Interaction) -> bool:
    return any(role.id in REQUIRED_ROLE_IDS for role in interaction.user.roles)


def register_commands(tree: app_commands.CommandTree):
    @tree.command(name="status", description="Displays the bot's current status and statistics.")
    async def status(interaction: discord.Interaction):
        if not has_required_roles(interaction):
            await interaction.response.send_message("You lack permission to use this command.", ephemeral=True)
            await log_message(
                interaction.client,
                title="Unauthorized /status Attempt",
                description=f"User: {interaction.user.mention} (`{interaction.user.id}`) tried to use `/status`.",
                color=discord.Color.red()
            )
            return

        # Calculate latency
        latency = round(interaction.client.latency * 1000)

        # Calculate uptime
        now = datetime.now()
        uptime = now - START_TIME
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes = remainder // 60
        uptime_str = f"{days}d {hours}h {minutes}m"

        # Create embed
        embed = discord.Embed(
            title="🤖 S.U.N.D.A.Y. Status",
            description="Here are my current statistics!",
            color=discord.Color.green()
        )
        embed.add_field(name="Latency:", value=f"{latency}ms", inline=True)
        embed.add_field(name="Uptime:", value=uptime_str, inline=True)
        embed.add_field(name="Last Restart Date:", value=START_TIME.strftime("%A, %B %d %Y"), inline=False)
        embed.add_field(name="Status:", value="🟢 | **All Systems Online!**", inline=False)
        embed.add_field(name="Bot Information:", value="Property of the Carolina State Sheriff's Office", inline=False)
        embed.add_field(name="Bot Version:", value="v2.0.1", inline=True)
        embed.add_field(name="Last Updated:", value="August 6, 2026", inline=True)
        embed.set_footer(
            text="Carolina State Sheriff's Office Administration®",
            icon_url="https://i.imgur.com/wRbvz3o.png"
        )

        await interaction.response.send_message(embed=embed)


    @tree.command(name="tos",description="Get the Terms of Service & Privacy Policy links")
    async def tos(interaction: discord.Interaction):
        """
        Replies with the public URLs for your /tos and /privacy pages.
        """
        # adjust these URLs to wherever you’re hosting the Flask app
        tos_url     = "https://auth.joincsso.org/tos"
        privacy_url = "https://auth.joincsso.org/privacy"

        await interaction.response.send_message(
            f"📄 **Terms of Service:** {tos_url}\n"
            f"🔒 **Privacy Policy:** {privacy_url}",
            ephemeral=False
        )
