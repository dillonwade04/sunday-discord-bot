# fun.py

import discord
from discord import app_commands
from datetime import datetime
import pytz
import random
import aiohttp
from utils import log_message
from discord import Permissions




# Roles allowed to use /promote
ROLE_IDS = [
    1047611161245397009,
    1047612711099441182,
    1047611180715348060, # pink Bots roles
    1047611169990516887,
    1047612707576221746

          # Example: Heads Role leadership discord
    # ... add more role IDs if needed
]


# Restrict administrative fun commands to leadership roles.

def can_use(interaction: discord.Interaction) -> bool:
    """Returns True if the user has any of the allowed role IDs."""
    return any(role.id in ROLE_IDS for role in interaction.user.roles)



def register_commands(tree: app_commands.CommandTree):
    """
    Call this function from your main bot file (e.g. bot.py)
    to register the /promote slash command.
    """


    @tree.command(name="dm", description="Send a direct message to a user.")
    async def send_dm(interaction: discord.Interaction, user: discord.User, message: str):
        if not can_use(interaction):
            await interaction.response.send_message(
                "You do not have the required role to use this command. The Administration team has been notified.",
                ephemeral=True
            )
            return

        try:
            await user.send(message)
            await interaction.response.send_message(f"Message sent to {user.mention}.", ephemeral=True)
            await log_message(bot=interaction.client, title="DM Command Used", description=f"{interaction.user} sent a DM to {user.mention} with the message: {message}", color=discord.Color.purple())
        except discord.Forbidden:
            await interaction.response.send_message("I cannot send a DM to this user.", ephemeral=True)
            await log_message(bot=interaction.client, title="DM Command Failed", description=f"{interaction.user} attempted to send a DM to {user.mention}, but it failed.", color=discord.Color.red())


    @tree.command(name="joke", description="Get a random joke!")
    async def joke(interaction: discord.Interaction):
        if not can_use(interaction):
            await interaction.response.send_message(
                "You do not have the required role to use this command. The Administration team has been notified.",
                ephemeral=True
            )
            return
        jokes = [
        "Why don't skeletons fight each other? They don't have the guts.",
        "I told my computer I needed a break, and now it won't stop sending me KitKats!",
        "What do you call a fish wearing a bowtie? Sofishticated.",
    ]
        await interaction.response.send_message(f"😂 {random.choice(jokes)}")
        await log_message(bot=interaction.client, title="/joke command used.", description=f"Invoker: {interaction.user.mention}", color=discord.Color.purple())

    @tree.command(name="8ball", description="Ask the Magic 8-Ball a question!")
    @app_commands.describe(question="What do you want to ask the Magic 8-Ball?")
    async def eight_ball(interaction: discord.Interaction, question: str):
        if not can_use(interaction):
            await interaction.response.send_message(
                "You do not have the required role to use this command. The Administration team has been notified.",
                ephemeral=True
            )
            return
        responses = [
            "Yes.", "No.", "Maybe.", "Ask again later.", "Definitely!", "I wouldn't count on it."
        ]
        await interaction.response.send_message(f"🎱 {random.choice(responses)}")
        await log_message(bot=interaction.client, title="/8ball command used.", description=f"Invoker: {interaction.user.mention}", color=discord.Color.purple())

    @tree.command(name="dadjoke", description="Get a random dad joke!")
    async def dad_joke(interaction: discord.Interaction):
        if not can_use(interaction):
            await interaction.response.send_message(
                "You do not have the required role to use this command. The Administration team has been notified.",
                ephemeral=True
            )
            return
        async with aiohttp.ClientSession() as session:
            async with session.get("https://icanhazdadjoke.com/", headers={"Accept": "application/json"}) as response:
                data = await response.json()
                await interaction.response.send_message(data["joke"])
                await log_message(bot=interaction.client, title="/dadjoke command used.", description=f"Invoker: {interaction.user.mention}", color=discord.Color.purple())

    @tree.command(name="meme", description="Get a random meme!")
    async def meme(interaction: discord.Interaction):
        if not can_use(interaction):
            await interaction.response.send_message(
                "You do not have the required role to use this command. The Administration team has been notified.",
                ephemeral=True
            )
            return
        async with aiohttp.ClientSession() as session:
            async with session.get("https://meme-api.com/gimme") as response:
                data = await response.json()
                embed = discord.Embed(title=data["title"], url=data["postLink"])
                embed.set_image(url=data["url"])
                await interaction.response.send_message(embed=embed)
                await log_message(bot=interaction.client, title="/meme command used.", description=f"Invoker: {interaction.user.mention}", color=discord.Color.purple())

    @tree.command(name="rps", description="Play Rock, Paper, Scissors!")
    @app_commands.describe(choice="Rock, Paper, or Scissors?")
    async def rps(interaction: discord.Interaction, choice: str):
        if not can_use(interaction):
            await interaction.response.send_message(
                "You do not have the required role to use this command. The Administration team has been notified.",
                ephemeral=True
            )
            return
        options = ["Rock", "Paper", "Scissors"]
        bot_choice = random.choice(options)
        if choice.capitalize() == bot_choice:
            result = "It's a tie!"
        elif (choice.capitalize() == "Rock" and bot_choice == "Scissors") or \
            (choice.capitalize() == "Scissors" and bot_choice == "Paper") or \
            (choice.capitalize() == "Paper" and bot_choice == "Rock"):
            result = "You win!"
        else:
            result = "You lose!"
        await interaction.response.send_message(f"You chose {choice.capitalize()}. I chose {bot_choice}. {result}")
        await log_message(bot=interaction.client, title="/rps command used.", description=f"Invoker: {interaction.user.mention}", color=discord.Color.purple())


    @tree.command(name="coinflip", description="Flip a coin!")
    async def coin_flip(interaction: discord.Interaction):
        if not can_use(interaction):
            await interaction.response.send_message(
                "You do not have the required role to use this command. The Administration team has been notified.",
                ephemeral=True
            )
            return
        result = random.choice(["Heads", "Tails"])
        await interaction.response.send_message(f"🪙 The coin landed on **{result}**!")
        await log_message(bot=interaction.client, title="/coinflip command used.", description=f"Invoker: {interaction.user.mention}", color=discord.Color.purple())


    @tree.command(name="compliment", description="Send a random compliment!")
    @app_commands.describe(user="Who do you want to compliment?")
    async def compliment(interaction: discord.Interaction, user: discord.Member):
        if not can_use(interaction):
            await interaction.response.send_message(
                "You do not have the required role to use this command. The Administration team has been notified.",
                ephemeral=True
            )
            return
        compliments = [
            "You're amazing!", "You light up the room!", "You're a fantastic person!",
            "You're so talented!", "You have a great sense of humor!"
        ]
        await interaction.response.send_message(f"{user.mention}, {random.choice(compliments)} 😊")
        await log_message( bot=interaction.client, title="/compliment command used.", description=f"Invoker: {interaction.user.mention}", color=discord.Color.purple())


    @tree.command(name="mock", description="Mock someone's text.")
    @app_commands.describe(text="Text to mock.")
    async def mock(interaction: discord.Interaction, text: str):
        if not can_use(interaction):
            await interaction.response.send_message(
                "You do not have the required role to use this command. The Administration team has been notified.",
                ephemeral=True
            )
            return
        mocked = ''.join(
            char.upper() if i % 2 else char.lower() for i, char in enumerate(text)
        )
        await interaction.response.send_message(mocked)
        await log_message(title="/mock command used.", description=f"Invoker: {interaction.user.mention}", color=discord.Color.purple())

    @tree.command(name="catfact", description="Get a random cat fact!")
    async def cat_fact(interaction: discord.Interaction):
        if not can_use(interaction):
            await interaction.response.send_message(
                "You do not have the required role to use this command. The Administration team has been notified.",
                ephemeral=True
            )
        async with aiohttp.ClientSession() as session:
            async with session.get("https://meowfacts.herokuapp.com/") as response:
                data = await response.json()
                await interaction.response.send_message(data["data"][0])
                await log_message( bot=interaction.client, title="/catfact command used.", description=f"Invoker: {interaction.user.mention}", color=discord.Color.purple())
