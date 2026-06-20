import discord
from discord import app_commands
from utils.premium import *

def format_perms(perms: list[str]) -> str:
    return ", ".join(p.replace("_", " ").title() for p in perms)

def setup_error_handler(bot):
    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            perms = format_perms(error.missing_permissions)
            msg = f"You need the **{perms}** permission(s) to use this command."
        elif isinstance(error, app_commands.BotMissingPermissions):
            perms = format_perms(error.missing_permissions)
            msg = f"I'm missing the **{perms}** permission(s) needed to run this command."
        elif isinstance(error, NotPremium):
            await interaction.response.send_message(str(error), ephemeral=True)
            return
        elif isinstance(error, app_commands.CommandOnCooldown):
            msg = f"Slow down — try again in {error.retry_after:.1f}s."
        elif isinstance(error, app_commands.CheckFailure):
            msg = "You can't use this command right now."
        else:
            raise error  # unexpected — let it surface in logs

        embed = discord.Embed(title="Error", description=msg)
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)