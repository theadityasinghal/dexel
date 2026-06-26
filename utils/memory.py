import asyncpg

# Per-user memory: a small free-text profile the user controls, used to tailor AI replies.

async def get_memory(pool: asyncpg.Pool, user_id: int) -> str | None:
    row = await pool.fetchrow("SELECT profile FROM user_memory WHERE user_id = $1", user_id)
    return row["profile"] if row and row["profile"] else None


async def set_memory(pool: asyncpg.Pool, user_id: int, profile: str):
    await pool.execute(
        """
        INSERT INTO user_memory (user_id, profile, updated_at)
        VALUES ($1, $2, now())
        ON CONFLICT (user_id) DO UPDATE SET profile = $2, updated_at = now()
        """,
        user_id,
        profile,
    )


async def append_memory(pool: asyncpg.Pool, user_id: int, note: str) -> str:
    existing = await get_memory(pool, user_id)
    combined = f"{existing}\n{note}".strip() if existing else note.strip()
    combined = combined[-2000:]  # keep it bounded
    await set_memory(pool, user_id, combined)
    return combined


async def clear_memory(pool: asyncpg.Pool, user_id: int):
    await pool.execute("DELETE FROM user_memory WHERE user_id = $1", user_id)
