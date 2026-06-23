from google import genai
import discord
from discord.ext import commands
import os
import asyncio
from utils.hyperparams import *
import mimetypes
import random

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

class GeneralHelper():
    def __init__(self):
        pass

    async def _attachment_to_part(self, attachment: discord.Attachment) -> tuple[bytes, str]:
        img_bytes = await attachment.read()
        mime_type = attachment.content_type or mimetypes.guess_type(attachment.filename)[0] or "image/png"
        return img_bytes, mime_type

class LLMHelper():
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("MR_GPU_BOI_API_FOR_GOOGLE"))
        self.general = GeneralHelper()

    async def _ask(self, final_prompt, models=None, max_output_tokens=1500, images=None):
        """
        images: optional, one of:
        - (bytes, mime_type) tuple, e.g. (img_bytes, "image/png")
        - list of such tuples, for multi-image input
        """
        contents = []
        if models is None:
            models = ["gemini-3.5-flash"]
            #models = ["gemma-4-31b-it", "gemma-4-26b-a4b-it"]
        model = random.choices(models, weights=[1] * len(models), k=1)[0]
        if images:
            if isinstance(images, tuple):
                images = [images]
            for img_bytes, mime_type in images:
                contents.append(genai.types.Part.from_bytes(data=img_bytes, mime_type=mime_type))

        contents.append(final_prompt)  # text after image(s)

        response = await self.client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=genai.types.GenerateContentConfig(
                max_output_tokens=max_output_tokens,
            )
        )

        parts = response.candidates[0].content.parts
        actual_text = next(p.text for p in parts if not p.thought)
        return actual_text
    
    async def askllm(self, user_raw_prompt, attempts=5, wait_time = 2, images_raw = None):
        final_prompt = system_prompt + user_raw_prompt
        for attempt in range(attempts):
            try:
                if images_raw:
                    img_part = await self.general._attachment_to_part(images_raw[0])
                    response = await self._ask(final_prompt, images=img_part)
                else:
                    response = await self._ask(final_prompt)
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

