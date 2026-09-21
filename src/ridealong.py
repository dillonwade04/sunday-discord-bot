import discord
from discord import app_commands

# The channel where the /request-ridealong command can be used:
RIDEALONG_REQUEST_CHANNEL_ID = 1047611323418169526

# The channel where the bot posts the ridealong request embed & claim button:
RIDEALONG_NOTIFICATIONS_CHANNEL_ID = 1047611351050223668

class RidealongClaimView(discord.ui.View):
    def __init__(self, requestor_id: int, name: str, ridealong_type: str, time_available: str):
        super().__init__(timeout=None)
        self.requestor_id = requestor_id
        self.name = name
        self.ridealong_type = ridealong_type
        self.time_available = time_available

    @discord.ui.button(label="Claim Ridealong", style=discord.ButtonStyle.primary)
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        claimer = interaction.user
        button.disabled = True
        self.stop()

        # 1) Public message in the same channel
        await interaction.response.send_message(
            f"{claimer.mention} has claimed the ridealong for <@{self.requestor_id}>!",
            ephemeral=False
        )

        # 2) DM the requestor
        requestor = interaction.guild.get_member(self.requestor_id)
        if requestor:
            try:
                await requestor.send(
                    f"Your ridealong request has been claimed by {claimer.mention}!\n"
                    "They will contact you shortly to schedule your ridealong."
                )
            except discord.Forbidden:
                pass

        # 3) Edit the original embed to show the button disabled
        await interaction.message.edit(view=self)

def register_commands(tree: app_commands.CommandTree):
    @tree.command(name="request-ridealong", description="Request a ridealong from your leadership.")
    @app_commands.describe(
        ridealong_type="What type of ridealong are you requesting?",
        time_available="When are you available? Please format in EST.",
        name="Your name."
    )
    @app_commands.choices(ridealong_type=[
        app_commands.Choice(name="Experience", value="Experience"),
        app_commands.Choice(name="MRA", value="MRA"),
        app_commands.Choice(name="Probationary-ride-along", value="Probationary-ride-along")
    ])
    async def request_ridealong(
        interaction: discord.Interaction,
        ridealong_type: app_commands.Choice[str],
        time_available: str,
        name: str
    ):
        """
        Let Deputies request a ridealong from Corporals/Sergeants.
        Posts an embed with a Claim button in the ridealong notifications channel.
        """

        # 1) Ensure the command is used in the correct channel
        if interaction.channel_id != RIDEALONG_REQUEST_CHANNEL_ID:
            await interaction.response.send_message(
                "This command can only be used in the designated ridealong request channel.",
                ephemeral=True
            )
            return

        # 2) Send ephemeral confirmation to user
        await interaction.response.send_message(
            "I have sent this request to the leadership team, please check your DMs for more information!",
            ephemeral=False
        )

        # 3) DM the user with the request details
        try:
            await interaction.user.send(
                f"Thank you for requesting a ridealong!\n\n"
                f"**Ridealong Details**\n"
                f"- **Type**: {ridealong_type.value}\n"
                f"- **Time Available**: {time_available}\n"
                f"- **Name**: {name}\n\n"
                "A member of the leadership team will contact you soon to schedule the ridealong."
            )
        except discord.Forbidden:
            pass

        # 4) Build the embed for the notifications channel
        embed = discord.Embed(
            title="Ridealong Request",
            color=discord.Color.green()
        )
        embed.add_field(
            name="> Ridealong Request",
            value=(
                f"**Name**: {name}\n"
                f"**Type Of Ridealong**: {ridealong_type.value}\n"
                f"**Time Available**: {time_available}\n"
                f"**User**: <@{interaction.user.id}>\n"
                f"**User-ID**: {interaction.user.id}"
            ),
            inline=False
        )

        embed.set_footer(text="Carolina State Sheriff's Office Administration®", icon_url="https://i.imgur.com/wRbvz3o.png")

        view = RidealongClaimView(
            requestor_id=interaction.user.id,
            name=name,
            ridealong_type=ridealong_type.value,
            time_available=time_available
        )

        # 5) Send to the ridealong notifications channel
        channel = interaction.guild.get_channel(RIDEALONG_NOTIFICATIONS_CHANNEL_ID)
        if channel:
            await channel.send(
              content=f"<@&1047611254778384534>",
              embed=embed,
              view=view,
              allowed_mentions=discord.AllowedMentions(roles=True)
            )
        else:
            print("Ridealong notifications channel not found! Check the ID.")
