# application_review.py

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

# Required role ID to use /review-application
REQUIRED_ROLE_ID = 1047612736823099484  # <--- Supervisor role ID leadership discord

# Allowed channel ID where /review-application can be used
ALLOWED_CHANNEL_ID = 1047612816523276319  # <--- applications channel ID
# Webhooks for "accept" scenario
WEBHOOK_ACCEPT_1 = DISCORD_TAGS_WEBHOOK_URL
WEBHOOK_ACCEPT_2 = DISCORD_APPLICATIONS_WEBHOOK_URL

# Webhook for "deny" scenario
WEBHOOK_DENY_1 = DISCORD_APPLICATIONS_WEBHOOK_URL

def register_commands(tree: app_commands.CommandTree):
    """
    Call register_commands(tree) from your main bot file, then sync in on_ready().
    """

    @tree.command(name="review-application", description="Review a CSSO application.")
    @app_commands.describe(
        discord_id="The numeric Discord ID of the applicant",
        decision="Accept or Deny the application",
        reason="Reason for denial (only required if decision=deny)"
    )
    @app_commands.choices(
        decision=[
            app_commands.Choice(name="Accept", value="accept"),
            app_commands.Choice(name="Deny",   value="deny")
        ]
    )
    async def review_application(
        interaction: discord.Interaction,
        discord_id: str,
        decision: app_commands.Choice[str],
        reason: str = None
    ):
        """
        /review-application <discord_id> <Accept|Deny> [reason]

        - Must be used in ALLOWED_CHANNEL_ID
        - The invoker must have the role REQUIRED_ROLE_ID
        - If Accept:
             * reason optional
             * Send TWO webhook messages
        - If Deny:
             * reason required
             * Send ONE webhook message
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

        # 3) Validate reason if denying
        if decision.value == "deny" and (not reason or reason.strip() == ""):
            await interaction.response.send_message(
                "You must provide a reason when denying an application.",
                ephemeral=True
            )
            return

        # Acknowledge ephemeral
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
                "+CSSO\n"
                "+CSSO Recruit\n"
                f"<@&1215107073893998592>"
            )
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(WEBHOOK_ACCEPT_1, session=session)
                await webhook.send(content=first_message, username="S.U.N.D.A.Y.", allowed_mentions=discord.AllowedMentions(roles=True, users=True))

            # 2) Second webhook (embed)

            embed = discord.Embed(
                title="CSSO Application Results..",
                description=(
                    f"Congratulations {applicant_mention}, you have been **ACCEPTED** into the __Carolina State Sheriff's Office!__\n"
                    f"Please reference the <#587657461863809035> channel.\n"
                    f"We hope you have a Great day and we thank you for your time while filling out the application!\n\n"
                    f"*Sincerely*\n"
                    f"- {interaction.user.mention}"
                ),
                color=discord.Color.green()
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
            # reason required
            # -----------------------
            applicant_mention = f"<@{discord_id}>"
            embed = discord.Embed(
                title="CSSO Application Results..",
                description=(
                    f"Hello {applicant_mention}, unfortunately your application has been **denied** "
                    f"due but not limited to: __{reason}__. Do not let this discourage you into joining CSSO, you may re-apply in 48 hours!\n\n"
                    "*Sincerely*\n"
                    "CSSO's Friendly AI - S.U.N.D.A.Y."
                ),
                color=discord.Color.red()
            )
            embed.set_footer(text="Carolina State Sheriff's Office Administration®", icon_url="https://i.imgur.com/wRbvz3o.png")

            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(WEBHOOK_DENY_1, session=session)
                await webhook.send(
                    content=applicant_mention,
                    embed=embed,
                    username="S.U.N.D.A.Y."
                )

        #  Log usage
        from utils import log_message
        result_str = "Accepted" if decision.value == "accept" else "Denied"
        await log_message(
             bot=interaction.client,
             title="/review-application Used",
             description=(
               f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
               f"**Applicant ID:** {discord_id}\n"
               f"**Decision:** {result_str}\n"
               f"**Reason:** {reason if reason else 'N/A'}"
           ),
           color=discord.Color.blue()
       )
