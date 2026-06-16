import discord
from discord import app_commands
from discord.ext import commands
from cogs.helpers import *
import asyncio
from cogs.hyperparams import *

class OW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.secret = Secrecy()

    @app_commands.command(name="embed", description="Send an embed")
    @app_commands.describe(title="The embed title", description="The embed description")
    async def embed(self, interaction: discord.Interaction, title: str, description: str):
        if self.secret.usercheck(interaction.user):
            embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
            await interaction.response.send_message(embed=embed)
            
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if self.secret.guildcheck(member.guild):
            try:
                await member.send(f"Welcome to {member.guild.name}! Check out #rules to get started.")
            except discord.Forbidden:
                # user has DMs disabled or blocked the bot — log and move on
                pass

async def setup(bot):
    await bot.add_cog(OW(bot))