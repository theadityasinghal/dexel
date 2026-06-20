import ast
import operator

import discord
from discord import app_commands
from discord.ext import commands

from utils import supabase as counting_db

# Restricted arithmetic - only +, -, *, /, unary +/-. No names, no calls, no power.
ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def safe_eval(expr: str):
    """Evaluate a restricted arithmetic expression. Raises ValueError/SyntaxError if invalid."""
    node = ast.parse(expr, mode="eval").body
    return _eval_node(node)


def _eval_node(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise ValueError("non-numeric constant")
    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPS:
        return ALLOWED_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_OPS:
        return ALLOWED_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("disallowed expression")


class Counting(commands.GroupCog, name="counting", description="Configure the counting game"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Set the counting channel for this server")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer()
        await counting_db.set_channel(self.bot.supabase_db, interaction.guild_id, channel.id)
        await interaction.followup.send(
            f"Counting channel set to {channel.mention}. Next number is **1**."
        )

    @app_commands.command(name="reset", description="Reset the count back to 0")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def reset(self, interaction: discord.Interaction):
        await interaction.response.defer()
        config = await counting_db.get_config(self.bot.supabase_db, interaction.guild_id)
        if not config or config["channel_id"] is None:
            await interaction.followup.send(
                "Counting isn't set up yet. Use `/counting setup` first."
            )
            return
        await counting_db.reset_count(self.bot.supabase_db, interaction.guild_id)
        await interaction.followup.send("Count reset to **0**.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        config = await counting_db.get_config(self.bot.supabase_db, message.guild.id)
        if not config or config["channel_id"] != message.channel.id:
            return

        # Not a number/expression -> ignore, don't touch the count.
        try:
            result = safe_eval(message.content.strip())
        except (ValueError, SyntaxError, ZeroDivisionError, TypeError):
            return

        expected = config["current_count"] + 1

        if result == expected:
            await counting_db.advance_count(
                self.bot.supabase_db, message.guild.id, message.author.id, expected
            )
            await message.add_reaction("✅")
        else:
            await counting_db.reset_count(self.bot.supabase_db, message.guild.id)
            await message.add_reaction("❌")
            await message.reply(
                f"Wrong number! Expected **{expected}**, got **{result:g}**. Count reset to **0**.",
                mention_author=False,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Counting(bot))