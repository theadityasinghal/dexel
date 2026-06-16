import discord
from discord.ext import commands
from cogs.helpers import *


class Management(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def setlogchannel(self, ctx, channel: discord.TextChannel):
        print("set log triggered")
        # if ctx.author.guild_permissions.manage_guild:
        #     log_channels[ctx.guild.id] = channel.id
        #     await ctx.send(f"Log channel set to {channel.mention}")
        # else:
        #     await ctx.send(embed=permerror())

async def setup(bot):
    await bot.add_cog(Management(bot))
