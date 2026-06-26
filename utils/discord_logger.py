import logging

import discord


class _NoiseFilter(logging.Filter):
    """Keep our app's WARNING+ logs, but only ERROR+ from discord.py's chatty internals."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name.startswith("discord.") and record.levelno < logging.ERROR:
            return False
        return True


class DiscordEmbedHandler(logging.Handler):
    """Posts log records to a Discord channel as embeds, without blocking the logger."""

    def __init__(self, bot, channel_id: int, level=logging.WARNING):
        super().__init__(level)
        self.bot = bot
        self.channel_id = channel_id
        self.addFilter(_NoiseFilter())

    def emit(self, record: logging.LogRecord):
        # logging is synchronous; hand the send off to the bot's event loop.
        try:
            loop = getattr(self.bot, "loop", None)
            if loop and loop.is_running():
                loop.create_task(self._send(record))
        except Exception:
            self.handleError(record)

    async def _send(self, record: logging.LogRecord):
        channel = self.bot.get_channel(self.channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(self.channel_id)
            except discord.HTTPException:
                return
        try:
            msg = self.format(record)
        except Exception:
            msg = record.getMessage()
        color = discord.Color.red() if record.levelno >= logging.ERROR else discord.Color.orange()
        embed = discord.Embed(
            title=f"{record.levelname} · {record.name}",
            description=f"```\n{msg[:3800]}\n```",
            color=color,
            timestamp=discord.utils.utcnow(),
        )
        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass


def setup_discord_logging(bot, channel_id: int, level=logging.WARNING):
    """Attach a Discord-channel log handler to the root logger. Returns the handler."""
    handler = DiscordEmbedHandler(bot, channel_id, level)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger().addHandler(handler)
    return handler
