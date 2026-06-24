import asyncpg
import discord
from discord import app_commands
from discord.ext import commands
from utils.premium import is_premium
import time
from collections import defaultdict
from functools import wraps

class NotPremium(app_commands.CheckFailure):
    """Raised when a guild doesn't have an active premium subscription."""
    pass

def premium_check():
    async def predicate(interaction: discord.Interaction) -> bool:
        bot = interaction.client  # your Bot subclass, has .supabase_db
        if not await is_premium(pool=bot.supabase_db, guild_id=interaction.guild_id):
            raise NotPremium("This server needs **premium** to use this command.")
        return True
    return app_commands.check(predicate)

def unique(timelimit):
    if timelimit is None:
        timelimit = 60
    cache: dict[tuple, float] = {}

    def decorator(func):
        @wraps(func)
        async def wrapper(self, message: discord.Message, *args, **kwargs):
            if message.author.bot or not message.guild:
                return

            key = (message.guild.id, message.author.id)
            now = time.monotonic()

            if now - cache.get(key, 0) < timelimit:
                return  # same user-guild pair seen within last 60s

            cache[key] = now
            return await func(self, message, *args, **kwargs)
        return wrapper
    return decorator