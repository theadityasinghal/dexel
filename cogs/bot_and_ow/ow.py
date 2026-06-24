import discord
from discord import app_commands
from discord.ext import commands
from utils.helpers.helpers_new import *
import asyncio
from utils.hyperparams import *

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
        if member.bot or member.guild.id != 1514609250222080072:
            return
        embed = discord.Embed(
            description=(
                "Hey! Thanks for joining — Dexel's a multi-purpose bot I'm building solo. "
                "It's got moderation, a counting game, AI chat with context history, and more being added regularly.\n\n"
                "If it's useful to you, it'd mean a lot if you invited it to your server or dropped by the support server.\n\n"
                "[Add Dexel to your server](https://discord.com/oauth2/authorize?client_id=1435304876266619061&permissions=3405200329403511&integration_type=0&scope=bot+applications.commands) "
                "· [Support server](https://discord.gg/VqY8qkHuWY)\n\n"
                "Either way, welcome 👋"
            ),
            color=discord.Color.blurple(),
        )

        try:
            await member.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.guild.id != openweights_id:
            return
        channel = self.bot.get_channel(openweights_log)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(openweights_log)
            except discord.NotFound:
                return

        embed = discord.Embed(
            description=f"📤 **{member}** left the server",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id} • Members: {member.guild.member_count}")

        await channel.send(embed=embed)
        

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        log_channel = self.bot.get_channel(guild_log_channel_id)
        owner = guild.owner
        owner_str = f"{owner} ({owner.id})" if owner else "Unknown"
        member_count = guild.member_count
        embed = discord.Embed(
            title="Bot Added!",
            color=discord.Color.green()
        )
        embed.add_field(name="Server Name", value=guild.name, inline=False)
        embed.add_field(name="Server ID", value=guild.id, inline=False)
        embed.add_field(name="Owner", value=f"{owner_str}", inline=False)
        embed.add_field(name="Members", value=member_count, inline=False)
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        log_channel = self.bot.get_channel(guild_log_channel_id)
        owner = guild.owner
        owner_str = f"{owner} ({owner.id})" if owner else "Unknown"
        member_count = guild.member_count
        embed = discord.Embed(
            title="Bot Removed!",
            color=discord.Color.red()
        )
        embed.add_field(name="Server Name", value=guild.name, inline=False)
        embed.add_field(name="Server ID", value=guild.id, inline=False)
        embed.add_field(name="Owner", value=f"{owner_str}", inline=False)
        embed.add_field(name="Members", value=member_count, inline=False)
        await log_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(OW(bot))