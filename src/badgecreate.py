#badgecreate .py

import discord
from discord import app_commands
import urllib.parse
from utils import log_message

# Badge creation configuration.


ALLOWED_CHANNEL_ID = 1108993511732285451

# Badge Type Configurations (corresponding to different templates)
FINISHES = {
    "Deputy": "https://www.smithwarren.com/visualbadge/image/S579.png?finish=1&line1=&line2=&line4=&line5=&font=21&enamel=17&color=10&center=376&att=513&shape=495&",  # Nickel Electroplate
    "Supervisor": "https://www.smithwarren.com/visualbadge/image/S579.png?finish=7&line1=&line2=&line4=&line5=&font=21&enamel_type=19&color=10&center=376&att=513&shape=495&",  # Gold-Ray w/ Sil-Ray Panels
    "Command": "https://www.smithwarren.com/visualbadge/image/S579.png?finish=4&line1=&line2=&line4=&line5=&font=21&enamel=17&color=10&center=376&att=513&shape=495&",  # Gold Electroplate
    "Breast Cancer Awareness Month (October ONLY)": "https://www.smithwarren.com/visualbadge/image/S579.png?finish=535&line1=&line2=&line4=&line5=&font=21&color=10&center=376&att=513&shape=495&", #breast cancer
    "Autism Awareness Month (April ONLY)": "https://www.smithwarren.com/visualbadge/image/S579.png?finish=1408&line1=&line2=&line4=&line5=&font=21&color=10&center=376&att=513&shape=495&",
}

def generate_badge_url(rank, name, callsign, badge_type):

    # Get the base URL based on the badge type
    base_url = FINISHES.get(badge_type)
    if not base_url:
        raise ValueError(f"Invalid badge type: {badge_type}")

    # Define the badge parameters
    params = {
        "line1": rank.upper(),  # Line 1: Rank
        "line2": name.upper(),  # Line 2: Name
        "line4": callsign.upper(),  # Line 4: Callsign
        "line5": "COUNTY SHERIFF",  # Line 5: Static text
        "font": "21",  # Font style
        "enamel": "17",  # Enamel type
        "color": "10",  # Color
        "center": "376",  # Center setting
        "att": "513",  # Attribute
        "shape": "495",  # Shape
    }

    # Encode the parameters into a URL query string
    encoded_params = urllib.parse.urlencode(params)

    # Construct the full badge URL
    badge_url = f"{base_url}&{encoded_params}"
    return badge_url

def register_commands(tree: app_commands.CommandTree):
    """
    Registers the /badge-create command to the bot's command tree.
    """


    @tree.command(name="badge-create", description="Generate a badge with user-provided details.")
    @app_commands.describe(
        user="Who do you want to send the Badge to?",
        rank="Rank to display on the badge (e.g., Deputy II)",
        name="Name to display on the badge (e.g., J. Doe)",
        callsign="Callsign to display on the badge (e.g., 210)",
        type="Badge type (Deputy, Supervisor, Command)"
    )
    @app_commands.choices(
        type=[
            app_commands.Choice(name="Deputy", value="Deputy"),
            app_commands.Choice(name="Supervisor", value="Supervisor"),
            app_commands.Choice(name="Command", value="Command"),
            app_commands.Choice(name="Breast Cancer Awareness Month (October ONLY)", value="Breast Cancer Awareness Month (October ONLY)"),
            app_commands.Choice(name="Autism Awareness Month (April ONLY)", value="Autism Awareness Month (April ONLY)"),
        ]
    )
    async def badge_create(
        interaction: discord.Interaction,
        user: discord.User,
        rank: str,
        name: str,
        callsign: str,
        type: app_commands.Choice[str]
    ):

        # Check if the command is being used in the allowed channel
        if interaction.channel_id != ALLOWED_CHANNEL_ID:
            await interaction.response.send_message(
                f"This command can only be used in the <#{ALLOWED_CHANNEL_ID}>.", ephemeral=True
            )
            return

        """
        Handles the /badge-create command.
        """
        try:
            # Generate the badge URL dynamically
            badge_url = generate_badge_url(rank, name, callsign, type.value)

            # Create the embed with the badge preview
            embed = discord.Embed(
                title="Badge Created!",
                description=f"Badge for {user.mention} is ready!\n[View Badge]({badge_url})",
                color=discord.Color.blue()
            )
            embed.set_image(url=badge_url)  # Add the badge image to the embed

            # Send the embed to the channel
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            # Handle errors gracefully.
            await interaction.response.send_message(
                f"Error creating badge: {str(e)}", ephemeral=True
            )

        await log_message(
            interaction.client,
            title="/badge-create used",
            description=(
                f"{interaction.user.mention} (`{interaction.user.id}`) created a badge.\n"
                f"{user}\n"
                f"{rank}\n"
                f"{callsign}\n"
                f"{type}"
            ),
            color=discord.Color.pink()
        )
