import aiohttp
import discord
from discord import app_commands
from discord.ext import commands


class LeetCodeAgent(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.webhook_url = "http://localhost:5678/webhook/dexel-agent"
        self.timeout = aiohttp.ClientTimeout(total=30)

    @app_commands.command(name="leetcode", description="Get LeetCode stats for a user")
    @app_commands.describe(userid="The LeetCode username to look up")
    async def leetcode(self, interaction: discord.Interaction, userid: str):
        await interaction.response.defer()

        prompt = f"gimme stats of {userid}"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    self.webhook_url,
                    json={
                        "message": prompt,
                        "sessionId": str(interaction.channel_id),
                    },
                ) as resp:
                    if resp.status != 200:
                        await interaction.followup.send(
                            f"Workflow returned status {resp.status}. Try again in a bit."
                        )
                        return
                    data = await resp.json()
        except aiohttp.ClientConnectorError:
            await interaction.followup.send(
                "Couldn't reach the n8n workflow — is it running locally?"
            )
            return
        except Exception as e:
            await interaction.followup.send(f"Something broke: `{e}`")
            return

        output = data.get("output", "No response from agent.")
        await interaction.followup.send(output)


async def setup(bot: commands.Bot):
    await bot.add_cog(LeetCodeAgent(bot))