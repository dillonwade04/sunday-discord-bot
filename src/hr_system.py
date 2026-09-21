
import requests

from config import OAUTH_API_SECRET

OAUTH_BASE_URL = "https://auth.joincsso.org"  # Replace with your deployed OAuth2 site URL


def check_user_authorization(user_id: int) -> bool:
    try:
        response = requests.get(
            f"{OAUTH_BASE_URL}/check",
            params={"user_id": user_id},
            headers={"X-API-Key": OAUTH_API_SECRET},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("authorized", False)
        return False
    except Exception as e:
        print(f"[OAuth Check] Error checking authorization: {e}")
        return False

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import os
import io
import logging
from chat_exporter import export

# HR ticket configuration and persistent views.

# Setup logging
logger = logging.getLogger(__name__)

# Role and Category IDs
HR_CATEGORY_ID = 1047611285967220836  # HR Ticket category ID
HR_ROLE_ID = 1047611188957151362  # HR Role ID
HR_SUPERVISION_ROLE_ID = 1047611188151853136  # HR Supervision Role ID
HR_HEADS_ROLE_ID = 1047611161245397009  # HR Heads Role ID
LOGGING_CHANNEL_ID = 1047611340447039558  # Logging channel ID

# Ensure the "transcripts" folder exists
os.makedirs("transcripts", exist_ok=True)


async def generate_transcript(channel):
    try:
        # Export the transcript
        transcript = await export(
            channel,
            limit=None,  # Set to None to fetch all messages
            tz_info="UTC",  # Timezone for the transcript
            military_time=True,  # Use 24-hour format for times
            fancy_times=True,  # Enable 'fancy' timestamps like Today/Yesterday
        )

        if transcript is None:
            raise ValueError("Failed to generate transcript: No data returned.")

        # Ensure the "transcripts" folder exists
        os.makedirs("transcripts", exist_ok=True)

        # Save the transcript to a file
        safe_channel_name = ''.join(c for c in channel.name if c.isalnum() or c in ('-', '_')).rstrip()
        file_path = f"transcripts/{safe_channel_name}.html"

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(transcript)

        print(f"Transcript successfully saved to {file_path}.")
        return file_path

    except Exception as e:
        print(f"Failed to generate transcript for {channel.name}: {e}")
        raise e


class ConfirmCloseView(discord.ui.View):
    def __init__(self, ticket_channel):
        super().__init__(timeout=None)
        self.ticket_channel = ticket_channel

    @discord.ui.button(label="Confirm Close", style=discord.ButtonStyle.danger, custom_id="confirm_close_button")
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if not check_user_authorization(user_id):
            await interaction.response.send_message(
                f'🔐 Please verify your account by logging in: [Click Here]({OAUTH_BASE_URL}/?user_id={user_id})',
                ephemeral=True
            )
            return
        try:
            # Use interaction.channel inside this method:
            channel = interaction.channel

            # Generate transcript
            transcript_path = await generate_transcript(channel)
            logging_channel = interaction.guild.get_channel(LOGGING_CHANNEL_ID)

            if logging_channel:
                await logging_channel.send(
                    f"📄 **Ticket Transcript:** {channel.name} (closed by {interaction.user.mention})",
                    file=discord.File(transcript_path),
                )
                embed = discord.Embed(
                    title="📕 **Ticket Action** 📕",
                    color=discord.Color.red()
                )
                embed.add_field(name="Logged Info", value="Ticket Transcribed", inline=False)
                embed.add_field(name="Transcribed By", value=interaction.user.mention, inline=True)
                embed.add_field(name="Ticket Name", value=channel.name, inline=True)
                embed.add_field(name="Ticket Owner", value=f"<@{channel.topic}>", inline=True)
                embed.add_field(name="Panel", value="Sheriff Human Resources", inline=False)
                embed.set_footer(
                    text="Carolina State Sheriff's Office Administration®",
                    icon_url="https://i.imgur.com/wRbvz3o.png"
                )

                await logging_channel.send(embed=embed)

            os.remove(transcript_path)
            # Delete the channel
            await channel.delete(reason=f"Ticket closed by {interaction.user}.")
            await interaction.response.send_message("✅ Ticket has been successfully closed.", ephemeral=True)
        except Exception as e:
            logger.exception(f"Error occurred while closing the ticket: {e}")
            await interaction.response.send_message(f"⚠️ Error closing ticket: {e}", ephemeral=True)



class HRChannelControlsView(discord.ui.View):
    def __init__(self, ticket_channel):
        super().__init__(timeout=None)
        self.ticket_channel = ticket_channel  # It's okay to keep it, but you won't use it after restart.

    @discord.ui.button(label="Close HR Ticket", style=discord.ButtonStyle.success, custom_id="close_hr_ticket")
    async def close_hr_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if not check_user_authorization(user_id):
            await interaction.response.send_message(
                f'🔐 Please verify your account by logging in: [Click Here]({OAUTH_BASE_URL}/?user_id={user_id})',
                ephemeral=True
            )
            return
        embed = discord.Embed(
            title="Are you sure?",
            description="Click the button below to confirm closing this ticket.",
            color=discord.Color.red()
        )
        # Instead of passing self.ticket_channel, pass interaction.channel to ConfirmCloseView
        await interaction.response.send_message(
            embed=embed,
            view=ConfirmCloseView(interaction.channel),
            ephemeral=True
        )

    @discord.ui.button(label="Lock to HR Supervision", style=discord.ButtonStyle.danger, custom_id="lock_hr_supervision")
    async def lock_hr_supervision(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if not check_user_authorization(user_id):
            await interaction.response.send_message(
                f'🔐 Please verify your account by logging in: [Click Here]({OAUTH_BASE_URL}/?user_id={user_id})',
                ephemeral=True
            )
            return
        guild = interaction.guild
        role = guild.get_role(HR_SUPERVISION_ROLE_ID)
        if not role:
            await interaction.response.send_message("HR Supervision role not found.", ephemeral=True)
            return

        # Use interaction.channel instead of self.ticket_channel
        channel = interaction.channel
        overwrites = channel.overwrites

        # ***ADDED CODE***
        # Remove the Human Resources role from the channel overwrites.
        hr_role = guild.get_role(HR_ROLE_ID)
        if hr_role in overwrites:
            del overwrites[hr_role]
        # ***END OF ADDED CODE***

        overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        await channel.edit(overwrites=overwrites)
        embed = discord.Embed(
            title="Ticket Locked to HR Supervision",
            description="⚠️ This ticket has been locked to HR Supervision. ⚠️",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @discord.ui.button(label="Lock to Heads", style=discord.ButtonStyle.primary, custom_id="lock_hr_heads")
    async def lock_heads(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if not check_user_authorization(user_id):
            await interaction.response.send_message(
                f'🔐 Please verify your account by logging in: [Click Here]({OAUTH_BASE_URL}/?user_id={user_id})',
                ephemeral=True
            )
            return
        guild = interaction.guild
        role = guild.get_role(HR_HEADS_ROLE_ID)
        if not role:
            await interaction.response.send_message("HR Heads role not found.", ephemeral=True)
            return

        channel = interaction.channel
        overwrites = channel.overwrites

        # Remove the Human Resources role if present.
        hr_role = guild.get_role(HR_ROLE_ID)
        if hr_role in overwrites:
            del overwrites[hr_role]

        # Remove the HR Supervision role if present.
        hr_supervision_role = guild.get_role(HR_SUPERVISION_ROLE_ID)
        if hr_supervision_role in overwrites:
            del overwrites[hr_supervision_role]

        # Add the HR Heads role.
        overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        await channel.edit(overwrites=overwrites)
        embed = discord.Embed(
            title="Ticket Locked to Heads",
            description="⚠️ This ticket has been locked to CSSO Department Heads. Expect a slower response. ⚠️",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)




class HRPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📩 Create HR Ticket",
        style=discord.ButtonStyle.primary,
        custom_id="create_hr_ticket"  # This was already present
    )
    async def create_hr_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if not check_user_authorization(user_id):
            await interaction.response.send_message(
                f'🔐 Please verify your account by logging in: [Click Here]({OAUTH_BASE_URL}/?user_id={user_id})',
                ephemeral=True
            )
            return
        guild = interaction.guild
        category = guild.get_channel(HR_CATEGORY_ID)

        if not category:
            await interaction.response.send_message("HR category not found. Please contact an admin.", ephemeral=True)
            logger.error("HR category not found.")
            return

        # Sanitize the username to remove special characters for the channel name
        sanitized_username = ''.join(c for c in interaction.user.name if c.isalnum() or c in ('-', '_')).lower()
        channel_name = f"hr-ticket-{sanitized_username}"

        # Check for existing channel with the sanitized username
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message("You already have an open ticket.", ephemeral=True)
            logger.info(f"User {interaction.user} attempted to create multiple tickets.")
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(HR_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        try:
            ticket_channel = await guild.create_text_channel(
                name=f"hr-ticket-{interaction.user}",
                category=category,
                overwrites=overwrites,
                reason=f"HR Ticket created by {interaction.user}."
            )
            logger.info(f"HR Ticket channel {ticket_channel.name} created for {interaction.user}.")

            embed = discord.Embed(
                title="Welcome to CSSO Human Resources",
                description="",
                color=discord.Color.blue()
            )
            embed.add_field(name="> CSSO HR Formats", value="""
\n\u200b
> **LOA FORMAT**\nName:\nDiscord:\nDiscord ID:\nReason:\nDuration:
> **TRANSFER OUT FORMAT**\nName:\nDiscord:\nDiscord ID:\nRank in CSSO:\nReason:\nSub Divisions:\nAge:
> **RESIGNATION FORMAT**\nName:\nDiscord:\nDiscord ID:\nReason:
> **RESERVES FORMAT**\nName:\nDiscord:\nDiscord ID:\nReason:\nDuration: *(Note: Corporal +)*
> **NAME CHANGE FORMAT**\nCurrent Name:\nNew Name:\nRank:\nReason for Change:
> **LOW/ALTERED HOURS FORMAT**\nName:\nDiscord:\nDiscord ID:\nReason:\nDuration:
""", inline=False)
            embed.set_footer(
                text="Carolina State Sheriff's Office Administration®",
                icon_url="https://i.imgur.com/wRbvz3o.png"
            )

            view = HRChannelControlsView(ticket_channel)
            await ticket_channel.send(
                content=(
                    f"Welcome to the CSSO Human Resources {interaction.user.mention}. "
                    f"Please look at one of the formats that is posted below and "
                    f"one of our <@&{HR_ROLE_ID}> Agents will assist you. If you don't receive a response "
                    f"within 15 minutes please feel free to ping an online Human Resource Agent."
                    f"*(They will be on the right-hand side of the screen.)*"
                ),
                embed=embed,
                view=view
            )
            await interaction.response.send_message(
                f"✅ HR Ticket created: {ticket_channel.mention}",
                ephemeral=True
            )
        except Exception as e:
            logger.exception(f"Failed to create HR Ticket for {interaction.user}: {e}")
            await interaction.response.send_message(
                f"⚠️ Failed to create HR Ticket: {e}",
                ephemeral=True
            )


def register_commands(tree: app_commands.CommandTree):

    @tree.command(name="setup-hr-panel", description="Set up the HR panel in a channel.")
    @app_commands.describe(channel="The channel to send the HR panel to.")
    async def setup_hr_panel(interaction: discord.Interaction, channel: discord.TextChannel):
        try:
            logger.info(f"setup-hr-panel triggered by {interaction.user} in {channel.name}.")

            # Defer response
            await interaction.response.defer(ephemeral=True)

            logger.info("Creating HR panel embed and view.")
            view = HRPanelView()
            embed = discord.Embed(
                title="CSSO HR Panel",
                description=(
                    "### Carolina State Sheriffs Office Human Resources\n\n"
                    "To create a CSSO Support ticket and speak to a Human Resources agent, click the button below."
                ),
                color=discord.Color.blue()
            )
            embed.set_footer(
                text="Carolina State Sheriff's Office Administration®",
                icon_url="https://i.imgur.com/wRbvz3o.png"
            )

            # Send the embed with the view
            await channel.send(embed=embed, view=view)

            logger.info(f"HR panel sent to {channel.name}.")

            # Respond to the interaction
            await interaction.followup.send("✅ HR panel has been successfully set up.", ephemeral=True)
        except Exception as e:
            logger.exception(f"Error in setup-hr-panel: {e}")
            await interaction.followup.send(f"⚠️ Failed to set up HR panel: {e}", ephemeral=True)


    @tree.command(name="hr-user-add", description="Add a user to the HR ticket.")
    @app_commands.describe(user="The user to add to this HR ticket.")
    async def hr_user_add(interaction: discord.Interaction, user: discord.User):
        """Adds a specified user to the HR ticket channel."""
        try:
            channel = interaction.channel
            if not isinstance(channel, discord.TextChannel):
                await interaction.response.send_message(
                    "This command can only be used in text channels.", ephemeral=True
                )
                return

            # Add the user to the channel with appropriate permissions
            await channel.set_permissions(user, view_channel=True, send_messages=True)

            await interaction.response.send_message(
                f"✅ {user.mention} has been added to the HR ticket.",
                ephemeral=False,
            )
        except Exception as e:
            await interaction.response.send_message(
                f"⚠️ Error adding user: {str(e)}", ephemeral=True
            )
            logger.exception(f"Error adding user {user} to HR ticket: {e}")


    @tree.command(name="hr-user-remove", description="Remove a user from the HR ticket.")
    @app_commands.describe(user="The user to remove from this HR ticket.")
    async def hr_user_remove(interaction: discord.Interaction, user: discord.User):
        try:
            channel = interaction.channel
            if not isinstance(channel, discord.TextChannel):
                await interaction.response.send_message(
                    "This command can only be used in text channels.", ephemeral=True
                )
                return

            await channel.set_permissions(user, overwrite=None)
            await interaction.response.send_message(
                f"✅ {user.mention} has been removed from the HR ticket.",
                ephemeral=False,
            )
        except Exception as e:
            await interaction.response.send_message(
                f"⚠️ Error removing user: {str(e)}", ephemeral=True
            )
            logger.exception(f"Error removing user {user} from HR ticket: {e}")


    @tree.command(name="hr-role-add", description="Add a role to the HR ticket.")
    @app_commands.describe(role="The role to add to this HR ticket.")
    async def hr_role_add(interaction: discord.Interaction, role: discord.Role):
        """Adds a specified role to the HR ticket channel."""
        try:
            channel = interaction.channel
            if not isinstance(channel, discord.TextChannel):
                await interaction.response.send_message(
                    "This command can only be used in text channels.", ephemeral=True
                )
                return

            # Add the role to the channel with appropriate permissions
            await channel.set_permissions(role, view_channel=True, send_messages=True)

            await interaction.response.send_message(
                f"✅ {role.mention} has been added to the HR ticket.",
                ephemeral=False,
            )
        except Exception as e:
            await interaction.response.send_message(
                f"⚠️ Error adding role: {str(e)}", ephemeral=True
            )
            logger.exception(f"Error adding role {role} to HR ticket: {e}")


    @tree.command(name="hr-role-remove", description="Remove a role from the HR ticket.")
    @app_commands.describe(role="The role to remove from this HR ticket.")
    async def hr_role_remove(interaction: discord.Interaction, role: discord.Role):
        try:
            channel = interaction.channel
            if not isinstance(channel, discord.TextChannel):
                await interaction.response.send_message(
                    "This command can only be used in text channels.", ephemeral=True
                )
                return

            await channel.set_permissions(role, overwrite=None)
            await interaction.response.send_message(
                f"✅ {role.mention} has been removed from the HR ticket.",
                ephemeral=False,
            )
        except Exception as e:
            await interaction.response.send_message(
                f"⚠️ Error removing role: {str(e)}", ephemeral=True
            )
            logger.exception(f"Error removing role {role} from HR ticket: {e}")


    @tree.command(name="hr-force-close", description="Force close the HR ticket if the embed button doesn't work.")
    async def hr_force_close(interaction: discord.Interaction):
        """
        Forcefully closes the HR ticket by deleting the channel.
        """
        try:
            channel = interaction.channel
            if not isinstance(channel, discord.TextChannel):
                await interaction.response.send_message(
                    "This command can only be used in text channels.", ephemeral=True
                )
                return

            # Log channel deletion
            logging_channel = interaction.guild.get_channel(LOGGING_CHANNEL_ID)
            if logging_channel:
                embed = discord.Embed(
                    title="📕 **Force Closed Ticket** 📕",
                    color=discord.Color.red(),
                    description=f"Ticket {channel.name} was force closed by {interaction.user.mention}."
                )
                embed.set_footer(
                    text="Carolina State Sheriff's Office Administration®",
                    icon_url="https://i.imgur.com/MyeKKcO.png"
                )
                await logging_channel.send(embed=embed)

            # Delete the channel
            await channel.delete(reason=f"Force closed by {interaction.user}.")
            await interaction.response.send_message(
                "✅ Ticket has been forcefully closed and the channel deleted.",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.response.send_message(
                f"⚠️ Error force closing ticket: {str(e)}", ephemeral=True
            )
            logger.exception(f"Error force closing HR ticket {interaction.channel.name}: {e}")
