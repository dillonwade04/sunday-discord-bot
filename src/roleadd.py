import discord
from discord import app_commands
from discord.ui import View, Button, button
from utils import log_message  # Your existing log system

REQUIRED_ROLE_NAMES = {"Heads", "Bots", "BOT"}

def can_use(interaction: discord.Interaction) -> bool:
    return any(role.name in REQUIRED_ROLE_NAMES for role in interaction.user.roles)


def register_commands(tree: app_commands.CommandTree):
    @tree.command(name="role-add", description="Give a role to a user.")
    @app_commands.describe(member="The member to give the role to", role="The role to give")
    async def role_add(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        if not can_use(interaction):
            return await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
        if role in member.roles:
            return await interaction.response.send_message(
                f"{member.mention} already has the {role.name} role.", ephemeral=True
            )
        await interaction.response.defer(ephemeral=True)
        try:
            await member.add_roles(role)
            await log_message(
                interaction.client,
                title="Role Added",
                description=(
                    f"👤 **User:** {member.mention} (`{member.id}`)\n"
                    f"➕ **Role Added:** {role.name}\n"
                    f"👮 **By:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"🌐 **Guild:** {interaction.guild.name} (`{interaction.guild.id}`)"
                ),
                color=discord.Color.green()
            )
            await interaction.followup.send(f"✅ Added {role.name} to {member.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to add that role.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"⚠️ An error occurred: `{e}`", ephemeral=True)

    @tree.command(name="role-remove", description="Remove a role from a user.")
    @app_commands.describe(member="The member to remove the role from", role="The role to remove")
    async def role_remove(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        if not can_use(interaction):
            return await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
        if role not in member.roles:
            return await interaction.response.send_message(
                f"{member.mention} does not have the {role.name} role.", ephemeral=True
            )
        await interaction.response.defer(ephemeral=True)
        try:
            await member.remove_roles(role)
            await log_message(
                interaction.client,
                title="Role Removed",
                description=(
                    f"👤 **User:** {member.mention} (`{member.id}`)\n"
                    f"➖ **Role Removed:** {role.name}\n"
                    f"👮 **By:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"🌐 **Guild:** {interaction.guild.name} (`{interaction.guild.id}`)"
                ),
                color=discord.Color.red()
            )
            await interaction.followup.send(f"✅ Removed {role.name} from {member.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to remove that role.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"⚠️ An error occurred: `{e}`", ephemeral=True)

    @tree.command(
        name="role-removeall",
        description="Remove every non-@everyone role from a user (with confirmation)."
    )
    @app_commands.describe(member="The member to strip all roles from")
    async def role_remove_all(interaction: discord.Interaction, member: discord.Member):
        if not can_use(interaction):
            return await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
        default_role = member.guild.default_role
        roles_to_remove = [r for r in member.roles if r != default_role]
        count = len(roles_to_remove)
        if count == 0:
            return await interaction.response.send_message(
                f"ℹ️ {member.mention} has no removable roles.", ephemeral=True
            )
        view = ConfirmRemoveAllView(
            member_id=member.id,
            role_ids=[r.id for r in roles_to_remove],
            requester_id=interaction.user.id
        )
        await interaction.response.send_message(
            f"Are you sure you want to remove **{count}** roles from {member.mention}?",
            view=view,
            ephemeral=True
        )


class ConfirmRemoveAllView(View):
    def __init__(self, member_id: int, role_ids: list[int], requester_id: int):
        super().__init__(timeout=60)
        self.member_id = member_id
        self.role_ids = role_ids
        self.requester_id = requester_id

    @button(label="Confirm", style=discord.ButtonStyle.danger, custom_id="confirm_remove_all")
    async def confirm(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.requester_id:
            return await interaction.response.send_message(
                "❌ Only the command invoker can confirm this.", ephemeral=True
            )
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        member = guild.get_member(self.member_id) or await guild.fetch_member(self.member_id)
        roles = [guild.get_role(rid) for rid in self.role_ids]
        await member.remove_roles(*roles, reason=f"All roles removed by {interaction.user}")
        names = [r.name for r in roles if r]
        await log_message(
            interaction.client,
            title="All Roles Removed",
            description=(
                f"👤 **User:** {member.mention} (`{member.id}`)\n"
                f"➖ **Roles Removed ({len(names)}):** {', '.join(names)}\n"
                f"👮 **By:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                f"🌐 **Guild:** {guild.name} (`{guild.id}`)"
            ),
            color=discord.Color.dark_red()
        )
        await interaction.followup.send(
            f"✅ Removed {len(names)} roles from {member.mention}.", ephemeral=True
        )
        await interaction.edit_original_response(view=None)

    @button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel_remove_all")
    async def cancel(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.requester_id:
            return await interaction.response.send_message(
                "❌ Only the command invoker can cancel this.", ephemeral=True
            )
        await interaction.response.edit_message(
            content="❌ Role removal cancelled.", view=None, ephemeral=True
        )
