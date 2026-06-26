# Ted — server metrics bot (spec)

## Purpose
A standalone Discord bot that gathers activity metrics for the **Open Weights** server so the admins (Austin + Spen) can boost engagement and server efficiency. Persona — a dry, henpecked, mid-50s bird-watching dad — is **voice only**; the data underneath is rigorous.

## What it does
- **Logs** one row per message: `message_id, guild_id, channel_id, user_id, created_at`. **Never stores content.** Privacy-friendly, and needs **no privileged intents**.
- **Backfills** ~30 days of history per channel on first run, so metrics are available immediately (rate-limit aware; deduped by `message_id`).
- **`/ted`** (any channel, **public** so members enjoy it): that channel's pulse — messages last 7 days, distinct posters, % change vs prior 7 days, rank among channels — topped with a hand-written Ted remark.
- **2-day digest** in `#bot-commands`: every channel ranked alive → dead, biggest risers/fallers, total server messages, with an **AI-written** Ted summary that riffs on the real numbers.

## Voice
- `/ted`: rotating **hand-written** lines (free, instant, spam-safe), with sighs/asides. Examples:
  - `*sigh.* #general — 312 messages this week, up 18%. More conversation than I get at home. Moving on.`
  - `#research — 4 messages. Even the Tufted Titmouse is more active than this, and they're not known for ambition.`
  - `#memes — 88, up 22%. Good for them. *checks phone. Bob still hasn't texted about the hike.*`
- Digest: **Gemini-written** Ted commentary on the week's trends (only ~15 calls/month, so cost is trivial).

## Architecture
- Python + `discord.py` (matches Dexel's stack). Own Discord app/token.
- Postgres (Supabase). Tables: `message_events` (the log) + `ted_backfill` (which channels are done).
- `on_message` → insert metadata row (`ON CONFLICT (message_id) DO NOTHING`).
- Backfill task on ready: walk each text channel's `history(after=now-30d)`, batch-insert, mark done.
- Metrics module: SQL for per-channel counts, distinct users, % change, ranking.
- `/ted`: compute current channel's metrics → format with a random hand-written quip.
- Digest: `discord.ext.tasks` loop every 48h → all-channel report → Gemini commentary → post to `#bot-commands`.

## Hosting / deploy
- Runs on **Spen's EC2** (always-on, alongside Dexel). Spen adds Ted to Open Weights (View Channels + Read Message History + Send Messages + Embed Links) and deploys.
- Built + tested first on the **test server**.

## Config (.env)
`DISCORD_TOKEN` (Ted's own), `SUPABASE_DB`, `GEMINI_API_KEY` (Austin's, for the digest), `GUILD_ID`, `DIGEST_CHANNEL_ID` (#bot-commands).

## Out of scope (v1)
- Member-level "who's lurking" **public** stats (could single people out) — channel-focused for v1.
- Voice-channel activity.

## Testing
- Synthetic: insert fake `message_events` → verify metric queries (counts, % change, ranking).
- Live on test server: Ted logs real messages via `on_message`; `/ted` returns correct numbers; backfill picks up history; digest posts to the configured channel.
