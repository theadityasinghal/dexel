from google import genai
import discord
from discord.ext import commands
import os
import asyncio
from utils.hyperparams import *

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

class LLMHelper():
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GOOGLE_LLM_API"))

    async def _ask(self, final_prompt, model="gemma-4-31b-it", max_output_tokens=1500):
        response = await self.client.aio.models.generate_content(
            model=model,
            contents=final_prompt,
            config=genai.types.GenerateContentConfig(
                max_output_tokens=max_output_tokens,
            )
        )
        # print(response)
        # instead of response.text
        parts = response.candidates[0].content.parts
        actual_text = next(p.text for p in parts if not p.thought)
        # print(actual_text)
        return actual_text
    
    async def askllm(self, user_raw_prompt, attempts=5, wait_time = 2):
        final_prompt = system_prompt + user_raw_prompt
        for attempt in range(attempts):
            try:
                response = await self._ask(final_prompt=final_prompt)
                if not response:
                    raise RuntimeError("Got an empty message")
                return response
            except Exception as e:
                #print(f"Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(wait_time)
        return customError("LLMfailure")

def customError(permission, arguments = None) -> discord.Embed:
    categories = {
        "missingUserPerm": ["Missing User Permission","The user doesn't have the permission(s) to use this command"],
        "LLMfailure": ["Low IQ LLM", "The bot's LLM is stupid and basically died :/"]
    }
    # permission = ["which_category","arguments"]
    category = categories[permission]
    embed = discord.Embed(
        title=category[0],
        description=category[1],
        color=discord.Color.red()
    )
    return embed

class ErrorHandler():
    def __init__(self):
        pass

    def error(self, errorType, user, guild, channel, message, timestamp):
        embed = discord.Embed(
            title=f"Error: {errorType}",
            description=f"""User: {user.id}
                            Guild: {guild.name} {guild.id}
                            Channel: {channel.mention} {channel.id}
                            User Message: {message}
                            timestamp: {timestamp}""",
            color=discord.Color.red()
        )
        return embed

class Secrecy():
    def __init__(self):
        self.ownerid = ownerid
        self.mainguildid = mainguildid

    def usercheck(self, member: discord.Member):
        return member.id == self.ownerid
    def guildcheck(self, guild: discord.Guild):
        return guild.id == self.mainguildid


class MenuSelect(discord.ui.Select):
    def __init__(self, pages: dict, placeholder="Choose an option..."):
        self.pages = pages
        options = [discord.SelectOption(label=label, value=key) for key, (label, _) in pages.items()]
        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, interaction: discord.Interaction):
        label, desc = self.pages[self.values[0]]
        embed = discord.Embed(title=label, description=desc, color=discord.Color.blurple())
        await interaction.response.edit_message(embed=embed, view=self.view)

class MenuView(discord.ui.View):
    def __init__(self, pages: dict, author_id: int, timeout=120):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.add_item(MenuSelect(pages))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Not your menu.", ephemeral=True)
            return False
        return True
