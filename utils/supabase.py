import asyncpg


async def get_config(pool: asyncpg.Pool, guild_id: int):
    return await pool.fetchrow(
        "SELECT current_count, last_user_id, channel_id FROM counting WHERE guild_id = $1",
        guild_id,
    )


async def set_channel(pool: asyncpg.Pool, guild_id: int, channel_id: int):
    await pool.execute(
        """
        INSERT INTO counting (guild_id, channel_id, current_count, last_user_id)
        VALUES ($1, $2, 0, NULL)
        ON CONFLICT (guild_id)
        DO UPDATE SET channel_id = $2, current_count = 0, last_user_id = NULL
        """,
        guild_id,
        channel_id,
    )


async def reset_count(pool: asyncpg.Pool, guild_id: int):
    await pool.execute(
        "UPDATE counting SET current_count = 0, last_user_id = NULL WHERE guild_id = $1",
        guild_id,
    )


async def advance_count(pool: asyncpg.Pool, guild_id: int, user_id: int, new_count: int):
    await pool.execute(
        "UPDATE counting SET current_count = $2, last_user_id = $3 WHERE guild_id = $1",
        guild_id,
        new_count,
        user_id,
    )   