import discord
from discord import app_commands
from discord.ext import commands
from cogs.helpers import *
import asyncio
from cogs.hyperparams import *

class OW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="embed", description="Send an embed")
    @app_commands.describe(title="The embed title", description="The embed description")
    async def embed(self, interaction: discord.Interaction, title: str, description: str):
        embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(OW(bot))