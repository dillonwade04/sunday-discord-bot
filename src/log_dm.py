# log_dm.py

import discord


LOG_DM_CHANNEL_ID = 1057460662147743856

def register_dm_logger(bot: discord.Client):
    async def dm_logger(message: discord.Message):

        if message.author.bot:
            return

        # Process only direct messages (DMs)
        if message.guild is None:
            log_channel = bot.get_channel(LOG_DM_CHANNEL_ID)
            if log_channel is None:
                # Log a warning if the channel isn't found.
                print(f"Log channel with ID {LOG_DM_CHANNEL_ID} not found.")
                return

            # Build an embed with details of the DM.
            embed = discord.Embed(
                title="New Direct Message Received",
                description="A DM was sent to the bot.",
                color=discord.Color.blue(),
                timestamp=message.created_at
            )
            embed.add_field(
                name="From",
                value=f"<@{message.author.id}>\n{message.author}\n{message.author.id}",
                inline=False
            )
            embed.add_field(
                name="Content",
                value=message.content if message.content else "No text content",
                inline=False
            )

            # If there are attachments, list their URLs.
            if message.attachments:
                attachment_urls = "\n".join(attachment.url for attachment in message.attachments)
                embed.add_field(name="Attachments", value=attachment_urls, inline=False)

            await log_channel.send(embed=embed)

    # Check if the bot has an add_listener method
    if hasattr(bot, "add_listener"):
        bot.add_listener(dm_logger, "on_message")
    else:
        # Fallback: combine the new listener with any existing on_message handler
        existing_on_message = getattr(bot, "on_message", None)
        async def combined_on_message(message: discord.Message):
            await dm_logger(message)
            if existing_on_message:
                await existing_on_message(message)
        bot.on_message = combined_on_message
