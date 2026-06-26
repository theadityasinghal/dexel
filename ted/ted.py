import os
import asyncio
import datetime

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()
import db
import voice

GUILD_ID = int(os.getenv("GUILD_ID") or 0)
DIGEST_CHANNEL_ID = int(os.getenv("DIGEST_CHANNEL_ID") or 0)
BACKFILL_DAYS = 30

intents = discord.Intents.default()  # no privileged intents — Ted never reads content
bot = commands.Bot(command_prefix="ted!", intents=intents)


def pct_change(now, prev):
    return None if prev == 0 else round((now - prev) / prev * 100)


@bot.event
async def setup_hook():
    await db.init(os.getenv("SUPABASE_DB"))
    if GUILD_ID:
        g = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=g)
        await bot.tree.sync(guild=g)
    else:
        await bot.tree.sync()


@bot.event
async def on_ready():
    print(f"Ted is on the clock as {bot.user}. He'd rather be birdwatching.")
    if not digest_loop.is_running():
        digest_loop.start()
    asyncio.create_task(backfill_all())


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return
    await db.log_message(message.id, message.guild.id, message.channel.id, message.author.id, message.created_at)


async def backfill_all():
    after = discord.utils.utcnow() - datetime.timedelta(days=BACKFILL_DAYS)
    for guild in bot.guilds:
        for ch in guild.text_channels:
            if not ch.permissions_for(guild.me).read_message_history:
                continue
            if await db.is_backfilled(ch.id):
                continue
            rows = []
            try:
                async for m in ch.history(limit=None, after=after, oldest_first=True):
                    if m.author.bot:
                        continue
                    rows.append((m.id, guild.id, ch.id, m.author.id, m.created_at))
                    if len(rows) >= 500:
                        await db.log_many(rows)
                        rows = []
                if rows:
                    await db.log_many(rows)
                await db.mark_backfilled(ch.id)
                print(f"Ted backfilled #{ch.name}")
            except discord.Forbidden:
                continue
            except Exception as e:
                print(f"backfill error #{ch.name}: {e!r}")


@bot.tree.command(name="ted", description="Ted reports this channel's recent activity. He'd rather be birdwatching.")
async def ted(interaction: discord.Interaction):
    await interaction.response.defer()  # public, so the members can enjoy his suffering
    p = await db.channel_pulse(interaction.guild_id, interaction.channel_id)
    pct = pct_change(p["msgs"], p["prev"])
    line = voice.pulse_line(interaction.channel.name, p["msgs"], p["posters"], pct, p["rank"], p["total_channels"])
    await interaction.followup.send(line)


@tasks.loop(hours=48)
async def digest_loop():
    if not DIGEST_CHANNEL_ID:
        return
    channel = bot.get_channel(DIGEST_CHANNEL_ID)
    if channel is None:
        return
    for guild in bot.guilds:
        report = await db.all_channels_report(guild.id)
        if not report:
            continue
        lines, total = [], 0
        for r in report:
            ch = bot.get_channel(r["channel_id"])
            name = f"#{ch.name}" if ch else f"channel {r['channel_id']}"
            pct = pct_change(r["msgs"], r["prev"])
            arrow = "" if pct is None else f" ({'+' if pct >= 0 else ''}{pct}%)"
            lines.append(f"{name}: {r['msgs']} msgs / {r['posters']} ppl{arrow}")
            total += r["msgs"]
        report_text = f"Server total (last 7 days): {total} messages across {len(report)} active channels.\n" + "\n".join(lines)
        commentary = await voice.digest_commentary(report_text)
        embed = discord.Embed(
            title="Ted's Activity Report — last 7 days",
            description=commentary,
            color=discord.Color.dark_teal(),
        )
        embed.add_field(name="By channel", value=("\n".join(lines)[:1000] or "Nothing. *sigh.*"), inline=False)
        embed.set_footer(text="Ted • would rather be birdwatching")
        await channel.send(embed=embed)


@digest_loop.before_loop
async def _before_digest():
    await bot.wait_until_ready()


if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"), log_handler=None)
