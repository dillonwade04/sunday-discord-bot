"""Environment-backed secrets used by the bot.

Keep credential values in a local ``.env`` file. The file is intentionally
ignored by Git; ``.env.example`` documents the required variable names.
"""

import os


def required_env(name: str) -> str:
    """Return a configured value or fail with a clear startup error."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value


DISCORD_TAGS_WEBHOOK_URL = required_env("DISCORD_TAGS_WEBHOOK_URL")
DISCORD_APPLICATIONS_WEBHOOK_URL = required_env(
    "DISCORD_APPLICATIONS_WEBHOOK_URL"
)
CLOCKIFY_API_KEY = required_env("CLOCKIFY_API_KEY")
CLOCKIFY_WORKSPACE_ID = required_env("CLOCKIFY_WORKSPACE_ID")
FORM_WEBHOOK_SECRET = required_env("FORM_WEBHOOK_SECRET")
SUBDIVISION_FORM_WEBHOOK_SECRET = required_env(
    "SUBDIVISION_FORM_WEBHOOK_SECRET"
)
OAUTH_API_SECRET = required_env("OAUTH_API_SECRET")
