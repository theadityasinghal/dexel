import asyncio
import os
import discord
from discord.ext import commands
from utils.helpers.neon import *

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass


class Dexel(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True

        super().__init__(command_prefix="!", intents=intents)

        self.db = Database()

    async def setup_hook(self):
        for entry in os.scandir("./cogs"):
            if entry.is_file() and entry.name.endswith(".py") and entry.name != "__init__.py":
                await self.load_extension(f"cogs.{entry.name[:-3]}")
            elif entry.is_dir() and os.path.exists(f"{entry.path}/__init__.py"):
                await self.load_extension(f"cogs.{entry.name}")

        guild_id = os.getenv("GUILD_ID")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
        else:
            synced = await self.tree.sync()

        print(f"Synced {len(synced)} command(s)")

    async def on_ready(self):
        print(f"Bot is live: {self.user}")


async def main():
    async with Dexel() as bot:
        await bot.start(os.getenv("DISCORD_TOKEN"))


asyncio.run(main())