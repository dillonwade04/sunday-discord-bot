import discord
import aiohttp

from config import DISCORD_TAGS_WEBHOOK_URL

# Guild where these events should trigger.
TARGET_GUILD_ID = 1047607743940395119

# Channel where welcome/goodbye embeds should be posted.
WELCOME_CHANNEL_ID = 1047611295937073242

# Webhook URL for "S.U.N.D.A.Y."
LEAVE_WEBHOOK_URL = DISCORD_TAGS_WEBHOOK_URL

def register_events(bot: discord.Client):
    async def on_member_join(member: discord.Member):
        # Only run if this member joined the target guild.
        if member.guild.id != TARGET_GUILD_ID:
            return

        channel = bot.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="Carolina State Sheriff's Officer Welcomer",
                description=(
                    f"Howdy! {member.mention} and welcome to the Sheriff's Office! Below you will find many important channels.\n\n"
                    f"<#1047611411951521822> This is where you will find when your basic training is.\n"
                    f"<#1047611300416585870> This holds the majority of information you need to know.\n"
                    f"<#1047611306255077548> This holds all our rules.\n"
                    f"<#1047611305223258243> This is where you can apply for subdivisions when you reach deputy I.\n\n"
                    "*If you have any questions please DM a Leadership member or create a CSSO HR Ticket!*"
                ),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text="Carolina State Sheriff's Office Administration®")
            # Ping the user outside the embed.
            await channel.send(content=f"{member.mention}", embed=embed)

    async def on_member_remove(member: discord.Member):
        # Only run if this member left the target guild.
        if member.guild.id != TARGET_GUILD_ID:
            return

        # 1) Send the normal goodbye embed in the specified channel.
        channel = bot.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="Carolina State Sheriff's Office",
                description=(
                    f"<@&1047611182695055442> it appears that {member.mention} has left the CSSO Discord!"
                ),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text="Carolina State Sheriff's Office Administration®")
            await channel.send(content=f"{member.mention} | <@&1047611182695055442>", embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))

        # 2) Send the extra webhook message via aiohttp (manually).
        async with aiohttp.ClientSession() as session:
            payload = {
                "content": f"{member.mention}\n-All CSSO Roles.\n<@&1215107073893998592>",
                "username": "S.U.N.D.A.Y.",
                "allowed_mentions": {"parse": ["users", "roles"]}
            }
            async with session.post(LEAVE_WEBHOOK_URL, json=payload) as resp:
                if resp.status not in (200, 204):
                    print(f"[WARNING] Webhook POST failed with status {resp.status}")

    # Chain the new handlers onto any existing on_member_join / on_member_remove
    if getattr(bot, "on_member_join", None):
        old_join = bot.on_member_join
        async def combined_on_member_join(member: discord.Member):
            await old_join(member)
            await on_member_join(member)
        bot.on_member_join = combined_on_member_join
    else:
        bot.on_member_join = on_member_join

    if getattr(bot, "on_member_remove", None):
        old_remove = bot.on_member_remove
        async def combined_on_member_remove(member: discord.Member):
            await old_remove(member)
            await on_member_remove(member)
        bot.on_member_remove = combined_on_member_remove
    else:
        bot.on_member_remove = on_member_remove
