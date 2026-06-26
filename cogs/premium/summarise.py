import re
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone, timedelta
from typing import Optional
from utils.helpers.helpers_new import LLMHelper

# ── helpers ──────────────────────────────────────────────────────────────────

def parse_since(since_str: str) -> Optional[datetime]:
    """
    Parse a human-readable duration string into a UTC cutoff datetime.
    Accepted formats: 30m, 2h, 1d, 7d, 2w
    Returns None if unparseable.
    """
    pattern = re.fullmatch(r"(\d+)\s*([mhdw])", since_str.strip().lower())
    if not pattern:
        return None

    value, unit = int(pattern.group(1)), pattern.group(2)
    delta_map = {"m": "minutes", "h": "hours", "d": "days", "w": "weeks"}
    delta = timedelta(**{delta_map[unit]: value})
    return datetime.now(timezone.utc) - delta


def relative_time(created_at: datetime) -> str:
    """Return a human-readable relative timestamp like '2h 5m ago'."""
    now = datetime.now(timezone.utc)
    age = now - created_at
    total_secs = int(age.total_seconds())

    if total_secs < 60:
        return f"{total_secs}s ago"
    elif total_secs < 3600:
        return f"{total_secs // 60}m ago"
    elif total_secs < 86400:
        h, m = total_secs // 3600, (total_secs % 3600) // 60
        return f"{h}h {m}m ago"
    else:
        d, h = total_secs // 86400, (total_secs % 86400) // 3600
        return f"{d}d {h}h ago"


VALID_MSG_TYPES = {discord.MessageType.default, discord.MessageType.reply}

def format_messages(messages: list[discord.Message]) -> str:
    """
    Format a list of messages (oldest → newest) into a structured string for the LLM.
    """
    lines = []
    for msg in messages:
        # skip system messages (join, leave, pin, etc.)
        if msg.type not in VALID_MSG_TYPES:
            continue
        # skip bots
        if msg.author.bot:
            continue

        content = msg.content or ""

        # surface attachments
        if msg.attachments:
            names = ", ".join(a.filename for a in msg.attachments)
            content += f" [attachment: {names}]"

        # surface embeds
        if msg.embeds:
            content += " [embed]"

        # surface reply context
        if msg.reference and msg.type == discord.MessageType.reply:
            content = f"[replying to msg id {msg.reference.message_id}] " + content

        # skip truly empty messages (e.g. sticker-only)
        if not content.strip():
            continue

        time_str = relative_time(msg.created_at)
        line = (
            f"[{time_str}] "
            f"{msg.author.display_name} ({msg.author.id}) (<@{msg.author.id}>): "
            f"{content}"
        )
        lines.append(line)

    return "\n".join(lines)


def build_prompt(formatted: str, topic: Optional[str]) -> str:
    # askllm prepends system_prompt, so we extend it here with task-specific context.
    base = (
        "You are now acting as a conversation summariser.\n"
        "Summarize the following Discord conversation concisely.\n"
        "Messages are ordered oldest to newest.\n"
        "Format: [time ago] DisplayName (user_id) (<@mention>): content\n\n"
    )
    if topic:
        base += f"Focus your summary specifically on discussions related to: {topic}\n\n"
    base += "Messages:\n" + formatted + "\n\nSummary:"
    return base


ROUGH_TOKEN_LIMIT = 60_000  # ~15k tokens, safe for most providers

# ── cog ──────────────────────────────────────────────────────────────────────

class SummarizeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.LLMinstance = LLMHelper()  

    @app_commands.command(
        name="summarize",
        description="Summarize recent messages from a channel."
    )
    @app_commands.describe(
        channel="Channel to summarize",
        limit="Number of messages to fetch (default 100, max 500)",
        since="Time window, e.g. 30m, 2h, 1d, 7d (hardcap: 500 messages)",
        topic="Focus the summary on a specific topic or keyword",
        #public="Post the summary publicly? (default: only visible to you)",
    )
    async def summarize(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        limit: Optional[int] = None,
        since: Optional[str] = None,
        topic: Optional[str] = None,
        #public: bool = False,
    ):
        await interaction.response.defer(ephemeral=False, thinking=True)

        # ── permission check ─────────────────────────────────────────────────
        perms = channel.permissions_for(interaction.guild.me)
        if not perms.read_messages or not perms.read_message_history:
            await interaction.followup.send(
                f"❌ I don't have permission to read {channel.mention}.",
                ephemeral=False
            )
            return

        # ── resolve effective limit ───────────────────────────────────────────
        cutoff: Optional[datetime] = None

        if since:
            cutoff = parse_since(since)
            if cutoff is None:
                await interaction.followup.send(
                    "❌ Couldn't parse `since`. Use formats like `30m`, `2h`, `1d`, `7d`, `2w`.",
                    ephemeral=True
                )
                return
            # hardcap at 500 when since is provided
            effective_limit = min(limit or 500, 500)
        else:
            effective_limit = limit or 100  # default 100, no cap enforced

        # ── fetch messages ────────────────────────────────────────────────────
        raw: list[discord.Message] = []

        async for msg in channel.history(limit=effective_limit, oldest_first=False):
            if cutoff and msg.created_at < cutoff:
                break  # gone past the time window
            raw.append(msg)

        if not raw:
            await interaction.followup.send(
                f"No messages found in {channel.mention} for the given parameters.",
                ephemeral=True
            )
            return

        # oldest → newest for LLM
        raw.reverse()

        # ── format ───────────────────────────────────────────────────────────
        formatted = format_messages(raw)

        if not formatted.strip():
            await interaction.followup.send(
                "No readable messages found (all messages were bots/system messages).",
                ephemeral=True
            )
            return

        # rough token guard
        if len(formatted) > ROUGH_TOKEN_LIMIT:
            formatted = formatted[-ROUGH_TOKEN_LIMIT:]  # keep most recent content

        # ── build prompt and call LLM ─────────────────────────────────────────
        prompt = build_prompt(formatted, topic)
        summary = await self._call_llm(prompt)

        # askllm exhausted retries → returns a discord.Embed from customError()
        if isinstance(summary, discord.Embed):
            await interaction.followup.send(embed=summary, ephemeral=True)
            return

        # ── build embed ───────────────────────────────────────────────────────
        embed = discord.Embed(
            title=f"📋 Summary — #{channel.name}",
            description=summary,
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )

        # metadata footer
        meta_parts = [f"{len(raw)} messages"]
        if since:
            meta_parts.append(f"since {since}")
        if topic:
            meta_parts.append(f"topic: {topic}")
        embed.set_footer(text=" · ".join(meta_parts))

        await interaction.followup.send(embed=embed, ephemeral=False)

    async def _call_llm(self, prompt: str) -> str | discord.Embed:
        """
        Returns the summary string on success.
        Returns a discord.Embed (from customError) on LLM failure — caller must handle.
        """
        return await self.LLMinstance.askllm(prompt)


async def setup(bot: commands.Bot):
    await bot.add_cog(SummarizeCog(bot))