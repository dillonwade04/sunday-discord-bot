import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import tasks
from datetime import datetime, timedelta
import pytz
import asyncio
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# --- CONFIGURATION ---
# Global schedule data – each day maps to a dictionary with "AM" and "PM" slots.
schedule_data = {
    "Monday": {"AM": None, "PM": None},
    "Tuesday": {"AM": None, "PM": None},
    "Wednesday": {"AM": None, "PM": None},
    "Thursday": {"AM": None, "PM": None},
    "Friday": {"AM": None, "PM": None},
    "Saturday": {"AM": None, "PM": None},
    "Sunday": {"AM": None, "PM": None}
}

# Channel ID where the schedule board embed is posted.
SCHEDULE_BOARD_CHANNEL_ID = 1047612975688720387

# File path to persist the schedule board info (message ID + week range).
SCHEDULE_DATA_FILE = "schedule_message.json"

# File path to persist the schedule entries (so they survive restarts).
SCHEDULE_ENTRIES_FILE = "schedule_entries.json"

# Global variable to hold the message ID of the current week’s schedule board.
current_schedule_message_id = None

# Variables to store the current week’s date range for display.
current_week_start = None
current_week_end = None

# Content to be sent along with the schedule embed to ping roles.
SCHEDULE_PING_CONTENT = "<@&1047612734956650607> <@&1309682099506118810> <@&1251634226910986440>"

# Role IDs for permission checks:
SUPERVISOR_ROLE_ID = 1047612736823099484  # Supervisor
ADMIN_ROLE_ID = 1047612711099441182       # HEADS

# Global scheduler instance to prevent garbage collection.
scheduler = None

EST = pytz.timezone("US/Eastern")

# --- PERSISTENCE FUNCTIONS (Message Info) ---
def save_schedule_message_info(message_id, week_start, week_end):
    data = {
        "message_id": message_id,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat()
    }
    with open(SCHEDULE_DATA_FILE, "w") as f:
        json.dump(data, f)

def load_schedule_message_info():
    try:
        with open(SCHEDULE_DATA_FILE, "r") as f:
            data = json.load(f)
            return int(data["message_id"]), datetime.fromisoformat(data["week_start"]).date(), datetime.fromisoformat(data["week_end"]).date()
    except Exception:
        return None, None, None

# --- PERSISTENCE FUNCTIONS (Schedule Entries) ---
def save_schedule_entries():
    """
    Save the current schedule_data dict to a JSON file.
    """
    with open(SCHEDULE_ENTRIES_FILE, "w") as f:
        json.dump(schedule_data, f)

def load_schedule_entries():
    """
    Load schedule data from a JSON file if it exists.
    Overwrites the global schedule_data in memory.
    """
    global schedule_data
    try:
        with open(SCHEDULE_ENTRIES_FILE, "r") as f:
            loaded = json.load(f)
            # Validate or trust the structure
            schedule_data = loaded
    except FileNotFoundError:
        pass  # If no file exists yet, just use the default schedule_data
    except Exception as e:
        print(f"[DEBUG] Failed to load schedule entries: {e}")


# --- HELPER FUNCTIONS ---
def create_schedule_embed(start_date: datetime.date = None, end_date: datetime.date = None) -> discord.Embed:
    """
    Create and return an embed representing the current weekly schedule.
    """
    if start_date and end_date:
        title = f"Weekly Schedule: {start_date.month}/{start_date.day}/{start_date.year} – {end_date.month}/{end_date.day}/{end_date.year}"
    else:
        title = "Weekly Schedule"

    embed = discord.Embed(
        title=title,
        description="Use /schedule-add to schedule your day.\nBelow is the current training schedule:",
        color=discord.Color.green()
    )
    for day, slots in schedule_data.items():
        am_entry = slots["AM"] if slots["AM"] is not None else "No entry"
        pm_entry = slots["PM"] if slots["PM"] is not None else "No entry"
        field_value = f"**AM:** {am_entry}\n**PM:** {pm_entry}"
        embed.add_field(name=day, value=field_value, inline=False)
    embed.set_footer(text="Carolina State Sheriff's Office Administration®", icon_url="https://i.imgur.com/wRbvz3o.png")
    return embed

async def update_schedule_embed(bot: discord.Client):
    """
    Updates the current week's schedule board embed.
    This function only edits an existing embed if a schedule board message exists.
    It will not post a new embed if none exists.
    """
    global current_schedule_message_id, current_week_start, current_week_end
    channel = bot.get_channel(SCHEDULE_BOARD_CHANNEL_ID)
    if not channel:
        print("[DEBUG] Schedule board channel not found.")
        return

    # If no message ID is loaded in memory, try loading from file.
    if current_schedule_message_id is None:
        loaded_id, loaded_start, loaded_end = load_schedule_message_info()
        if loaded_id and loaded_start and loaded_end:
            current_schedule_message_id = loaded_id
            current_week_start = loaded_start
            current_week_end = loaded_end

    if current_schedule_message_id is None:
        # No schedule board exists, so do not post a new embed.
        print("[DEBUG] No schedule board embed found; update aborted.")
        return

    embed = create_schedule_embed(current_week_start, current_week_end)
    try:
        message = await channel.fetch_message(current_schedule_message_id)
        await message.edit(embed=embed)
        print("[DEBUG] Successfully updated schedule board embed.")
    except Exception as e:
        print(f"[DEBUG] Failed to edit schedule board: {e}")


# --- APSCHEDULER WEEKLY JOB ---
async def weekly_schedule_reset_job(bot: discord.Client):
    """
    Resets the schedule_data for the new week and posts a new schedule board embed.
    This job runs exactly at 9:00 AM on Monday Eastern.
    """
    global schedule_data, current_schedule_message_id, current_week_start, current_week_end
    now = datetime.now(EST)
    print(f"[DEBUG] weekly_schedule_reset_job triggered at {now} (Weekday: {now.strftime('%A')})")

    # Clear schedule_data for the new week
    schedule_data = {day: {"AM": None, "PM": None} for day in schedule_data}
    save_schedule_entries()  # Save the cleared data

    current_week_start = now.date()
    current_week_end = (now + timedelta(days=6)).date()

    channel = bot.get_channel(SCHEDULE_BOARD_CHANNEL_ID)
    if channel:
        new_embed = create_schedule_embed(current_week_start, current_week_end)
        message = await channel.send(content=SCHEDULE_PING_CONTENT, embed=new_embed)
        current_schedule_message_id = message.id
        # Save the new message ID and the new week range
        save_schedule_message_info(current_schedule_message_id, current_week_start, current_week_end)
        print(f"[DEBUG] New schedule board posted. ID: {current_schedule_message_id}")
    else:
        print("[DEBUG] Failed to post new schedule board: channel not found.")

def start_weekly_schedule_reset(bot: discord.Client):
    """
    Starts an APScheduler job that posts a new schedule board embed exactly at 9:00 AM on Monday Eastern.
    """
    global scheduler
    scheduler = AsyncIOScheduler(timezone=EST)
    job = scheduler.add_job(
        weekly_schedule_reset_job,
        CronTrigger(day_of_week='mon', hour=10, minute=0),
        args=[bot],
        id='weekly_schedule_reset'
    )
    scheduler.start()
    print("[DEBUG] APScheduler started with job:", scheduler.get_jobs())
    print(f"[DEBUG] Next run time: {job.next_run_time}")


# --- SLASH COMMANDS ---
def register_commands(tree: app_commands.CommandTree):
    """
    Register scheduling commands:
      - /schedule-add: Add your name to an AM or PM slot for a specified day (Supervisor only).
      - /schedule-reset: Reset the weekly schedule (Admin only).
    """

    @tree.command(name="schedule-add", description="Add your name to an AM or PM slot for a specified day (Supervisor only).")
    @app_commands.describe(
        day="Day of the week (e.g., Monday, Tuesday, etc.)",
        slot="Time slot: AM or PM"
    )
    @app_commands.choices(slot=[
        Choice(name="AM", value="AM"),
        Choice(name="PM", value="PM")
    ])
    async def schedule_add(interaction: discord.Interaction, day: str, slot: str):
        if not any(role.id == SUPERVISOR_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message("You do not have permission to add to the schedule (Supervisor only).", ephemeral=True)
            return

        day_title = day.title()
        if day_title not in schedule_data:
            await interaction.response.send_message("Invalid day. Please use a day from Monday to Sunday.", ephemeral=True)
            return

        if schedule_data[day_title][slot] is not None:
            await interaction.response.send_message(f"The {slot} slot for {day_title} is already taken.", ephemeral=True)
            return

        user_name = interaction.user.display_name
        # Count how many times the user is already scheduled.
        user_entries = sum(1 for slots in schedule_data.values() for entry in slots.values() if entry == user_name)
        if user_entries >= 3:
            await interaction.response.send_message("You have already added yourself to the schedule 3 times. You cannot add any more entries.", ephemeral=True)
            return

        schedule_data[day_title][slot] = user_name
        # Save the updated schedule_data to JSON
        save_schedule_entries()

        # Update the existing schedule board embed if it exists
        await update_schedule_embed(interaction.client)
        await interaction.response.send_message(
            f"Added your name to the {slot} slot on **{day_title}**. (The schedule board has been updated.)",
            ephemeral=False
        )

    @tree.command(name="schedule-reset", description="Reset the weekly schedule (Admin only).")
    async def schedule_reset(interaction: discord.Interaction):
        if not any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message("You do not have permission to reset the schedule (Admin only).", ephemeral=True)
            return

        global schedule_data
        schedule_data = {day: {"AM": None, "PM": None} for day in schedule_data}
        save_schedule_entries()

        # Only update if a schedule board exists
        await update_schedule_embed(interaction.client)
        await interaction.response.send_message("The weekly schedule has been reset. (The schedule board has been updated.)", ephemeral=True)
