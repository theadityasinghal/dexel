import discord
from discord import app_commands
from discord.ext import commands
from utils.helpers.helpers_new import *
import asyncio
from utils.hyperparams import *

class App(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.start_time = discord.utils.utcnow()

    @app_commands.command(name="about", description="About Dexel, the cute bot.")
    @app_commands.describe()
    async def embed(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(
        title=self.bot.user.name,
        description=("""A multi-purpose utility bot built to keep your server running itself. That's it to the bot, for now."""
        ),
        color=discord.Color.blurple(),
    )
        embed.add_field(name="Invite", value=f"[Add me to your server]({invite_url})", inline=True)
        embed.add_field(name="Support Server", value=f"[Join here]({guild_invite_link})", inline=True)
        embed.add_field(name="Owner", value=f"<@{ownerid}>", inline=True)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Built in the open, breaks in the open, fixed in the open.")
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Users", value=str(sum(g.member_count for g in self.bot.guilds)), inline=True)
        embed.add_field(name="Ping", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Uptime", value=str(discord.utils.utcnow() - self.bot.start_time).split(".")[0], inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ping", description="check how fast the bot is ⚡️")
    @app_commands.describe()
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="PONG!", description=f"The bot replied in {round(self.bot.latency * 1000)}ms!")
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(App(bot))
