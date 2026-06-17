import asyncio
import os
import discord
from discord.ext import commands

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

async def main():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True

    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        print(f"Bot is live: {bot.user}")

        guild_id = os.getenv("GUILD_ID")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
        else:
            synced = await bot.tree.sync()

        print(f"Synced {len(synced)} command(s)")

    # Auto-load all cogs
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename not in ("__init__.py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

    await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())