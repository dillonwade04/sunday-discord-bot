import discord
from discord import app_commands
from datetime import datetime, timezone

from utils import log_message

LEADERSHIP_VERIFY_CHANNEL_ID = 1117644398382026792  # The channel where this command can be used
VERIFIED_ROLE_ID = 1047612749364080662              # SHIELD Verified role
UNVERIFIED_ROLE_ID = 1050590950541512775            # Unverified role

def register_commands(tree: app_commands.CommandTree):
    @tree.command(name="leadership-verify", description="Verify your account for the CSSO Leadership Discord.")
    async def leadership_verify(interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild

        # Ensure command is used in the correct channel
        if interaction.channel.id != LEADERSHIP_VERIFY_CHANNEL_ID:
            await interaction.response.send_message(
                "❌ This command can only be used in the designated Leadership Verify channel.",
                ephemeral=True
            )
            return

        # ----- Perform your risk assessment checks -----
        passed_checks = 0
        total_checks = 5
        risk_factors = []

        # 1) Check if the account is a bot
        if not user.bot:
            passed_checks += 1
        else:
            risk_factors.append("⚠️ The account is a bot account (high risk).")

        # 2) Check avatar
        if user.avatar is not None:
            passed_checks += 1
            risk_factors.append("✅ The account has a custom avatar (low risk).")
        else:
            risk_factors.append("⚠️ The account has no custom avatar (default avatar).")

        # 3) Check account creation date
        account_age_days = (datetime.now(timezone.utc) - user.created_at).days
        if account_age_days >= 30:
            passed_checks += 1
            risk_factors.append(f"✅ The account was created {account_age_days} days ago (low risk).")
        else:
            risk_factors.append(f"⚠️ The account was created {account_age_days} days ago (high risk).")

        # 4) Check Nitro or server boosting
        if hasattr(user, 'premium_type') and user.premium_type in (1, 2):
            passed_checks += 1
            risk_factors.append("✅ Nitro subscription detected (low risk).")
        elif isinstance(user, discord.Member) and user.premium_since:
            passed_checks += 1
            risk_factors.append("✅ Server boosting detected (low risk).")
        else:
            risk_factors.append("⚠️ No Nitro or server boosting detected (medium risk).")

        # 5) Check shared servers
        mutual_guilds = len(user.mutual_guilds)
        if mutual_guilds > 1:
            passed_checks += 1
            risk_factors.append(f"✅ Shared servers: {mutual_guilds} (low risk).")
        else:
            risk_factors.append("⚠️ The account is only in this server (high risk).")

        # Additional info
        risk_factors.append(f"ℹ️ **Username**: {user.name}#{user.discriminator}")
        risk_factors.append(f"ℹ️ **Shared Servers**: {mutual_guilds}")
        risk_factors.append(f"ℹ️ **Account Creation Date**: {user.created_at.strftime('%B %d, %Y')}")

        # Create the ephemeral embed
        embed = discord.Embed(
            title="Leadership Verification",
            description="Here is the risk assessment for your account:",
            color=discord.Color.blue()
        )
        for factor in risk_factors:
            embed.add_field(name="Assessment", value=factor, inline=False)

        # Check if the user is in the guild
        member = guild.get_member(user.id)
        if not member:
            await interaction.response.send_message("Member not found in the guild.", ephemeral=True)
            return

        # Determine pass or fail
        if passed_checks >= 4:
            # Passed
            embed.add_field(name="Result", value="✅ Verification Passed! Role Assigned.", inline=False)

            # Assign the Verified role, remove the Unverified role
            verified_role = guild.get_role(VERIFIED_ROLE_ID)
            unverified_role = guild.get_role(UNVERIFIED_ROLE_ID)
            if verified_role and unverified_role:
                await member.add_roles(verified_role, reason="Leadership Verification Passed")
                await member.remove_roles(unverified_role, reason="Leadership Verification Passed")

            # Log success
            await log_message(
                interaction.client,
                title="Passed /leadership-verify",
                description=f"User: {interaction.user.mention}",
                color=discord.Color.green(),
            )

            # 1) Send ephemeral embed to user
            await interaction.response.send_message(embed=embed, ephemeral=True)

            # 2) Send a normal (non-ephemeral) message in the **same** channel
            public_embed = discord.Embed(
                title="Leadership Verification",
                description="Verification Status:",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            public_embed.add_field(
                name="Result",
                value=f"I have Verified you into CSSO Leadership, Welcome <@{member.id}>!",
                inline=False
            )
            public_embed.set_footer(
                text="Carolina State Sheriff's Office Administration®",
                icon_url="https://i.imgur.com/wRbvz3o.png"
            )

            # Send it publicly so everyone sees it
            await interaction.followup.send(embed=public_embed, ephemeral=False)

        else:
            # Failed
            embed.add_field(name="Result", value="❌ Verification Failed! High-risk account.", inline=False)

            # Log failure
            await log_message(
                interaction.client,
                title="Failed /leadership-verify",
                description=f"User: {interaction.user.mention}",
                color=discord.Color.red(),
            )

            # Send ephemeral embed to user
            await interaction.response.send_message(embed=embed, ephemeral=True)
