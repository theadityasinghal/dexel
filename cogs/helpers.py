from google import genai
import discord
from discord.ext import commands
import os
import asyncio
from cogs.hyperparams import *
from openai import OpenAI
import httpx

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

class LLMHelper():
    def __init__(self, base_url=nvidia_base_url,
                 model="meta/llama-3.2-1b-instruct", 
                 api_key = os.getenv("NVIDIA_API_KEY")):
        self.client = OpenAI(
            base_url = base_url,
            api_key = api_key
        )
        self.model = model

    async def _ask(self, final_prompt, max_tokens=1024, 
                   temperature=0.2, top_p=0.7, stream = False):

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": final_prompt}],
            temperature=temperature, top_p=top_p, max_tokens=max_tokens, stream=False,
            extra_body={"chat_template_kwargs": {"thinking": False}})
        return completion.choices[0].message.content
    
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
