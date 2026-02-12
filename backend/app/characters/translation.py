"""Batch translation of character card fields (name, tagline, tags) via LLM."""

import asyncio
import json
import logging

from sqlalchemy import text

from app.db.session import engine as db_engine
from app.llm.base import LLMMessage, LLMConfig
from app.llm.registry import get_provider

logger = logging.getLogger(__name__)

TRANSLATE_SYSTEM_PROMPT = """You are a translation engine for a character chat application.

INPUT: A JSON array of objects, each with:
- "id": character identifier (return as-is)
- "name": character name
- "tagline": short character description (may be null)
- "tags": array of tag strings

TARGET LANGUAGE: {target_lang}

TRANSLATION RULES:

For "name":
- Personal/proper names: TRANSLITERATE (keep the name, change script)
  Examples: Алина → Alina, Кира → Kira, Дмитрий → Dmitry
- Descriptive/title names: TRANSLATE the meaning
  Examples: Тёмный Лорд → Dark Lord, Хранитель Леса → Forest Keeper
- Mixed (name + epithet): transliterate the name, translate the epithet
  Examples: Князь Владимир → Prince Vladimir

For "tagline": Translate naturally. Keep the same tone and brevity.

For "tags": Translate each tag to its natural equivalent.
  Examples: фэнтези → fantasy, романтика → romance, злодей → villain

OUTPUT: Return ONLY a JSON array with the same structure. No markdown, no explanation."""

_PROVIDER_ORDER = ("groq", "cerebras", "openrouter")
_TIMEOUT = 8.0  # seconds


async def translate_batch(
    characters: list[dict],
    target_language: str,
) -> dict[str, dict]:
    """Translate a batch of character card fields via LLM.

    Returns {character_id: {"name": ..., "tagline": ..., "tags": [...]}}.
    Returns {} on any failure.
    """
    if not characters:
        return {}

    lang_names = {"en": "English", "ru": "Russian", "es": "Spanish", "fr": "French",
                  "de": "German", "ja": "Japanese", "zh": "Chinese", "ko": "Korean"}
    lang_name = lang_names.get(target_language, target_language)

    system = TRANSLATE_SYSTEM_PROMPT.format(target_lang=lang_name)
    user_msg = json.dumps(characters, ensure_ascii=False)

    messages = [
        LLMMessage(role="system", content=system),
        LLMMessage(role="user", content=user_msg),
    ]
    config = LLMConfig(model="", temperature=0.3, max_tokens=2048)

    for provider_name in _PROVIDER_ORDER:
        try:
            provider = get_provider(provider_name)
        except ValueError:
            continue

        try:
            raw = await asyncio.wait_for(
                provider.generate(messages, config),
                timeout=_TIMEOUT,
            )
            # Strip markdown fences
            text_clean = raw.strip()
            if text_clean.startswith("```"):
                text_clean = text_clean.split("\n", 1)[1] if "\n" in text_clean else text_clean[3:]
                if text_clean.endswith("```"):
                    text_clean = text_clean[:-3].strip()

            result = json.loads(text_clean)
            if not isinstance(result, list):
                continue

            return {
                item["id"]: {
                    "name": item.get("name", ""),
                    "tagline": item.get("tagline"),
                    "tags": item.get("tags", []),
                }
                for item in result
                if "id" in item
            }
        except Exception as e:
            logger.warning("Translation via %s failed: %s", provider_name, str(e)[:100])
            continue

    return {}


async def _save_translations(
    char_translations: dict[str, dict],
    target_language: str,
):
    """Save translation results to each character's translations JSONB column."""
    try:
        async with db_engine.begin() as conn:
            for char_id, tr in char_translations.items():
                await conn.execute(
                    text("""
                        UPDATE characters SET translations = jsonb_set(
                            COALESCE(translations, '{}'),
                            ARRAY[:lang],
                            :data::jsonb
                        ) WHERE id = :cid
                    """),
                    {"lang": target_language, "data": json.dumps(tr, ensure_ascii=False), "cid": char_id},
                )
    except Exception as e:
        logger.warning("Failed to save translations: %s", str(e)[:100])


async def ensure_translations(characters, target_language: str):
    """Translate card fields for characters whose original_language != target_language.

    Sets _active_translations attribute on each character object.
    """
    need_translation = []
    for c in characters:
        orig = getattr(c, 'original_language', None) or 'ru'
        if orig == target_language:
            continue
        cached = (getattr(c, 'translations', None) or {}).get(target_language)
        if cached:
            c._active_translations = cached
        else:
            need_translation.append(c)

    if not need_translation:
        return

    batch = [
        {
            "id": c.id,
            "name": c.name,
            "tagline": c.tagline or "",
            "tags": [t for t in (c.tags or "").split(",") if t],
        }
        for c in need_translation
    ]

    results = await translate_batch(batch, target_language)

    if results:
        # Save to DB in background (fire-and-forget)
        asyncio.create_task(_save_translations(results, target_language))

        for c in need_translation:
            tr = results.get(c.id)
            if tr:
                c._active_translations = tr
