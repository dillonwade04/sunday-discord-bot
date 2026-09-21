# Clockify integration commands.
import requests
import discord
from discord import app_commands

from config import CLOCKIFY_API_KEY, CLOCKIFY_WORKSPACE_ID

# Clockify workspace configuration
WORKSPACE_ID = CLOCKIFY_WORKSPACE_ID

BASE_URL = "https://api.clockify.me/api/v1"


def invite_user_to_clockify(workspace_id, email):
    """
    Sends an invitation to a user to join the Clockify workspace.

    Args:
        workspace_id (str): The Clockify workspace ID.
        email (str): The email address of the user to invite.

    Returns:
        dict: Response from the Clockify API.
    """
    url = f"{BASE_URL}/workspaces/{workspace_id}/users"
    headers = {
        "X-Api-Key": CLOCKIFY_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "email": email,
        "membershipStatus": "ACTIVE"
    }

    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()

    if response.status_code == 200:
        return {"success": True, "message": f"User {email} invited successfully!"}
    else:
        return {"success": False, "message": response_data.get('message', 'Unknown error occurred.')}


def register_commands(tree: app_commands.CommandTree):
    @tree.command(name="clockify-add", description="Add or invite a user to the Clockify workspace.")
    @app_commands.describe(email="The email address of the user to add to Clockify.")
    async def clockify_add(interaction: discord.Interaction, email: str):
        """
        Invite a user to the configured Clockify workspace.
        """
        await interaction.response.defer(ephemeral=True)

        try:
            result = invite_user_to_clockify(WORKSPACE_ID, email)

            if result["success"]:
                await interaction.followup.send(f"✅ {result['message']}", ephemeral=True)
            else:
                await interaction.followup.send(f"⚠️ {result['message']}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"⚠️ Failed to invite user: {str(e)}", ephemeral=True)
