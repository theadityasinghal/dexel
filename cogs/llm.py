import discord
from discord import app_commands
from discord.ext import commands
from cogs.helpers import *
import asyncio
from cogs.hyperparams import *

class LLM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.LLMinstance = LLMHelper(model="deepseek-ai/deepseek-v4-pro")

    @app_commands.command(name="chat", description="Chat with Dexel :D")
    @app_commands.describe(prompt="your prompt, could be anything, say 'who's the owner of this bot?")
    async def embed(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        response = await self.LLMinstance.askllm(prompt)
        if isinstance(response, discord.Embed):
            await interaction.followup.send(embed=response)
            return
        embed = discord.Embed(
            description=
            f"""{response}""",
            color=discord.Color.blurple()
        )
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LLM(bot))
