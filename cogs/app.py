import discord
from discord import app_commands
from discord.ext import commands
from cogs.helpers import *
import asyncio
from cogs.hyperparams import *

class App(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="help", description="oh help this pour soul!")
    @app_commands.describe()
    async def help(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Help Menu", description="Pick a category below.")
        await interaction.followup.send(embed=embed, view=MenuView(HELP_CATEGORIES))

async def setup(bot):
    await bot.add_cog(App(bot))
