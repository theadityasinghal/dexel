import asyncio
import os

import asyncpg
import discord
from discord.ext import commands
from utils.neon import *
from utils.errors import setup_error_handler
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Dexel(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True

        super().__init__(command_prefix="!", intents=intents)

        self.db = Database()  # Neon 
        self.supabase_db = None  # asyncpg pool, set up in setup_hook

    async def setup_hook(self):
        setup_error_handler(self)
        self.supabase_db = await asyncpg.create_pool(
            os.getenv("SUPABASE_DB_NEW"),
            ssl="require",
            statement_cache_size=0,  # required for pooler
        )

        for entry in os.walk("./cogs"): 
            dirpath, _, filenames = entry
            for filename in filenames:
                if filename.endswith(".py") and filename != "__init__.py":
                    rel_path = os.path.relpath(os.path.join(dirpath, filename), ".")
                    module = rel_path[:-3].replace(os.sep, ".")
                    try:
                        await self.load_extension(module)
                    except Exception as e:
                        print(f"Failed to load {module}: {e}")

        guild_id = os.getenv("GUILD_ID")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
        else:
            synced = await self.tree.sync()

        print(f"Synced {len(synced)} command(s)")

    async def close(self):
        if self.supabase_db:
            await self.supabase_db.close()
        await super().close()

    async def on_ready(self):
        print(f"Bot is live: {self.user}")


async def main():
    discord.utils.setup_logging()
    async with Dexel() as bot:
        await bot.start(os.getenv("DISCORD_TOKEN"))


asyncio.run(main())