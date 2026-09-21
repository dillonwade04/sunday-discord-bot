import discord
from discord import app_commands
from datetime import datetime


REQUIRED_ROLE_ID = 1047612726433816668 #command role id in leadership discord
ALLOWED_CHANNEL_ID = 1047612855421251595  # <--- transfers channel ID


def register_commands(tree: app_commands.CommandTree):
    @tree.command(name="transfer-in", description="Log a transferee into CSSO.")
    @app_commands.describe(
        name="Name of the transferee",
        discord_id="Discord ID of the transferee",
        department="Department of origin (the bot will append '- CSSO')",
        rank="Rank of the transferee",
        reason="Reason for transfer",
        length="How long will the transfer period be? 00/00/000 - 00/00/000 format ",
        age="Age of the transferee",
        expectations="Were expectations met? (Y/N)",
        punishments="Any punishments? (Y/N)",
        approved_by="Approved by",
        leadership_approved_by="Leadership approved by (optional)",
        notes="Additional notes (optional)"
    )
    async def transfer_in(
        interaction: discord.Interaction,
        name: str,
        discord_id: str,
        department: str,
        rank: str,
        reason: str,
        length: str,
        age: int,
        expectations: str,
        punishments: str,
        approved_by: str,
        leadership_approved_by: str = None,
        notes: str = None,
    ):

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


        try:


            # First Embed
            logging_embed = discord.Embed(
                title="Carolina State Sheriff's Office Logging System",
                description=f"The transfer from {department} has been successfully logged.",
                color=discord.Color.green()
            )

            # Append '- CSSO' to the department
            department = f"{department} - CSSO"

            logging_embed.set_footer(
                text="Carolina State Sheriff's Office Administration®",
                icon_url="https://i.imgur.com/wRbvz3o.png"
            )

            # Second Embed
            log_embed = discord.Embed(
                title="Carolina State Sheriff's Office Log",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )

            # Add all information in one field
            info = (
                f"> **Name:** {name}\n"
                f"> **Discord:** <@{discord_id}>\n"
                f"> **Discord-ID:** {discord_id}\n"
                f"> **Department:** {department}\n"
                f"> **Rank:** {rank}\n"
                f"> **Reason:** {reason}\n"
                f"> **Length:** {length}\n"
                f"> **Age:** {age}\n"
                f"> **Expectations Met:** {expectations}\n"
                f"> **Punishments:** {punishments}\n"
                f"> **Notes:** {notes if notes else 'No additional notes.'}\n"
                f"> **Approved By:** {approved_by}\n"
            )

            log_embed.add_field(name="**__CSSO Transfer In__**", value=info, inline=False)

            # Footer
            log_embed.set_footer(
                text="Carolina State Sheriff's Office Administration®",
                icon_url="https://i.imgur.com/wRbvz3o.png"
            )


            # Send both embeds to the same channel
            await interaction.response.send_message(embeds=[logging_embed, log_embed])

        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while processing the transfer: {e}",
                ephemeral=True
            )


    @tree.command(name="transfer-out", description="Will log a transfer out of CSSO.")
    @app_commands.describe(
        name="Name of the transferee",
        discord_id="Discord ID of the transferee",
        department="Department of deputy is transferring to. (the bot will append 'CSSO- ')",
        rank="Rank of the transferee",
        reason="Reason for transfer",
        length="How long will the transfer period be? 00/00/000 - 00/00/000 format ",
        age="Age of the transferee",
        expectations="Were expectations met? (Y/N)",
        punishments="Any punishments? (Y/N)",
        approved_by="Approved by",
        leadership_approved_by="Leadership approved by (optional)",
        notes="Additional notes (optional)"
    )
    async def transfer_out(
        interaction: discord.Interaction,
        name: str,
        discord_id: str,
        department: str,
        rank: str,
        reason: str,
        length: str,
        age: int,
        expectations: str,
        punishments: str,
        approved_by: str,
        leadership_approved_by: str = None,
        notes: str = None,
    ):
        try:

            # First Embed
            logging_embed = discord.Embed(
                title="Carolina State Sheriff's Office Logging System",
                description=f"The transfer into {department} has been successfully logged.",
                color=discord.Color.green()
            )

            # Append '- CSSO' to the department
            department = f"CSSO - {department}"

            logging_embed.set_footer(
                text="Carolina State Sheriff's Office Administration®",
                icon_url="https://i.imgur.com/wRbvz3o.png"
            )

            #second embed
            log_embed = discord.Embed(
                title="Carolina State Sheriff's Office Log",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )

            # Add all information in one field
            info = (
                f"> **Name:** {name}\n"
                f"> **Discord:** <@{discord_id}>\n"
                f"> **Discord-ID:** {discord_id}\n"
                f"> **Department:** {department}\n"
                f"> **Rank:** {rank}\n"
                f"> **Reason:** {reason}\n"
                f"> **Length:** {length}\n"
                f"> **Age:** {age}\n"
                f"> **Expectations Met:** {expectations}\n"
                f"> **Punishments:** {punishments}\n"
                f"> **Notes:** {notes if notes else 'No additional notes.'}\n"
                f"> **Approved By:** {approved_by}\n"
            )

            log_embed.add_field(name="**__CSSO Transfer Out__**", value=info, inline=False)

            # Footer
            log_embed.set_footer(
                text="Carolina State Sheriff's Office Administration®",
                icon_url="https://i.imgur.com/wRbvz3o.png"
            )


            # Send both embeds to the same channel
            await interaction.response.send_message(embeds=[logging_embed, log_embed])

        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while processing the transfer: {e}",
                ephemeral=True
            )
