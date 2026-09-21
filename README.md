# S.U.N.D.A.Y. Discord Bot

S.U.N.D.A.Y. is a multi-purpose Discord bot built for the Carolina State
Sheriff's Office roleplay community. It combines moderation, staff workflows,
HR ticketing, scheduling, automated activity checks, form webhooks, and a
Gemini-powered reference assistant.

## Features

- Moderation and cross-server ban/unban workflows
- Promotion, demotion, transfer, blacklist, and application review commands
- HR tickets, HTML transcripts, leave-of-absence tracking, and staff reviews
- Background checks, ridealong requests, schedules, and role management
- Welcome/goodbye messages, rotating status text, utility commands, and games
- Gemini Q&A grounded in the documents under `docs/reference/`
- Authenticated HTTP form receivers on ports `8019` and `8134`

## Project structure

```text
.
|-- .github/workflows/   # Automated syntax checks
|-- docs/reference/      # Knowledge used by the Gemini assistant
|-- examples/data/       # Example and legacy JSON data
|-- src/                 # Bot entry point and feature modules
|-- .env.example         # Safe configuration template
|-- .gitignore           # Secrets, caches, and runtime data exclusions
`-- requirements.txt     # Python dependencies
```

## Requirements

- Python 3.10 or newer
- A Discord application and bot token
- Discord privileged intents for members, presences, and message content
- Credentials for the optional Gemini and Clockify integrations
- Two Discord webhook URLs and two strong shared secrets for the form services

## Setup

1. Create and activate a virtual environment.

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies.

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env`, then replace every placeholder with a newly
   issued credential.

   ```powershell
   Copy-Item .env.example .env
   ```

4. Run the bot from the repository root.

   ```powershell
   python src/bot.py
   ```

## Configuration

| Variable | Purpose |
| --- | --- |
| `DISCORD_TOKEN` | Authenticates the Discord bot |
| `GEMINI_API_KEY` | Enables the Gemini reference assistant |
| `CLOCKIFY_API_KEY` | Authenticates Clockify workspace requests |
| `CLOCKIFY_WORKSPACE_ID` | Selects the Clockify workspace |
| `DISCORD_TAGS_WEBHOOK_URL` | Sends role/tag workflow messages |
| `DISCORD_APPLICATIONS_WEBHOOK_URL` | Sends application decision messages |
| `FORM_WEBHOOK_SECRET` | Protects the main form receiver |
| `SUBDIVISION_FORM_WEBHOOK_SECRET` | Protects the subdivision form receiver |
| `OAUTH_API_SECRET` | Authenticates calls to the companion OAuth service |

The bot also contains community-specific guild, role, and channel IDs in its
feature modules. Update those IDs before deploying it to a different Discord
community.

## Runtime data

The bot creates JSON state files and HTML ticket transcripts while running.
Those files are intentionally excluded from version control because they may
contain Discord user data. Back them up separately if they are operationally
important.

## Security

- Never commit `.env` or paste credentials into source files.
- Use unique, high-entropy values for both form webhook secrets.
- Rotate a credential immediately if it is exposed in a file, log, or commit.
- Keep generated transcripts and runtime JSON data private.

Public repository visibility does not automatically grant permission to reuse
the code. No software license is included at this time.
