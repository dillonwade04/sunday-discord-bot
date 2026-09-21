# Blacklist appeal review commands.

import discord
from discord import app_commands
import aiohttp

from config import (
    DISCORD_APPLICATIONS_WEBHOOK_URL,
    DISCORD_TAGS_WEBHOOK_URL,
)

##########################
# Configuration
##########################

# Required role ID to use /blacklist_review
REQUIRED_ROLE_ID = 1047612711099441182  # <--- Heads role in CSSO leadership

# Allowed channel ID where /blacklist_review can be used
ALLOWED_CHANNEL_ID = 1258901277522264075  # <--- blacklist-appeal channel ID

# Webhooks for "accept" scenario
WEBHOOK_ACCEPT_1 = DISCORD_TAGS_WEBHOOK_URL
WEBHOOK_ACCEPT_2 = DISCORD_APPLICATIONS_WEBHOOK_URL

# Webhook for "deny" scenario
WEBHOOK_DENY_1 = DISCORD_APPLICATIONS_WEBHOOK_URL

def register_commands(tree: app_commands.CommandTree):

    @tree.command(name="review-blacklist", description="Review a CSSO blacklist application.")
    @app_commands.describe(
        discord_id="The numeric Discord ID of the applicant",
        decision="Accept or Deny the application"
    )
    @app_commands.choices(
        decision=[
            app_commands.Choice(name="Accept", value="accept"),
            app_commands.Choice(name="Deny", value="deny")
        ]
    )
    async def review_blacklist(
        interaction: discord.Interaction,
        discord_id: str,
        decision: app_commands.Choice[str]
    ):
        """
        /blacklist_review <discord_id> <Accept|Deny>

        - Must be used in ALLOWED_CHANNEL_ID.
        - The invoker must have the role REQUIRED_ROLE_ID.
        - If Accept:
             * Send TWO webhook messages.
        - If Deny:
             * Send ONE webhook message.
        """

        # 1) Check if correct channel
        if interaction.channel_id != ALLOWED_CHANNEL_ID:
            await interaction.response.send_message(
                f"This command can only be used in <#{ALLOWED_CHANNEL_ID}>.",
                ephemeral=True
            )
            return

        # 2) Check if user has the required role
        roles_of_user = [role.id for role in interaction.user.roles]
        if REQUIRED_ROLE_ID not in roles_of_user:
            await interaction.response.send_message(
                "You lack the required role to use this command.",
                ephemeral=True
            )
            return

        # Acknowledge the command
        await interaction.response.send_message(
            f"I have successfully **{decision.name}** the applicant with user ID `{discord_id}`...",
            ephemeral=False
        )

        if decision.value == "accept":
            # -----------------------
            # ACCEPT SCENARIO
            # -----------------------
            applicant_mention = f"<@{discord_id}>"

            # 1) First webhook
            first_message = (
                f"{applicant_mention}\n"
                "-CSSO Blacklist\n"
                "<@&1215107073893998592>"  # or <@&ROLE_ID> for a real mention
            )
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(WEBHOOK_ACCEPT_1, session=session)
                await webhook.send(content=first_message, username="S.U.N.D.A.Y.", allowed_mentions=discord.AllowedMentions(users=True, roles=True))

            # 2) Second webhook (embed)
            embed = discord.Embed(
                title="CSSO Blacklist Appeal Results..",
                description=(
                    f"Congratulations {applicant_mention}, your blacklist appeal has been accepted for the __Carolina State Sheriff's Office!__\n"
                    f"Feel free to re-apply to CSSO if you're not already in an LEO department.\n"
                    f"We hope you have a great day and thank you for your time while filling out the blacklist appeal!\n\n"
                    f"*Sincerely*\n"
                    f"- {interaction.user.mention}"
                ),
                color=discord.Color.yellow()
            )
            embed.set_footer(text="Carolina State Sheriff's Office Administration®", icon_url="https://i.imgur.com/wRbvz3o.png")

            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(WEBHOOK_ACCEPT_2, session=session)
                await webhook.send(
                    content=applicant_mention,
                    embed=embed,
                    username="S.U.N.D.A.Y."
                )

        else:
            # -----------------------
            # DENY SCENARIO
            # -----------------------
            applicant_mention = f"<@{discord_id}>"
            embed = discord.Embed(
                title="CSSO Blacklist Appeal Results..",
                description=(
                    f"Hello {applicant_mention}, unfortunately your blacklist appeal has been **denied**.\n"
                    f"Do not let this discourage you from appealing your CSSO blacklist; you may re-apply in 48 hours!\n\n"
                    "*Sincerely*\n"
                    "CSSO's Friendly AI - S.U.N.D.A.Y."
                ),
                color=discord.Color.orange()
            )
            embed.set_footer(text="Carolina State Sheriff's Office Administration®", icon_url="https://i.imgur.com/wRbvz3o.png")

            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(WEBHOOK_DENY_1, session=session)
                await webhook.send(
                    content=applicant_mention,
                    embed=embed,
                    username="S.U.N.D.A.Y."
                )

        # (Optional) Log usage
        from utils import log_message
        result_str = "Accepted" if decision.value == "accept" else "Denied"
        await log_message(
            bot=interaction.client,
            title="/review-blacklist Used",
            description=(
                f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                f"**Applicant ID:** {discord_id}\n"
                f"**Decision:** {result_str}"
            ),
            color=discord.Color.blue()
        )
