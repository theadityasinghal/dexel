import discord
from discord import app_commands
from discord.ext import commands
from utils.helpers.helpers_new import *
import asyncio
from utils.hyperparams import *
from collections import deque

class LLM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.LLMinstance = LLMHelper()
        self.window = deque(maxlen=16)

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

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id != 1516854796651462869:
            return
        self.window.append(f"{message.author.display_name} ({message.author.id}): {message.content}")
        context = "\n".join(self.window)
        async with message.channel.typing():
            response = await self.LLMinstance.askllm(f"{system_prompt}\n\n{context}")
            if isinstance(response, discord.Embed):
                sent = await message.channel.send(embed=response, reference=message, allowed_mentions=discord.AllowedMentions.none())
                # use embed description/title as the text representation
                bot_text = response.description or response.title or "[embed response]"
            else:
                sent = await message.channel.send(response, reference=message, allowed_mentions=discord.AllowedMentions.none())
                bot_text = response
            self.window.append(f"{self.bot.user.display_name} ({self.bot.user.id}): {bot_text}")

async def setup(bot):
    await bot.add_cog(LLM(bot))
