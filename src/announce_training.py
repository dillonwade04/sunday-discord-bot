# basic_training.py

import discord
from discord import app_commands
from datetime import datetime

######################
# Configuration
######################

# The role ID required to use /announce-basic-training
REQUIRED_ROLE_ID = 1047611211979685938      # CSSO Supervisor role

# The channel ID in which the command must be invoked
ALLOWED_CHANNEL_ID = 1047611348521062550    # command can only be used in the supervisor channel in the csso hq discord

# The channel ID where the first (detailed) embed goes
DETAILS_CHANNEL_ID = 1047611411951521822    # training-annoucements channel

# The channel ID where the second (reminder) embed goes
REMINDER_CHANNEL_ID = 1047611345626992680   # FTA annoucement channel

UNIFORM_IMAGE_URL = "https://i.imgur.com/SBpn8uq.png"

def register_commands(tree: app_commands.CommandTree):

    @tree.command(name="announce-basic-training", description="Announce a CSSO Basic Training session.")
    @app_commands.describe(
        date="Date of the training (e.g. January 6th, 2025)",
        time="Time of the training in EST (e.g. 7 PM)"
    )
    async def announce_basic_training(
        interaction: discord.Interaction,
        date: str,
        time: str
    ):
        """
        Sends two embedded announcements in two separate channels, each with an auto-added ✅ reaction.
        This command can only be used by someone with REQUIRED_ROLE_ID, in ALLOWED_CHANNEL_ID.
        The 'Hosted by' line is set to whoever invoked the command.
        """

        # 1) Check that the command is run in the correct channel
        if interaction.channel_id != ALLOWED_CHANNEL_ID:
            await interaction.response.send_message(
                f"This command can only be used in <#{ALLOWED_CHANNEL_ID}>.",
                ephemeral=True
            )
            return

        # 2) Check if the user has the required role
        user_role_ids = [role.id for role in interaction.user.roles]
        if REQUIRED_ROLE_ID not in user_role_ids:
            await interaction.response.send_message(
                "You do not have the required role to announce basic trainings.",
                ephemeral=True
            )
            return

        # 3) Send a short ephemeral confirmation
        embed_confirmation = discord.Embed(
            title="Carolina State Sheriffs Office",
            description="I have successfully sent the Training announcement!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed_confirmation.set_footer(
            text="Carolina State Sheriff's Office Administration®",
            icon_url="https://i.imgur.com/wRbvz3o.png"
        )
        await interaction.response.send_message(embed=embed_confirmation, ephemeral=False)

        # 4) Build the FIRST embed (detailed, with an image). Matches the text you wanted:
        description_text = (
            "**Carolina State Sheriffs Office | Training Administration**\n\n"
            "**__CSSO Basic Training__**\n"
            f"Date: {date}\n"
            f"Time: {time} EST\n"
            f"Hosted by: {interaction.user.mention}\n\n"
            "Have your Uniform and call-sign in your in-game-name. "
            "Make sure that you are in https://discord.com/channels/505147641781551124/552678811162902559\n"
            "15 minutes prior to the start of the training. below please react with a ✅ "
            "for attendance so that we can ensure that you are counted.\n\n"
            "**Note:** If you react with a ✅ and are unable to attend please un-react "
            "at least an hour before the training starts."
        )

        embed_details = discord.Embed(
            title="",
            description=description_text,
            color=discord.Color.yellow(),
            timestamp=datetime.utcnow()
        )
        embed_details.set_footer(text="Carolina State Sheriff's Office Administration®", icon_url="https://i.imgur.com/wRbvz3o.png")
        embed_details.set_image(url=UNIFORM_IMAGE_URL)

        # 5) Build the SECOND embed (simpler reminder)
        embed_reminder = discord.Embed(
            title="Carolina State Sheriffs Office | Training Administration",
            description=(
                "> **Basic Training Notice**\n"
                f"> Time: {time}\n"
                f"> Date: {date}\n"
                "> FTA's Needed: 2\n"
                "> Please react with ✅ confirming that you can attend."
            ),
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed_reminder.set_footer(text="Carolina State Sheriff's Office Administration®", icon_url="https://i.imgur.com/wRbvz3o.png")

        # 6) Fetch the two target channels
        details_channel = interaction.client.get_channel(DETAILS_CHANNEL_ID)
        reminder_channel = interaction.client.get_channel(REMINDER_CHANNEL_ID)
        if not details_channel or not reminder_channel:
            # Optionally log or handle this error, e.g. telling the user
            return

        # 7) Send the FIRST embed in Training annoucements
        # Mention any roles if desired, e.g. "@Cadet @Probie"
        mention_line = "<@&1047611224789110874> <@&1251633259285188789>"
        message1 = await details_channel.send(content=mention_line, embed=embed_details, allowed_mentions=discord.AllowedMentions(roles=True))

        # Automatically add the "check" reaction (✅) to the first message
        await message1.add_reaction("✅")
        await message1.add_reaction("❌")

        # 8) Send the SECOND embed in FTA channel
        mention2_line = "<@&1047611253884997823>"
        message2 = await reminder_channel.send(content=mention2_line, embed=embed_reminder, allowed_mentions=discord.AllowedMentions(roles=True))

        # Automatically add the "check" reaction (✅) to the second message
        await message2.add_reaction("✅")

        #(Optional) If you want to log
        from utils import log_message
        await log_message(
             bot=interaction.client,
             title="/announce-basic-training Used",
             description=(
                 f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                 f"**Date:** {date}\n"
                 f"**Time:** {time}\n"
             ),
             color=discord.Color.yellow()
         )
