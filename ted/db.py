import asyncpg

_pool: asyncpg.Pool | None = None


async def init(dsn: str):
    global _pool
    _pool = await asyncpg.create_pool(dsn, ssl="require")
    await ensure_schema()
    return _pool


async def ensure_schema():
    async with _pool.acquire() as con:
        await con.execute(
            """
            CREATE TABLE IF NOT EXISTS message_events (
                message_id BIGINT PRIMARY KEY,
                guild_id   BIGINT NOT NULL,
                channel_id BIGINT NOT NULL,
                user_id    BIGINT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            );
            """
        )
        await con.execute("CREATE INDEX IF NOT EXISTS idx_msgevents_channel_time ON message_events (channel_id, created_at);")
        await con.execute("CREATE INDEX IF NOT EXISTS idx_msgevents_guild_time ON message_events (guild_id, created_at);")
        await con.execute(
            "CREATE TABLE IF NOT EXISTS ted_backfill (channel_id BIGINT PRIMARY KEY, backfilled_at TIMESTAMPTZ NOT NULL);"
        )


async def log_message(message_id, guild_id, channel_id, user_id, created_at):
    await _pool.execute(
        "INSERT INTO message_events (message_id, guild_id, channel_id, user_id, created_at) "
        "VALUES ($1,$2,$3,$4,$5) ON CONFLICT (message_id) DO NOTHING",
        message_id, guild_id, channel_id, user_id, created_at,
    )


async def log_many(rows):
    # rows: list of (message_id, guild_id, channel_id, user_id, created_at)
    await _pool.executemany(
        "INSERT INTO message_events (message_id, guild_id, channel_id, user_id, created_at) "
        "VALUES ($1,$2,$3,$4,$5) ON CONFLICT (message_id) DO NOTHING",
        rows,
    )


async def is_backfilled(channel_id) -> bool:
    return await _pool.fetchval("SELECT 1 FROM ted_backfill WHERE channel_id = $1", channel_id) is not None


async def mark_backfilled(channel_id):
    await _pool.execute(
        "INSERT INTO ted_backfill (channel_id, backfilled_at) VALUES ($1, now()) "
        "ON CONFLICT (channel_id) DO UPDATE SET backfilled_at = now()",
        channel_id,
    )


async def channel_pulse(guild_id, channel_id) -> dict:
    cur = await _pool.fetchrow(
        "SELECT count(*) AS msgs, count(DISTINCT user_id) AS posters FROM message_events "
        "WHERE channel_id = $1 AND created_at >= now() - interval '7 days'",
        channel_id,
    )
    prev = await _pool.fetchval(
        "SELECT count(*) FROM message_events WHERE channel_id = $1 "
        "AND created_at >= now() - interval '14 days' AND created_at < now() - interval '7 days'",
        channel_id,
    )
    ranks = await _pool.fetch(
        "SELECT channel_id, count(*) AS msgs FROM message_events "
        "WHERE guild_id = $1 AND created_at >= now() - interval '7 days' "
        "GROUP BY channel_id ORDER BY msgs DESC",
        guild_id,
    )
    rank = next((i for i, r in enumerate(ranks, 1) if r["channel_id"] == channel_id), None)
    return {"msgs": cur["msgs"], "posters": cur["posters"], "prev": prev or 0,
            "rank": rank, "total_channels": len(ranks)}


async def all_channels_report(guild_id) -> list[dict]:
    rows = await _pool.fetch(
        """
        WITH last7 AS (
          SELECT channel_id, count(*) AS msgs, count(DISTINCT user_id) AS posters
          FROM message_events WHERE guild_id = $1 AND created_at >= now() - interval '7 days'
          GROUP BY channel_id
        ),
        prev7 AS (
          SELECT channel_id, count(*) AS msgs FROM message_events
          WHERE guild_id = $1 AND created_at >= now() - interval '14 days' AND created_at < now() - interval '7 days'
          GROUP BY channel_id
        )
        SELECT l.channel_id, l.msgs, l.posters, coalesce(p.msgs,0) AS prev
        FROM last7 l LEFT JOIN prev7 p ON l.channel_id = p.channel_id
        ORDER BY l.msgs DESC
        """,
        guild_id,
    )
    return [dict(r) for r in rows]
