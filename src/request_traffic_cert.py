import json
import os
from datetime import datetime

import discord
from discord import app_commands
from discord.ui import View, Select, Button

REQUEST_CHANNEL_ID = 1047611353751367680
REVIEWER_ROLE_ID = 1047611191851221023
TARGET_GUILD_ID = 1047610191711051866
TARGET_INVITE_CHANNEL_ID = 1288298156232282122

ROLE_OPTIONS = [
    "A.S.U. Trainee",
    "A.S.U. Advanced Trainee",
    "P.A. Trainee",
    "Dive Team Trainee",
    "M.U. Trainee"
    "M.U. Trainee"
    "B.C.U. Trainee"
]

DATA_FILE = "traffic_cert_requests.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"messages": {}, "pending_join_roles": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def user_has_role(member: discord.Member, role_id: int) -> bool:
    return any(role.id == role_id for role in member.roles)


class TrafficCertRoleSelect(Select):
    def __init__(self, requester: discord.Member):
        self.requester = requester

        options = [
            discord.SelectOption(label=role_name, value=role_name)
            for role_name in ROLE_OPTIONS
        ]

        super().__init__(
            placeholder="Select requested role(s)",
            min_values=1,
            max_values=len(options),
            options=options,
            custom_id="traffic_cert_role_select"
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.requester.id:
            return await interaction.response.send_message(
                "❌ Only the user who ran this command can use this selector.",
                ephemeral=True
            )

        reviewer_role = interaction.guild.get_role(REVIEWER_ROLE_ID)
        if reviewer_role is None:
            return await interaction.response.send_message(
                "❌ Reviewer role not found.",
                ephemeral=True
            )

        requested_roles = list(self.values)

        embed = discord.Embed(
            title="Traffic Certification Request",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Requester", value=f"{self.requester.mention} (`{self.requester.id}`)", inline=False)
        embed.add_field(name="Requested Roles", value="\n".join(f"• {r}" for r in requested_roles), inline=False)
        embed.add_field(name="Status", value="Pending Review", inline=False)
        embed.set_footer(text=f"requester_id:{self.requester.id}")

        review_view = TrafficCertReviewView()

        msg = await interaction.channel.send(
            content=reviewer_role.mention,
            embed=embed,
            view=review_view,
            allowed_mentions=discord.AllowedMentions(roles=True)
        )

        data = load_data()
        data["messages"][str(msg.id)] = {
            "requester_id": self.requester.id,
            "channel_id": interaction.channel.id,
            "guild_id": interaction.guild.id,
            "requested_roles": requested_roles,
            "status": "pending"
        }
        save_data(data)

        await interaction.response.send_message(
            "✅ Your traffic cert request has been submitted.",
            ephemeral=True
        )


class TrafficCertSelectionView(View):
    def __init__(self, requester: discord.Member):
        super().__init__(timeout=300)
        self.add_item(TrafficCertRoleSelect(requester))


class TrafficCertReviewView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Accept",
        style=discord.ButtonStyle.green,
        custom_id="traffic_cert_accept"
    )
    async def accept_button(self, interaction: discord.Interaction, button: Button):
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("❌ Member lookup failed.", ephemeral=True)

        if not user_has_role(interaction.user, REVIEWER_ROLE_ID):
            return await interaction.response.send_message(
                "❌ You do not have permission to accept this request.",
                ephemeral=True
            )

        data = load_data()
        request_data = data["messages"].get(str(interaction.message.id))

        if not request_data:
            return await interaction.response.send_message(
                "❌ Request data not found for this message.",
                ephemeral=True
            )

        if request_data["status"] != "pending":
            return await interaction.response.send_message(
                "❌ This request has already been handled.",
                ephemeral=True
            )

        requester_id = request_data["requester_id"]
        requested_roles = request_data["requested_roles"]

        target_guild = interaction.client.get_guild(TARGET_GUILD_ID)
        if target_guild is None:
            return await interaction.response.send_message(
                "❌ Target guild not found in bot cache.",
                ephemeral=True
            )

        invite_channel = target_guild.get_channel(TARGET_INVITE_CHANNEL_ID)
        if invite_channel is None:
            return await interaction.response.send_message(
                "❌ Invite channel not found.",
                ephemeral=True
            )

        try:
            invite = await invite_channel.create_invite(
                max_age=86400,
                max_uses=1,
                unique=True,
                reason=f"Traffic cert accepted for user {requester_id}"
            )
        except Exception as e:
            return await interaction.response.send_message(
                f"❌ Failed to create invite: {e}",
                ephemeral=True
            )

        data["pending_join_roles"][str(requester_id)] = {
            "guild_id": TARGET_GUILD_ID,
            "roles": requested_roles
        }

        data["messages"][str(interaction.message.id)]["status"] = "accepted"
        data["messages"][str(interaction.message.id)]["reviewed_by"] = interaction.user.id
        save_data(data)

        user = interaction.client.get_user(requester_id)
        if user:
            try:
                dm_embed = discord.Embed(
                    title="Traffic Certification Request Accepted",
                    description=(
                        "Your request was accepted.\n\n"
                        f"Join the server here:\n{invite.url}\n\n"
                        "Once you join, your requested roles will be assigned automatically if they exist by the same role name."
                    ),
                    color=discord.Color.green()
                )
                await user.send(embed=dm_embed)
            except Exception:
                pass

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.set_field_at(2, name="Status", value=f"Accepted by {interaction.user.mention}", inline=False)

        for item in self.children:
            item.disabled = True

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message("✅ Request accepted.", ephemeral=True)

    @discord.ui.button(
        label="Denied",
        style=discord.ButtonStyle.red,
        custom_id="traffic_cert_deny"
    )
    async def deny_button(self, interaction: discord.Interaction, button: Button):
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("❌ Member lookup failed.", ephemeral=True)

        if not user_has_role(interaction.user, REVIEWER_ROLE_ID):
            return await interaction.response.send_message(
                "❌ You do not have permission to deny this request.",
                ephemeral=True
            )

        data = load_data()
        request_data = data["messages"].get(str(interaction.message.id))

        if not request_data:
            return await interaction.response.send_message(
                "❌ Request data not found for this message.",
                ephemeral=True
            )

        if request_data["status"] != "pending":
            return await interaction.response.send_message(
                "❌ This request has already been handled.",
                ephemeral=True
            )

        requester_id = request_data["requester_id"]
        data["messages"][str(interaction.message.id)]["status"] = "denied"
        data["messages"][str(interaction.message.id)]["reviewed_by"] = interaction.user.id
        save_data(data)

        user = interaction.client.get_user(requester_id)
        if user:
            try:
                await user.send("❌ Your traffic certification request was denied.")
            except Exception:
                pass

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.set_field_at(2, name="Status", value=f"Denied by {interaction.user.mention}", inline=False)

        for item in self.children:
            item.disabled = True

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message("✅ Request denied.", ephemeral=True)


def register_commands(tree: app_commands.CommandTree):
    @tree.command(name="request-traffic-cert", description="Request traffic certification roles.")
    async def request_traffic_cert(interaction: discord.Interaction):
        if interaction.channel_id != REQUEST_CHANNEL_ID:
            return await interaction.response.send_message(
                "❌ This command can only be used in the designated channel.",
                ephemeral=True
            )

        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message(
                "❌ This command must be used in a server.",
                ephemeral=True
            )

        view = TrafficCertSelectionView(interaction.user)
        await interaction.response.send_message(
            "Select the role(s) you are requesting below.",
            view=view,
            ephemeral=True
        )


async def setup_persistent_views(bot: discord.Client):
    bot.add_view(TrafficCertReviewView())


async def handle_traffic_cert_join(member: discord.Member):
    if member.guild.id != TARGET_GUILD_ID:
        return

    data = load_data()
    pending = data["pending_join_roles"].get(str(member.id))
    if not pending:
        return

    role_names = pending.get("roles", [])
    roles_to_add = []

    for role_name in role_names:
        role = discord.utils.get(member.guild.roles, name=role_name)
        if role:
            roles_to_add.append(role)

    if roles_to_add:
        try:
            await member.add_roles(*roles_to_add, reason="Approved traffic cert request")
        except Exception:
            return

    data["pending_join_roles"].pop(str(member.id), None)
    save_data(data)
