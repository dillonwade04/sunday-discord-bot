# utils.py

import discord
from datetime import datetime
import pytz

# log channel ID (the channel where log messages should go). (duh)
LOG_CHANNEL_ID = 1109171155673292950

EST = pytz.timezone("US/Eastern")

async def log_message(
    bot: discord.Client,
    title: str,
    description: str,
    color: discord.Color = discord.Color.blue()
):
    """
    A helper to send an embedded log message to the channel with ID LOG_CHANNEL_ID,
    using the 'bot' parameter (discord.Client).
    """
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now(EST)
        )
        embed.set_footer(text="S.U.N.D.A.Y.", icon_url="https://i.imgur.com/wRbvz3o.png")
        await log_channel.send(embed=embed)
    else:
        print(f"Log channel not found: {LOG_CHANNEL_ID}")
