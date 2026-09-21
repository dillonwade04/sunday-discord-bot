import discord
from discord import app_commands
from discord.ui import View, button, Button
from datetime import datetime
import aiohttp

# ─── Pull in your existing blacklist settings ─────────────────────────────────
from blacklist import (
    GUILDS_TO_BAN,
    BLACKLIST_TEXT_CHANNEL_ID,
    BLACKLIST_EMBED_CHANNEL_ID,
    ROLE_ID_TO_MENTION,
    WEBHOOK_URL,
)
from utils import log_message  # log_message(bot, title: str, description: str, color: discord.Color)

# IDs allowed to *use* this request command:
REQUEST_COMMAND_ROLE_IDS = [
    1047612731425038356,  # SUNDAY Perms
    1215107073893998592,  # CSSO High Command
    1047612726433816668   # …add more as needed
]

class RequestBlacklistView(View):
    def __init__(self, target_id: str, name: str, reason: str, proof_url: str, requester: discord.Member):
        super().__init__(timeout=None)
        self.target_id = target_id
        self.name      = name
        self.reason    = reason
        self.proof_url = proof_url
        self.requester = requester

    @button(label="Blacklist", style=discord.ButtonStyle.danger, custom_id="request:blacklist")
    async def confirm(self, interaction: discord.Interaction, button: Button):
        # Permission guard
        if not any(r.id in REQUEST_COMMAND_ROLE_IDS for r in interaction.user.roles):
            return await interaction.response.send_message(
                "❌ You aren’t allowed to confirm this.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        # 1) Global‐ban across your GUILDS_TO_BAN
        successes, failures = [], []
        for gid in GUILDS_TO_BAN:
            guild = interaction.client.get_guild(gid)
            if not guild:
                failures.append(f"{gid} (not in cache)")
                continue
            try:
                await guild.ban(
                    discord.Object(id=int(self.target_id)),
                    reason=f"Blacklist requested by {self.requester} — {self.reason}"
                )
                successes.append(str(gid))
            except Exception as e:
                failures.append(f"{gid} ({type(e).__name__})")

        # 2) Plain‐text log in your text channel
        txt_chan = interaction.client.get_channel(BLACKLIST_TEXT_CHANNEL_ID)
        if txt_chan:
            await txt_chan.send(
                f"**CSSO Termination & Blacklist**\n"
                f"> *Name:* {self.name}\n"
                f"> *Discord ID:* {self.target_id}\n"
                f"> *Reason:* {self.reason}\n"
                f"> *Approved By:* {interaction.user.mention}"
            )

        # 3) Compact embed in your embed channel (proof as thumbnail)
        emb_chan = interaction.client.get_channel(BLACKLIST_EMBED_CHANNEL_ID)
        if emb_chan:
            em = discord.Embed(
                title="Carolina State Sheriff's Office Log",
                color=discord.Color.dark_red(),
                timestamp=datetime.utcnow()
            )
            em.description = "\n".join([
                "__**CSSO Blacklist**__",
                f"> **Name:** {self.name}",
                f"> **Discord ID:** {self.target_id}",
                f"> **Reason:** {self.reason}",
                f"> **Approved By:** {interaction.user.mention}"
            ])
            em.set_thumbnail(url=self.proof_url)
            em.set_footer(
                text="Carolina State Sheriff's Office Administration®",
                icon_url="https://i.imgur.com/wRbvz3o.png"
            )
            await emb_chan.send(embed=em)

        # 4) Fire your webhook ping (with heads role mention)
        async with aiohttp.ClientSession() as sess:
            hook = discord.Webhook.from_url(WEBHOOK_URL, session=sess)
            await hook.send(content=(
                f"<@{self.target_id}>\n"
                "-All CSSO Roles\n"
                "+CSSO Blacklist\n"
                f"<@&{ROLE_ID_TO_MENTION}>"
            ))

        # 5) Log it via your utils.log_message
        await log_message(
            bot=interaction.client,
            title="/request-blacklist Confirmed",
            description=(
                f"**Invoker:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                f"**Name:** {self.name}\n"
                f"**Discord ID:** {self.target_id}\n"
                f"**Reason:** {self.reason}\n"
                f"**Guilds Banned:** {', '.join(successes) or 'None'}\n"
                f"**Failures:** {', '.join(failures) or 'None'}"
            ),
            color=discord.Color.dark_red()
        )

        # Remove the buttons
        await interaction.edit_original_response(content="✅ Blacklist executed.", view=None)

    @button(label="Dismiss", style=discord.ButtonStyle.secondary, custom_id="request:dismiss")
    async def cancel(self, interaction: discord.Interaction, button: Button):
        if not any(r.id in REQUEST_COMMAND_ROLE_IDS for r in interaction.user.roles):
            return await interaction.response.send_message(
                "❌ You aren’t allowed to dismiss this.",
                ephemeral=True
            )
        await interaction.response.edit_message(content="❌ Request dismissed.", view=None)


def setup_request_blacklist(tree: app_commands.CommandTree):
    @tree.command(
        name="request-blacklist",
        description="Submit a request to blacklist a user (requires image proof)."
    )
    @app_commands.describe(
        user="The user to blacklist",
        reason="Why they should be blacklisted",
        proof="Attach an image as proof"
    )
    async def request_blacklist(
        interaction: discord.Interaction,
        user: discord.User,
        reason: str,
        proof: discord.Attachment
    ):
        # Permission
        if not any(r.id in REQUEST_COMMAND_ROLE_IDS for r in interaction.user.roles):
            return await interaction.response.send_message(
                "❌ You do not have permission to use this command. This command can only be used in the leadership discord.",
                ephemeral=True
            )

        # Require image proof
        if not proof.content_type or not proof.content_type.startswith("image"):
            return await interaction.response.send_message(
                "🚫 You must attach an image for proof!",
                ephemeral=True
            )

        # Ack
        await interaction.response.send_message(
            "✅ Your blacklist request has been sent for review.",
            ephemeral=True
        )

        # Build and send the review embed + buttons
        em = discord.Embed(
            title="🚨 New Blacklist Request",
            description=(
                f"**Target:** {user.mention} (`{user.id}`)\n"
                f"**Reason:** {reason}\n"
                f"**Requested By:** {interaction.user.mention}"
            ),
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        em.set_image(url=proof.url)
        content = f"<@&1047612711099441182>"
        view = RequestBlacklistView(
            target_id=str(user.id),
            name=user.display_name,
            reason=reason,
            proof_url=proof.url,
            requester=interaction.user
        )
        ch = interaction.client.get_channel(BLACKLIST_EMBED_CHANNEL_ID)
        await ch.send(content=content, embed=em, view=view)
