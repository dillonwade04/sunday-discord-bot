"""
ai_chat_cog_gemini.py

Mention-triggered AI Q&A cog for discord.py bots, using Google's Gemini API
free tier (no cost, rate-limited).

Usage:
    In your main bot file:
        from ai_chat_cog_gemini import AIChatCog
        await bot.add_cog(AIChatCog(bot))

How it works:
    - User pings the bot anywhere in a server and asks a question
      (e.g. "@Bot what's the SOP on vehicle pursuits?")
    - The cog strips the mention, sends the question + your reference
      documents to Gemini, and replies in the channel.
    - Reference documents are loaded once at startup from REFERENCE_DOCS_DIR.
      Just drop .txt or .md files in that folder (SOP.txt, disciplinary.txt, etc).

Requirements:
    pip install discord.py google-genai

Environment variables expected:
    GEMINI_API_KEY   - get one free at https://aistudio.google.com/apikey
                        (no credit card required)

IMPORTANT — free tier data privacy note:
    Google's free tier terms allow using your prompts/responses to improve
    their models (this changes if you ever enable billing on the project).
    If your SOP docs are sensitive/internal-only, keep that in mind. It's
    unlikely to matter for a public-facing RP server SOP, but worth knowing.

IMPORTANT — free tier rate limits:
    Free tier is limited to roughly 10-15 requests/minute and ~1,000-1,500
    requests/day on Flash models (Google can change this at any time — check
    https://ai.google.dev/gemini-api/docs/rate-limits for current numbers).
    This cog includes basic cooldown handling so one user spamming mentions
    can't burn through your daily quota.
"""

import os
import re
import glob
import logging
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands
from google import genai
from google.genai import types
from google.genai.errors import ClientError

logger = logging.getLogger("ai_chat_cog_gemini")

# ---- Configuration ----------------------------------------------------

REFERENCE_DOCS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "docs", "reference")
)

# Chain of free-tier models to try in order. Each model has its own
# separate daily quota, so when one is exhausted for the day, the cog
# automatically falls through to the next one. List your preferred
# (highest quality) model first.
MODEL_FALLBACK_CHAIN = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]

MAX_REPLY_CHARS = 1900  # stay under Discord's 2000 char limit with room to spare

# Google's daily quotas reset at midnight Pacific time.
PACIFIC_RESET_TZ = timezone(timedelta(hours=-8))  # PST; close enough for reset tracking

SYSTEM_PROMPT_TEMPLATE = """You are the department AI assistant for a GTA V law enforcement roleplay (LEO RP) server. \
You answer questions about department policy using ONLY the reference documents provided below. \
These documents include the Standard Operating Procedures (SOP) and disciplinary policy.

Rules:
- Answer strictly based on the reference documents. Do not invent policy that isn't in them.
- If the documents don't cover the question, say so plainly and suggest the user ask a supervisor/FTO.
- Citation format: after each policy point, cite the source in parentheses with the ENTIRE
  citation — document name and section number together — wrapped in a single markdown
  codeblock (backticks). Never include a file extension like .txt or .md.
  If the passage includes a specific section/rule number in the source text, format it as:
  (`SOP, Section 7.1`). If no section number exists in the source text, cite the document
  name alone inside the codeblock: (`Strikes Manual`). Never invent a section number that
  isn't explicitly in the text. Do not put the document name in its own separate codeblock
  from the section number — they must be inside the same backticks together.
- Keep answers concise and practical — this is for in-character/OOC department use, not essay writing.
- If a question is ambiguous, give your best interpretation and note the ambiguity.

=== REFERENCE DOCUMENTS ===
{reference_docs}
=== END REFERENCE DOCUMENTS ===
"""


def load_reference_docs() -> str:
    """Load all .txt/.md files from REFERENCE_DOCS_DIR into one blob of text."""
    if not os.path.isdir(REFERENCE_DOCS_DIR):
        logger.warning("Reference docs directory not found: %s", REFERENCE_DOCS_DIR)
        return "(no reference documents loaded)"

    chunks = []
    paths = sorted(
        glob.glob(os.path.join(REFERENCE_DOCS_DIR, "*.txt"))
        + glob.glob(os.path.join(REFERENCE_DOCS_DIR, "*.md"))
    )
    for path in paths:
        name = os.path.basename(path)
        display_name = os.path.splitext(name)[0]  # strip .txt/.md extension
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().strip()
        chunks.append(f"--- DOCUMENT: {display_name} ---\n{content}")

    if not chunks:
        logger.warning("No .txt/.md files found in %s", REFERENCE_DOCS_DIR)
        return "(no reference documents loaded)"

    logger.info("Loaded %d reference document(s): %s", len(chunks), ", ".join(paths))
    return "\n\n".join(chunks)


class AIChatCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set")
        self.client = genai.Client(api_key=api_key)
        self.reference_docs = load_reference_docs()
        self.system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            reference_docs=self.reference_docs
        )
        # Simple per-user cooldown so one person can't burn the whole daily
        # free-tier quota. Adjust rate/per to taste.
        self._cooldown = commands.CooldownMapping.from_cooldown(
            3, 60, commands.BucketType.user  # 3 questions per 60s per user
        )
        # Tracks which models have hit their daily quota today and when
        # that exhaustion should be cleared (next Pacific midnight).
        # Format: {model_name: reset_datetime}
        self._exhausted_until = {}

    def _next_pacific_midnight(self) -> datetime:
        now = datetime.now(PACIFIC_RESET_TZ)
        tomorrow = (now + timedelta(days=1)).date()
        return datetime(
            tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=PACIFIC_RESET_TZ
        )

    def _mark_exhausted(self, model: str):
        self._exhausted_until[model] = self._next_pacific_midnight()
        logger.warning(
            "Model %s hit its daily quota, falling back until %s",
            model,
            self._exhausted_until[model],
        )

    def _available_models(self):
        """Return the fallback chain, skipping models still marked exhausted today."""
        now = datetime.now(PACIFIC_RESET_TZ)
        expired = [m for m, reset_at in self._exhausted_until.items() if now >= reset_at]
        for m in expired:
            del self._exhausted_until[m]
        return [m for m in MODEL_FALLBACK_CHAIN if m not in self._exhausted_until]

    def reload_docs(self):
        """Call this (e.g. from an admin command) to pick up doc edits without restarting."""
        self.reference_docs = load_reference_docs()
        self.system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            reference_docs=self.reference_docs
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        # Only respond to an actual typed @mention in the message text —
        # NOT a reply-triggered mention (Discord silently adds the replied-to
        # user to message.mentions when "ping on reply" is enabled, even if
        # they never typed @BotName).
        bot_mention_pattern = rf"<@!?{self.bot.user.id}>"
        if not re.search(bot_mention_pattern, message.content):
            return

        # Per-user rate limit check
        bucket = self._cooldown.get_bucket(message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            await message.reply(
                f"Slow down a bit — try again in {retry_after:.0f}s. "
                "(Keeping us under the free API quota.)"
            )
            return

        question = message.content
        for mention in message.mentions:
            question = question.replace(f"<@{mention.id}>", "")
            question = question.replace(f"<@!{mention.id}>", "")
        question = question.strip()

        if not question:
            await message.reply(
                "Ask me a question about department policy, e.g. "
                f"`@{self.bot.user.name} what's the SOP on vehicle pursuits?`"
            )
            return

        async with message.channel.typing():
            answer = None
            candidates = self._available_models()

            if not candidates:
                await message.reply(
                    "All free-tier models have hit their daily limit — "
                    "try again after the quota resets (midnight Pacific time)."
                )
                return

            for model in candidates:
                try:
                    response = await self.client.aio.models.generate_content(
                        model=model,
                        contents=question,
                        config=types.GenerateContentConfig(
                            system_instruction=self.system_prompt,
                            max_output_tokens=1500,
                            thinking_config=types.ThinkingConfig(thinking_budget=0),
                        ),
                    )
                    answer = (response.text or "").strip()
                    try:
                        finish_reason = response.candidates[0].finish_reason
                        if finish_reason and "MAX_TOKENS" in str(finish_reason):
                            logger.warning(
                                "Response from %s was truncated by max_output_tokens; "
                                "consider raising the limit further.",
                                model,
                            )
                    except (AttributeError, IndexError):
                        pass
                    break  # success — stop trying further models
                except ClientError as e:
                    # 429 = quota/rate limit hit for this specific model.
                    # Mark it exhausted for today and fall through to the next one.
                    status = getattr(e, "status_code", None) or getattr(e, "code", None)
                    if status == 429 or "RESOURCE_EXHAUSTED" in str(e).upper():
                        self._mark_exhausted(model)
                        continue
                    logger.warning("Gemini API error on %s: %s", model, e)
                    continue
                except Exception:
                    logger.exception("AI chat request failed on model %s", model)
                    continue

            if answer is None:
                await message.reply(
                    "All free-tier models are rate-limited or unavailable right now — "
                    "try again in a bit."
                )
                return

        if not answer:
            answer = "I couldn't come up with an answer for that."

        for i in range(0, len(answer), MAX_REPLY_CHARS):
            chunk = answer[i : i + MAX_REPLY_CHARS]
            await message.reply(chunk)


async def setup(bot: commands.Bot):
    await bot.add_cog(AIChatCog(bot))
