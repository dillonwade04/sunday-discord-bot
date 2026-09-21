import discord
from datetime import datetime, timezone


STAFF_ALERT_CHANNEL_ID = 1325715730536075333

def register_alt_checker(bot: discord.Client):
    async def on_member_join(member: discord.Member):
        # Calculate account creation time and age (UTC)
        creation_time = member.created_at.replace(tzinfo=timezone.utc)
        now_utc = datetime.now(timezone.utc)
        account_age = now_utc - creation_time

        days = account_age.days
        seconds_left = account_age.seconds
        hours, remainder = divmod(seconds_left, 3600)
        minutes, seconds = divmod(remainder, 60)
        account_age_str = f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"

        creation_str = creation_time.strftime("%m/%d/%Y, %I:%M:%S %p UTC")
        now_str = now_utc.strftime("%m/%d/%Y, %I:%M:%S %p UTC")

        # Build the embed with user info.
        embed = discord.Embed(
            title="Potential ALT Account",
            description=f"**User:** {member.mention}",
            color=discord.Color.red()
        )
        embed.add_field(name="User ID", value=str(member.id), inline=False)
        embed.add_field(name="Creation Date & Time (UTC)", value=creation_str, inline=False)
        embed.add_field(name="Current Date & Time (UTC)", value=now_str, inline=False)
        embed.add_field(name="Account Age", value=account_age_str, inline=False)
        embed.set_footer(text="Carolina State Network Administration | Tebex Integration")

        # Send the embed to the staff alert channel.
        staff_channel = bot.get_channel(STAFF_ALERT_CHANNEL_ID)
        if staff_channel:
            await staff_channel.send(embed=embed)
        else:
            print(f"[WARNING] Staff alert channel (ID: {STAFF_ALERT_CHANNEL_ID}) not found.")


    if getattr(bot, "on_member_join", None):
        old_handler = bot.on_member_join
        async def combined_on_member_join(member: discord.Member):
            await old_handler(member)
            await on_member_join(member)
        bot.on_member_join = combined_on_member_join
    else:
        bot.on_member_join = on_member_join
