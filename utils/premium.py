import asyncpg
import discord
from discord import app_commands
from discord.ext import commands


async def is_premium(pool: asyncpg.Pool, guild_id: int) -> bool:
    row = await pool.fetchrow(
        "SELECT premium FROM paid WHERE guild_id = $1",
        guild_id,
    )
    return bool(row["premium"]) if row else False

async def add_premium(pool: asyncpg.Pool, guild_id: int):
    await pool.execute(
        """
        INSERT INTO paid (guild_id, premium)
        VALUES ($1, TRUE)
        ON CONFLICT (guild_id)
        DO UPDATE SET premium = TRUE
        """,
        guild_id,
    )

async def remove_premium(pool: asyncpg.Pool, guild_id: int):
    await pool.execute(
        """
        INSERT INTO paid (guild_id, premium)
        VALUES ($1, FALSE)
        ON CONFLICT (guild_id)
        DO UPDATE SET premium = FALSE
        """,
        guild_id,
    )
