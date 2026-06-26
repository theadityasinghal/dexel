import discord
from discord import app_commands
from discord.ext import commands

from utils import memory as mem


class Memory(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="remember",
        description="Tell the bot something to remember about you (skill level, preferences, etc.).",
    )
    @app_commands.describe(note="e.g. 'I'm a beginner at ML' or 'keep answers short and simple'.")
    async def remember(self, interaction: discord.Interaction, note: str):
        await interaction.response.defer(ephemeral=True)
        profile = await mem.append_memory(self.bot.supabase_db, interaction.user.id, note)
        embed = discord.Embed(
            title="Got it — I'll remember that 🧠",
            description=profile,
            color=discord.Color.green(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="memory", description="See what the bot remembers about you.")
    async def memory(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        profile = await mem.get_memory(self.bot.supabase_db, interaction.user.id)
        if not profile:
            await interaction.followup.send(
                "I don't have anything saved about you yet. Use `/remember` to tell me something.",
                ephemeral=True,
            )
            return
        embed = discord.Embed(
            title="What I remember about you",
            description=profile,
            color=discord.Color.blurple(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="forget", description="Make the bot forget everything it remembers about you.")
    async def forget(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await mem.clear_memory(self.bot.supabase_db, interaction.user.id)
        await interaction.followup.send("Done — I've cleared everything I remembered about you.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Memory(bot))
