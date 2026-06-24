import discord
from discord import app_commands
from discord.ext import commands
from utils.helpers.helpers_new import *
import asyncio
from utils.hyperparams import *
from typing import Optional
import re

def parse_duration(value: str) -> Optional[int]:
    """Convert duration string like 30s, 5m, 1h to seconds. Returns None if invalid."""
    match = re.fullmatch(r"(\d+)(s|m|h)", value.strip().lower())
    if not match:
        return None
    amount, unit = int(match.group(1)), match.group(2)
    return amount * {"s": 1, "m": 60, "h": 3600}[unit]

class Slowmode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.start_time = discord.utils.utcnow()

    @app_commands.command(name="slowmode", description="Set or view channel slowmode")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.describe(
        seconds="Slowmode delay (e.g. 30s, 5m, 1h)",
        channel="Target channel (defaults to current)",
        remove_after="Auto-remove slowmode after this duration (e.g. 10m, 1h)",
    )
    async def slowmode(
        self,
        interaction: discord.Interaction,
        seconds: Optional[str] = None,
        channel: Optional[discord.TextChannel] = None,
        remove_after: Optional[str] = None,
    ):
        await interaction.response.defer()
        target = channel or interaction.channel

        # --- View mode ---
        if seconds is None:
            delay = target.slowmode_delay
            msg = (
                f"{target.mention} has no slowmode."
                if delay == 0
                else f"{target.mention} slowmode is **{delay}s**."
            )
            await interaction.followup.send(msg)
            return

        # --- Parse seconds ---
        delay = parse_duration(seconds)
        if delay is None:
            await interaction.followup.send(
                "Invalid format. Use `30s`, `5m`, or `1h`.", ephemeral=True
            )
            return

        if not 0 <= delay <= 21600:
            await interaction.followup.send(
                "Must be between 0 and 21600 seconds (6 hours).", ephemeral=True
            )
            return

        # --- Parse remove_after ---
        remove_after_seconds = None
        if remove_after is not None:
            remove_after_seconds = parse_duration(remove_after)
            if remove_after_seconds is None:
                await interaction.followup.send(
                    "Invalid `remove_after` format. Use `30s`, `5m`, or `1h`.", ephemeral=True
                )
                return

        # --- Apply slowmode ---
        try:
            await target.edit(
                slowmode_delay=delay,
                reason=f"Slowmode set by {interaction.user} ({interaction.user.id})",
            )
        except discord.Forbidden:
            await interaction.followup.send(
                f"I don't have permission to manage {target.mention}.", ephemeral=True
            )
            return

        msg = (
            f"Slowmode set to **{seconds}** in {target.mention}."
            if delay > 0
            else f"Slowmode disabled in {target.mention}."
        )
        if remove_after_seconds:
            msg += f" Will be removed in **{remove_after}**."
        await interaction.followup.send(msg)

        # --- Auto-remove ---
        if remove_after_seconds:
            async def _remove():
                await asyncio.sleep(remove_after_seconds)
                try:
                    await target.edit(
                        slowmode_delay=0,
                        reason=f"Slowmode auto-removed (set by {interaction.user})",
                    )
                    await interaction.channel.send(
                        f"Slowmode in {target.mention} has been automatically removed."
                    )
                except discord.Forbidden:
                    pass

        asyncio.create_task(_remove())
async def setup(bot):
    await bot.add_cog(Slowmode(bot))
