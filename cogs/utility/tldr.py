import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Union
from datetime import datetime, timezone

from utils.helpers.helpers_new import LLMHelper

CHAT_LIMIT = 30      # messages read in a normal chat / thread
FORUM_LIMIT = 10     # recent posts summarized in a forum
_MIN_DT = datetime(2015, 1, 1, tzinfo=timezone.utc)  # fallback sort key


class Tldr(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.llm = LLMHelper()

    @app_commands.command(
        name="tldr",
        description="Summarize a channel — recent chat, or the recent posts in a forum.",
    )
    @app_commands.describe(
        channel="Channel to summarize (defaults to where you run this). Point at a forum to recap its posts."
    )
    @app_commands.checks.cooldown(1, 60.0, key=lambda i: i.user.id)
    async def tldr(
        self,
        interaction: discord.Interaction,
        channel: Optional[Union[discord.TextChannel, discord.ForumChannel]] = None,
    ):
        await interaction.response.defer()  # public: everyone in the channel sees the recap
        target = channel or interaction.channel

        if isinstance(target, discord.ForumChannel):
            await self._summarize_forum(interaction, target)
        elif isinstance(target, (discord.TextChannel, discord.Thread, discord.VoiceChannel)):
            await self._summarize_messages(interaction, target)
        else:
            await interaction.followup.send("I can only summarize text channels, threads, or forums.")

    async def _summarize_messages(self, interaction: discord.Interaction, channel):
        try:
            raw = [m async for m in channel.history(limit=CHAT_LIMIT)]
        except discord.Forbidden:
            await interaction.followup.send(
                f"I don't have permission to read history in {channel.mention}."
            )
            return

        msgs = [m for m in reversed(raw) if m.content and not m.author.bot]  # oldest->newest, drop bots/empty
        if len(msgs) < 2:
            await interaction.followup.send(
                f"There isn't enough recent conversation in {channel.mention} to summarize."
            )
            return

        text = "\n".join(f"{m.author.display_name}: {m.content}" for m in msgs)
        summary = await self.llm.summarize(text, kind="chat")
        await self._send_summary(interaction, channel, summary, footer=f"last {len(msgs)} messages")

    async def _summarize_forum(self, interaction: discord.Interaction, forum: discord.ForumChannel):
        posts = list(forum.threads)  # active posts
        try:
            async for t in forum.archived_threads(limit=FORUM_LIMIT):
                posts.append(t)
        except (discord.Forbidden, discord.HTTPException):
            pass

        posts = sorted(posts, key=lambda t: t.created_at or _MIN_DT, reverse=True)[:FORUM_LIMIT]
        if not posts:
            await interaction.followup.send(f"**{forum.name}** has no posts to summarize yet.")
            return

        blocks = []
        for t in posts:
            msg = t.starter_message
            if msg is None:
                try:
                    async for m in t.history(limit=1, oldest_first=True):
                        msg = m
                        break
                except (discord.Forbidden, discord.HTTPException):
                    msg = None
            opening = (msg.content[:500] if msg and msg.content else "(no text)")
            blocks.append(f"POST: {t.name}\nOPENING: {opening}")

        text = "\n\n".join(blocks)
        summary = await self.llm.summarize(text, kind="forum")
        await self._send_summary(interaction, forum, summary, footer=f"{len(posts)} recent posts")

    async def _send_summary(self, interaction: discord.Interaction, target, summary, footer: str):
        if isinstance(summary, discord.Embed):  # helper returns an error embed on LLM failure
            await interaction.followup.send(embed=summary)
            return
        embed = discord.Embed(
            title=f"TL;DR — {getattr(target, 'name', 'this channel')}",
            description=str(summary)[:4096],
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"Summary of {footer} • requested by {interaction.user.display_name}")
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tldr(bot))
