import discord
from discord import app_commands
from datetime import datetime

# ----- CONFIGURATION CONSTANTS -----
HR_REVIEW_LOG_CHANNEL_ID = 1066446933218054304  # The channel where reviews get logged
ALLOWED_HR_REVIEW_COMMAND_ROLE_ID = 1047611188957151362  # The HR role ID
# -------------------------------------

class HRReviewView(discord.ui.View):
    def __init__(self, target: discord.User, ticket_name: str):
        super().__init__(timeout=300)  # 5-minute timeout
        self.target = target
        self.ticket_name = ticket_name
        self.value = None

    @discord.ui.button(label="1 Star", style=discord.ButtonStyle.secondary, custom_id="hr_review_1")
    async def star1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_rating(interaction, 1)

    @discord.ui.button(label="2 Stars", style=discord.ButtonStyle.primary, custom_id="hr_review_2")
    async def star2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_rating(interaction, 2)

    @discord.ui.button(label="3 Stars", style=discord.ButtonStyle.primary, custom_id="hr_review_3")
    async def star3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_rating(interaction, 3)

    @discord.ui.button(label="4 Stars", style=discord.ButtonStyle.success, custom_id="hr_review_4")
    async def star4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_rating(interaction, 4)

    @discord.ui.button(label="5 Stars", style=discord.ButtonStyle.success, custom_id="hr_review_5")
    async def star5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_rating(interaction, 5)

    async def process_rating(self, interaction: discord.Interaction, rating: int):
        """Handles the user clicking a star rating button."""
        # Only the target user can respond.
        if interaction.user.id != self.target.id:
            await interaction.response.send_message("You are not the intended user for this review.", ephemeral=True)
            return

        self.value = rating

        # Disable all buttons to prevent multiple submissions.
        for child in self.children:
            child.disabled = True

        # Edit the original DM to thank the user for their rating.
        await interaction.response.edit_message(
            content=f"Thank you for rating your HR experience **{rating} star{'s' if rating != 1 else ''}**!",
            view=self
        )

        # Log the rating in the HR review log channel, with a custom embed style.
        log_channel = interaction.client.get_channel(HR_REVIEW_LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="Carolina State Sheriffs Office Human Resources",
                color=discord.Color.blue()
            )
            info_str = (
                f"**User:** {self.target.mention}\n"
                f"**User-ID:** {self.target.id}\n"
                f"**Ticket Name:** {self.ticket_name}\n"
                f"**Rating:** {rating} Stars"
            )
              # Add it all as one field
            embed.add_field(name="**> CSSO Rating System**", value=info_str, inline=False)
            embed.set_footer(text="Carolina State Sheriff's Office Administration®", icon_url="https://i.imgur.com/wRbvz3o.png")
            await log_channel.send(embed=embed)
        else:
            print(f"HR review log channel (ID: {HR_REVIEW_LOG_CHANNEL_ID}) not found.")

def register_commands(tree: app_commands.CommandTree):
    @tree.command(name="hr-rate-send", description="Send an HR review DM to a user with a star rating system.")
    @app_commands.describe(user="The user to send the HR review DM to")
    async def hr_rate_send(interaction: discord.Interaction, user: discord.User):
        """Command to DM a user an embedded star rating for HR feedback."""
        # Check if the command user has the HR role.
        if ALLOWED_HR_REVIEW_COMMAND_ROLE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        # We'll use the channel name where the command was run as the "ticket name."
        ticket_name = interaction.channel.name if interaction.channel else "Unknown-Channel"

        # Prepare the DM embed.
        embed = discord.Embed(
            title="Carolina State Sheriff's Office Human Resources",
            description=(
                "Greetings, your most recent HR ticket was **CLOSED**.\n"
                "Please click one of the buttons below to rate your HR experience.\n"
                "**Note:** 1 being the worst and 5 being the best! (This information is confidential.)\n\n"
                "Sincerely,\n"
                "**Sheriff HR Administration**"
            ),
            color=discord.Color.yellow(),
            timestamp=datetime.now()
        )
        embed.set_footer(text="Carolina State Sheriff's Office Administration®", icon_url="https://i.imgur.com/wRbvz3o.png")
        # Prepare the view with star rating buttons, passing in the ticket name.
        view = HRReviewView(target=user, ticket_name=ticket_name)

        # Attempt to send the DM.
        try:
            dm_channel = await user.create_dm()
            await dm_channel.send(embed=embed, view=view)
            await interaction.response.send_message(f"HR review DM sent to {user.mention}.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to send DM: {e}", ephemeral=True)
