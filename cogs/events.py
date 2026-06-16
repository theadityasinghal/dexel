import discord
from discord.ext import commands
from cogs.helpers import *

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

    # @commands.Cog.listener()
    # async def on_member_join(self, member):
    #     
async def setup(bot):
    await bot.add_cog(Events(bot))