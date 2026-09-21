import discord
from discord.ext import tasks
import aiohttp
import json
import os

from config import DISCORD_TAGS_WEBHOOK_URL

# ============ CONFIGURATION ============
DUAL_CLAN_ALERT_CHANNEL_ID = 1057460761577922570
YOUR_SERVER_KEYWORDS = [
  "CSRP", "Syn County", "Forgotten Trails", "No Hesi", "Seelen UI", "desktop", "CSSO", "Cyberpunk", "digital",
]
SUSPICIOUS_SERVER_KEYWORDS = [
    "Kentucky RP", "PSRP", "Cali RP", "Gang", "Roleplay", "Impulse 99", "Hoods", "RSM Freeroam",
    "San Andreas", "State", "RP", "FivePD", "MIRAGE RP", "Trappin NYC", "Streets of Chiraq", "County",
    "Opening", "Role", "18+", "Paradise", "Cops and robbers", "OasisRP", "NYC", "LucidCity",
    "ProdigyRP", "NeverDie", "NoPixel", "STATIC FIVEPD", "Roleplayers", "Roleplaying", "California Roleplay", "ValleyRP",
    "Miami", "Atlanta", "Grand", "Unscripted.gg", "Unscripted.gg Public Server",
]
GUILDS_TO_BAN = [1047607743940395119, 1047610191711051866, 1047610330693509272]
BLACKLIST_TEXT_CHANNEL_ID = 1047612860899004518
BLACKLIST_EMBED_CHANNEL_ID = 1047612844012732476
ROLE_ID_TO_MENTION = 1215107073893998592
WEBHOOK_URL = DISCORD_TAGS_WEBHOOK_URL
FOOTER_ICON_URL = "https://i.imgur.com/wRbvz3o.png"
MAIN_GUILD_ID = 1047607743940395119
BLACKLIST_FILE = "false_positives.json"
# ======================================

recent_alerts = set()

def load_false_positives():
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, "r") as f:
            return json.load(f)
    return []

def save_false_positives(data):
    with open(BLACKLIST_FILE, "w") as f:
        json.dump(data, f)

class DualClanningAlert(discord.ui.View):
    def __init__(self, bot: discord.Client, member: discord.Member, server_name: str, player_count: str = "Unknown"):
        super().__init__(timeout=None)
        self.bot = bot
        self.member = member
        self.server_name = server_name
        self.player_count = player_count

    @discord.ui.button(label="Blacklist - Dual Clanning", style=discord.ButtonStyle.danger)
    async def blacklist_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("❌ You lack permission to blacklist.", ephemeral=False)
            return

        await interaction.response.defer()
        discord_id = str(self.member.id)
        name = self.member.display_name
        reason = "Dual Clanning"

        successes = []
        failures = []
        for guild_id in GUILDS_TO_BAN:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                failures.append((guild_id, "Bot not in guild or invalid ID"))
                continue
            try:
                await guild.ban(discord.Object(id=discord_id), reason=f"Blacklist: {reason}")
                successes.append(guild_id)
            except discord.Forbidden:
                failures.append((guild_id, "Missing ban perms."))
            except discord.HTTPException as e:
                failures.append((guild_id, f"HTTP error: {e}"))

        channel_text = self.bot.get_channel(BLACKLIST_TEXT_CHANNEL_ID)
        if channel_text:
            await channel_text.send(
                f"**CSSO Termination & Blacklist**\n> *Name:* {name}\n> *Discord-ID:* {discord_id}\n> *Reason:* {reason}\n> *Approved By:* <@{interaction.user.id}>"
            )

        channel_embed = self.bot.get_channel(BLACKLIST_EMBED_CHANNEL_ID)
        if channel_embed:
            embed = discord.Embed(
                title="Carolina State Sheriff's Office Log",
                description=(
                    f"**__CSSO Blacklist__**\n> **Name**: {name}\n> **Discord ID**: {discord_id}\n> **Reason**: {reason}\n> **Validated By**: <@{interaction.user.id}>"
                ),
                color=discord.Color.dark_red()
            )
            embed.set_footer(text="Carolina State Sheriff's Office Administration®", icon_url=FOOTER_ICON_URL)
            await channel_embed.send(embed=embed)

        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(WEBHOOK_URL, session=session)
            await webhook.send(
                content=f"<@{self.member.id}>\n-All CSSO Roles\n+CSSO Blacklist\n<@&{ROLE_ID_TO_MENTION}>"
            )

        await interaction.followup.send(f"✅ User {self.member.mention} has been blacklisted for dual clanning.", ephemeral=False)

    @discord.ui.button(label="Dismiss", style=discord.ButtonStyle.secondary)
    async def dismiss_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"🗑️ Alert dismissed by {interaction.user.mention}.", ephemeral=False)

    @discord.ui.button(label="False Positive", style=discord.ButtonStyle.success)
    async def false_positive_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You don't have permission to mark this as a false positive.", ephemeral=False)
            return

        false_positives = load_false_positives()
        server = self.server_name.strip().lower()
        if server not in false_positives:
            false_positives.append(server)
            save_false_positives(false_positives)

        await interaction.response.send_message(
            f"✅ `{self.server_name}` has been marked as a false positive and blacklisted from future alerts by {interaction.user.mention}.",
            ephemeral=False
        )

async def register_dual_clan_detector(bot: discord.Client):
    @tasks.loop(minutes=2)
    async def check_activities():
        guild = bot.get_guild(MAIN_GUILD_ID)
        if not guild:
            return

        false_positives = [fp.lower() for fp in load_false_positives()]
        all_blacklist = [kw.lower() for kw in SUSPICIOUS_SERVER_KEYWORDS]

        for member in guild.members:
            if member.bot:
                continue
            for activity in member.activities:
                if activity.type == discord.ActivityType.playing:
                    details = (getattr(activity, "details", None) or activity.name or "") + " " + (getattr(activity, "state", None) or "")
                    clean_details = details.lower()

                    if any(fp in clean_details for fp in false_positives):
                        continue

                    if any(keyword in clean_details for keyword in all_blacklist):
                        if not any(kw.lower() in clean_details for kw in YOUR_SERVER_KEYWORDS):
                            alert_key = (member.id, details)
                            if alert_key in recent_alerts:
                                continue
                            recent_alerts.add(alert_key)
                            await send_dual_clan_alert(bot, member, details)

    @check_activities.before_loop
    async def before_check_activities():
        await bot.wait_until_ready()

    check_activities.start()

async def send_dual_clan_alert(bot: discord.Client, member: discord.Member, server_name: str):
    channel = bot.get_channel(DUAL_CLAN_ALERT_CHANNEL_ID)
    if not channel:
        return

    player_count = "N/A"
    embed = discord.Embed(
        title="Possible Dual Clanning Alert",
        description=(
            f"**User:** {member.mention}\n"
            f"**User Discord-ID:** {member.id}\n\n"
            f"**Server/Game Name:** {server_name}\n"
            f"**Server Details:** {player_count}"
        ),
        color=discord.Color.red()
    )
    embed.set_footer(text="Carolina State Sheriff's Office Administration®", icon_url=FOOTER_ICON_URL)
    view = DualClanningAlert(bot, member, server_name, player_count)
    await channel.send(content=f"<@&1047611161245397009>", embed=embed, view=view)
