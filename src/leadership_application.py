import discord
from discord import app_commands
from datetime import datetime
from utils import log_message

# CONFIGURATION CONSTANTS
REVIEW_CHANNEL_ID = 1124472511590060152
REQUIRED_ROLE_ID = 1047612726433816668
LEADERSHIP_LOG_CHANNEL_ID = 1316233527825666068
CSSO_SUPERVISOR_ROLE_ID = 1047611211979685938

def register_review_command(tree: app_commands.CommandTree):

    @tree.command(name="review-leadership-application", description="Accept or deny a leadership application.")
    @app_commands.describe(
        discord_id="The Discord ID of the applicant.",
        decision="Decision to accept or deny"
    )
    @app_commands.choices(decision=[
        app_commands.Choice(name="Accept", value="accept"),
        app_commands.Choice(name="Deny", value="deny")
    ])
    async def review_leadership_application(
        interaction: discord.Interaction,
        discord_id: str,
        decision: app_commands.Choice[str]
    ):
        # Channel lock
        if interaction.channel_id != REVIEW_CHANNEL_ID:
            return await interaction.response.send_message("❌ You can't use this command in this channel.", ephemeral=True)

        # Role lock
        if not any(role.id == REQUIRED_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)

        # Fetch user
        try:
            user = await interaction.client.fetch_user(int(discord_id))
        except Exception as e:
            return await interaction.response.send_message(f"❌ Could not fetch user: {e}", ephemeral=True)

        # Send public message to leadership log channel
        log_channel = interaction.client.get_channel(LEADERSHIP_LOG_CHANNEL_ID)
        if not log_channel:
            return await interaction.response.send_message("❌ Leadership log channel not found.", ephemeral=True)

        if decision.value == "accept":
            embed = discord.Embed(
                description="Congratulations! Your leadership application has been accepted! "
                            "Welcome to the CSSO leadership team. A sergeant will be in contact with you shortly.",
                color=discord.Color.gold()
            )
            await log_channel.send(content=f"{user.mention} <@&{CSSO_SUPERVISOR_ROLE_ID}>", embed=embed)
            await interaction.response.send_message("Leadership Application accepted! ✅.", ephemeral=False)

        else:
            embed = discord.Embed(
                description="Unfortunately, your leadership application has been denied. "
                            "Feel free to apply again in 24 hours.",
                color=discord.Color.dark_gray()
            )
            await log_channel.send(content=user.mention, embed=embed)
            await interaction.response.send_message("Leadership Application denied! ❌.", ephemeral=False)

        # Send to log system
        await log_message(
            bot=interaction.client,
            title="Leadership Application Reviewed",
            description=(
                f"**Applicant:** {user.mention} (`{user.id}`)\n"
                f"**Reviewed by:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                f"**Decision:** `{decision.name}`"
            ),
            color=discord.Color.green() if decision.value == "accept" else discord.Color.red()
        )

        # Confirm to reviewer
