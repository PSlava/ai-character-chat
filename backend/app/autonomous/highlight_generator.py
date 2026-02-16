"""Generate editorial highlights for characters — short catchy phrases, NOT fake reviews."""

import json
import logging

from sqlalchemy import text

from app.db.session import engine as db_engine
from app.llm.base import LLMMessage, LLMConfig
from app.llm.registry import get_provider
from app.autonomous.providers import get_autonomous_provider_order

logger = logging.getLogger("autonomous")
_TIMEOUT = 20.0
_BATCH_SIZE = 10  # characters per run

_PROMPT = """Generate 2 short editorial highlight phrases for this AI character.
These are descriptive/editorial phrases (NOT user reviews, NOT testimonials).

Character info:
- Name: {name}
- Tagline: {tagline}
- Tags: {tags}
- Personality (first 200 chars): {personality}
- Content rating: {rating}

Generate exactly 10 phrases: 2 in Russian, 2 in English, 2 in Spanish, 2 in French, 2 in German.
Each phrase should be catchy, under 80 characters, and describe what makes this character unique or appealing.

Examples of good phrases:
- "Dark romance with an unpredictable twist"
- "Идеальный микс цундере и воительницы"
- "Perfecto para fans del romance prohibido"
- "Romance sombre avec une touche imprévisible"
- "Dunkle Romantik mit unberechenbarer Wendung"

Return ONLY a JSON array:
[
  {{"text": "phrase in Russian", "lang": "ru"}},
  {{"text": "another phrase in Russian", "lang": "ru"}},
  {{"text": "phrase in English", "lang": "en"}},
  {{"text": "another phrase in English", "lang": "en"}},
  {{"text": "phrase in Spanish", "lang": "es"}},
  {{"text": "another phrase in Spanish", "lang": "es"}},
  {{"text": "phrase in French", "lang": "fr"}},
  {{"text": "another phrase in French", "lang": "fr"}},
  {{"text": "phrase in German", "lang": "de"}},
  {{"text": "another phrase in German", "lang": "de"}}
]"""


async def generate_highlights() -> int:
    """Generate highlights for characters that don't have them yet. Returns count."""
    # Find characters without highlights
    async with db_engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT id, name, tagline, tags, personality, content_rating
            FROM characters
            WHERE is_public = true
              AND (highlights IS NULL OR highlights = '[]'::jsonb)
            ORDER BY chat_count DESC
            LIMIT :limit
        """), {"limit": _BATCH_SIZE})
        characters = result.fetchall()

    if not characters:
        logger.info("No characters need highlights")
        return 0

    count = 0
    for char in characters:
        try:
            highlights = await _generate_for_character(
                char.name, char.tagline or "", char.tags or "",
                char.personality or "", char.content_rating or "sfw"
            )
            if highlights:
                async with db_engine.begin() as conn:
                    await conn.execute(text("""
                        UPDATE characters SET highlights = CAST(:h AS jsonb)
                        WHERE id = :id
                    """), {"h": json.dumps(highlights, ensure_ascii=False), "id": char.id})
                count += 1
                logger.info("Generated highlights for %s", char.name)
        except Exception:
            logger.exception("Failed to generate highlights for %s", char.name)

    return count


async def _generate_for_character(
    name: str, tagline: str, tags: str, personality: str, rating: str
) -> list[dict] | None:
    """Generate highlights using LLM with provider fallback."""
    prompt = _PROMPT.format(
        name=name, tagline=tagline, tags=tags,
        personality=personality[:200], rating=rating
    )
    messages = [LLMMessage(role="user", content=prompt)]
    config = LLMConfig(model="", temperature=0.8, max_tokens=512)

    for provider_name in get_autonomous_provider_order():
        try:
            provider = get_provider(provider_name)
        except ValueError:
            continue

        try:
            raw = await provider.generate(messages, config)
            text_content = raw.strip()
            # Strip markdown fences
            if text_content.startswith("```"):
                text_content = text_content.split("\n", 1)[1] if "\n" in text_content else text_content[3:]
                if text_content.endswith("```"):
                    text_content = text_content[:-3].strip()

            data = json.loads(text_content)
            if isinstance(data, list) and len(data) >= 2:
                # Validate structure
                valid = [
                    {"text": item["text"][:100], "lang": item["lang"]}
                    for item in data
                    if isinstance(item, dict) and "text" in item and "lang" in item
                    and item["lang"] in ("ru", "en", "es", "fr", "de")
                ]
                if valid:
                    return valid
        except Exception as e:
            logger.warning("Highlight generation failed with %s: %s", provider_name, str(e)[:100])
            continue

    return None
