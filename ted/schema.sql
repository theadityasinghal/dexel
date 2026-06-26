-- Ted's metrics store. Message metadata only — never content.

CREATE TABLE IF NOT EXISTS message_events (
    message_id  BIGINT PRIMARY KEY,         -- Discord snowflake; natural dedup for backfill + live
    guild_id    BIGINT NOT NULL,
    channel_id  BIGINT NOT NULL,
    user_id     BIGINT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_msgevents_channel_time ON message_events (channel_id, created_at);
CREATE INDEX IF NOT EXISTS idx_msgevents_guild_time   ON message_events (guild_id, created_at);

-- Tracks which channels have had their 30-day history backfilled, so we don't redo it.
CREATE TABLE IF NOT EXISTS ted_backfill (
    channel_id    BIGINT PRIMARY KEY,
    backfilled_at TIMESTAMPTZ NOT NULL
);
