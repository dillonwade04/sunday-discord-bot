# activities.py

import discord
from discord.ext import tasks
import random

# List of activities for the bot to display
activities = [
    discord.Activity(type=discord.ActivityType.playing, name="Made by Dillon!"),
    discord.Activity(type=discord.ActivityType.playing, name="Serving CSSO proudly"),
    discord.Activity(type=discord.ActivityType.playing, name="Carolina State Network!"),
]

# Task to rotate the bot's activities
@tasks.loop(seconds=5)
async def rotate_activity(bot):
    """
    Rotates the bot's activity every 5 seconds.
    Ensures the activities list is replenished when exhausted.
    """
    global activities

    if not activities:  # Replenish if empty
        activities = [
            discord.Activity(type=discord.ActivityType.playing, name="Made by Dillon!"),
            discord.Activity(type=discord.ActivityType.playing, name="Serving CSSO proudly"),
            discord.Activity(type=discord.ActivityType.playing, name="Carolina State Network!")
        ]
        random.shuffle(activities)

    current_activity = activities.pop(0)
    await bot.change_presence(activity=current_activity)

def start_activity_rotation(bot):
    """
    Starts the activity rotation loop.
    """
    if not rotate_activity.is_running():
        rotate_activity.start(bot)



from discord import app_commands
#dont think this will ever be needed
def register_commands(tree: app_commands.CommandTree):
    @tree.command(name="start-activities", description="Manually start the activity rotation.")
    async def start_activities(interaction: discord.Interaction):
        """
        Manually starts the activity rotation task.
        """
        if not rotate_activity.is_running():
            rotate_activity.start(interaction.client)
            await interaction.response.send_message("✅ Activity rotation has been started.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Activity rotation is already running.", ephemeral=True)
