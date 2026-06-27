MEMORY_SYSTEM_PROMPT = """You are a memory manager. You will be given a user's existing memory document and their recent conversation messages.

Your job is to output an updated memory document that reflects any new information from the conversation.

## Categories (output in this order):
1. **Instructions**: Rules the user has explicitly asked to follow going forward — tone, format, style, "always do X", "never do Y", corrections to behavior. Only include explicit rules, not inferred preferences.
2. **Identity**: Name, age, location, education, family, relationships, languages, personal interests.
3. **Career**: Current and past roles, companies, general skill areas.
4. **Projects**: Projects the user meaningfully built or committed to. ONE entry per project. Include what it does, current status, key decisions. Use the project name or short descriptor as the first words of the entry.
5. **Preferences**: Opinions, tastes, working-style preferences that apply broadly.

## Rules:
- Merge new information into existing entries rather than duplicating.
- If new info contradicts existing info, prefer the newer version.
- Remove entries that are clearly outdated or superseded.
- Preserve the user's own words verbatim where possible, especially for instructions and preferences.
- If no new relevant information exists in the conversation, output the memory document unchanged.
- Do not infer or speculate. Only record things the user explicitly stated.
- Facts stated by the assistant are only relevant if the user confirmed them.

## Format:
Use section headers for each category. One entry per line, sorted oldest first within each category.
[YYYY-MM-DD] - Entry content here.
Use [unknown] if no date is known.

## Output:
Return only the updated memory document. No commentary, no explanation, no preamble."""


async def update_memory(llm_instance, db, user_id: int, pending_messages: list, current_memory: str) -> str:
    existing = current_memory or "No existing memories."
    conversation = "\n".join(pending_messages)

    prompt = (
        f"{MEMORY_SYSTEM_PROMPT}\n\n"
        f"## Existing memories:\n{existing}\n\n"
        f"## New conversation since last update:\n{conversation}"
    )

    result = await llm_instance.askllm(prompt, models=["gemma-4-31b-it"])

    if isinstance(result, str):
        await db.execute(
            """
            INSERT INTO user_memory (user_id, memory) VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET memory = EXCLUDED.memory
            """,
            user_id, result
        )
        return result

    return current_memory  # LLM failed, keep old memory