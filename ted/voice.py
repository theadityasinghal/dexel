import os
import random

from google import genai

# Hand-written Ted asides for /ted (free, instant, spam-safe).
QUIPS = [
    "*sigh.*",
    "Anyway.",
    "Moving on, I suppose.",
    "*adjusts socks.*",
    "*checks phone. Bob still hasn't texted about the hike.*",
    "More conversation than I get at home, frankly.",
    "Even the Tufted Titmouse is busier than this, and they aren't known for ambition.",
    "Good for them. I suppose.",
    "*stares into the middle distance.*",
    "My wife says I care too much about this. She's probably right.",
    "I'd say more but I've got birds to go quietly disappoint.",
    "Riveting. *it is not riveting.*",
    "Dead as my houseplants in here.",
    "*sips lukewarm coffee.*",
]


def pulse_line(channel_name, msgs, posters, pct, rank, total) -> str:
    q1, q2 = random.sample(QUIPS, 2)
    people = "person" if posters == 1 else "people"
    head = f"**#{channel_name}** — {msgs} messages this week from {posters} {people}"
    if pct is not None:
        direction = "up" if pct > 0 else ("down" if pct < 0 else "flat")
        head += f", {direction} {abs(pct)}%"
    if rank:
        head += f". Rank {rank} of {total}."
    return f"{q1} {head} {q2}"


_client = None


def _genai():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


TED_PERSONA = (
    "You are Ted: a dry, henpecked, mildly self-sabotaging man in his mid-50s who logs Discord server "
    "activity for his bosses. You enjoy exactly two things: hiking with your friend Bob, and birdwatching. "
    "You quietly dread your wife's ire. Write a SHORT (3-5 sentence) weary, deadpan summary of the server "
    "activity numbers below. You may slip in at most one bird/Bob/wife aside. The numbers must stay accurate "
    "- you're sad about them, not making them up. Plain text, no markdown headers."
)


async def digest_commentary(report_text: str) -> str:
    try:
        r = await _genai().aio.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=TED_PERSONA + "\n\nNUMBERS:\n" + report_text,
            config=genai.types.GenerateContentConfig(max_output_tokens=400),
        )
        return (r.text or "").strip() or "*sigh.* The numbers are below."
    except Exception:
        return "*sigh.* The numbers are below. I'd summarize but my heart isn't in it today."
