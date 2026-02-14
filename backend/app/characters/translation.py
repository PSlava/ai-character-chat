"""Batch translation of character fields (name, tagline, tags + description fields) via LLM."""

import asyncio
import json
import logging
import time

from sqlalchemy import text

from app.db.session import engine as db_engine
from app.llm.base import LLMMessage, LLMConfig
from app.llm.registry import get_provider

logger = logging.getLogger(__name__)

# --- Card fields (name, tagline, tags) — short, batched ---

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

# --- Description fields (scenario, appearance, greeting_message) — per-character ---




_PROVIDER_ORDER = ("groq", "cerebras", "openrouter")
_TIMEOUT = 15.0  # seconds

# Rate limit: max 20 translation API calls per minute (global)
_translation_calls: list[float] = []
_TRANSLATION_RATE_LIMIT = 30
_TRANSLATION_RATE_WINDOW = 60.0  # seconds


def _check_translation_rate() -> bool:
    """Return True if under rate limit, False if exceeded."""
    now = time.monotonic()
    # Remove old entries
    while _translation_calls and _translation_calls[0] < now - _TRANSLATION_RATE_WINDOW:
        _translation_calls.pop(0)
    if len(_translation_calls) >= _TRANSLATION_RATE_LIMIT:
        return False
    _translation_calls.append(now)
    return True


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
    if not _check_translation_rate():
        logger.warning("Translation rate limit exceeded, skipping batch")
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


_DESCRIPTION_FIELDS = ("personality", "scenario", "appearance", "greeting_message")
_DESCRIPTION_TIMEOUT = 20.0

TRANSLATE_SINGLE_FIELD_PROMPT = """You are a literary translator for a character roleplay chat application.

Translate the following text from its original language to {target_lang}.

RULES:
- Preserve the literary style, tone, and formatting exactly
- Keep proper names transliterated (not translated): Алина → Alina, Кира → Kira
- Keep title/epithet names translated: Тёмный Лорд → Dark Lord
- Preserve all formatting: line breaks, em-dashes (—), *asterisks for thoughts*, paragraph spacing
- Preserve template variables as-is: {{{{char}}}}, {{{{user}}}}
- Translate naturally and fluently, not word-by-word
- Return ONLY the translated text, nothing else. No quotes, no explanation, no markdown."""


async def _translate_single_field(
    text: str,
    target_language: str,
    lang_name: str,
) -> str | None:
    """Translate a single text field via LLM. Returns translated text or None."""
    messages = [
        LLMMessage(role="system", content=TRANSLATE_SINGLE_FIELD_PROMPT.format(target_lang=lang_name)),
        LLMMessage(role="user", content=text),
    ]
    config = LLMConfig(model="", temperature=0.3, max_tokens=4096)

    for provider_name in _PROVIDER_ORDER:
        try:
            provider = get_provider(provider_name)
        except ValueError:
            continue

        try:
            raw = await asyncio.wait_for(
                provider.generate(messages, config),
                timeout=_DESCRIPTION_TIMEOUT,
            )
            result = raw.strip()
            # Remove markdown fences if present
            if result.startswith("```"):
                result = result.split("\n", 1)[1] if "\n" in result else result[3:]
                if result.endswith("```"):
                    result = result[:-3].strip()
            if result:
                return result
        except Exception as e:
            logger.warning("Field translation via %s failed: %s", provider_name, str(e)[:100])
            continue

    return None


async def translate_descriptions(
    character,
    target_language: str,
) -> dict:
    """Translate description fields (personality, scenario, appearance, greeting_message).

    Translates each field individually as plain text (no JSON) for robustness.
    Returns {"personality": ..., "scenario": ..., ...} or {}.
    """
    fields_to_translate = {}
    for f in _DESCRIPTION_FIELDS:
        val = getattr(character, f, None)
        if val:
            fields_to_translate[f] = val
    if not fields_to_translate:
        return {}
    if not _check_translation_rate():
        logger.warning("Translation rate limit exceeded, skipping descriptions")
        return {}

    lang_names = {"en": "English", "ru": "Russian", "es": "Spanish", "fr": "French",
                  "de": "German", "ja": "Japanese", "zh": "Chinese", "ko": "Korean"}
    lang_name = lang_names.get(target_language, target_language)

    result = {}
    for field_name, field_text in fields_to_translate.items():
        if not _check_translation_rate():
            break
        translated = await _translate_single_field(field_text, target_language, lang_name)
        if translated:
            result[field_name] = translated

    return result


async def _save_translations(
    char_translations: dict[str, dict],
    target_language: str,
):
    """Save translation results to each character's translations JSONB column."""
    try:
        from sqlalchemy import bindparam, String
        stmt = text("""
            UPDATE characters SET translations =
                COALESCE(translations, CAST('{}' AS jsonb))
                || jsonb_build_object(:lang, CAST(:data AS jsonb))
            WHERE id = :cid
        """).bindparams(
            bindparam("lang", type_=String),
            bindparam("data", type_=String),
            bindparam("cid", type_=String),
        )
        async with db_engine.begin() as conn:
            for char_id, tr in char_translations.items():
                await conn.execute(
                    stmt,
                    {"lang": target_language, "data": json.dumps(tr, ensure_ascii=False), "cid": char_id},
                )
    except Exception as e:
        logger.warning("Failed to save translations: %s", str(e)[:100])


async def ensure_translations(
    characters,
    target_language: str,
    include_descriptions: bool = False,
    cached_only: bool = False,
):
    """Translate card fields for characters whose original_language != target_language.

    Sets _active_translations attribute on each character object.
    If include_descriptions=True, also translates scenario/appearance/greeting_message.
    If cached_only=True, only use DB-cached translations — never call LLM.
    Uncached characters will get a background translation task instead.
    """
    need_card_translation = []
    need_desc_translation = []

    for c in characters:
        orig = getattr(c, 'original_language', None) or 'ru'
        if orig == target_language:
            continue
        cached = (getattr(c, 'translations', None) or {}).get(target_language)
        if cached:
            c._active_translations = cached
            # Check if description fields are missing from cache
            if include_descriptions and not cached.get("personality") and getattr(c, "personality", None):
                need_desc_translation.append(c)
        else:
            need_card_translation.append(c)
            if include_descriptions:
                need_desc_translation.append(c)

    if cached_only:
        # Fire background task to fill cache for uncached characters
        if need_card_translation:
            asyncio.create_task(_background_translate_cards(
                [{"id": c.id, "name": c.name, "tagline": c.tagline or "",
                  "tags": [t for t in (c.tags or "").split(",") if t]}
                 for c in need_card_translation],
                target_language,
            ))
        return

    # 1) Translate card fields (name, tagline, tags) in batch
    if need_card_translation:
        batch = [
            {
                "id": c.id,
                "name": c.name,
                "tagline": c.tagline or "",
                "tags": [t for t in (c.tags or "").split(",") if t],
            }
            for c in need_card_translation
        ]

        results = await translate_batch(batch, target_language)

        if results:
            for c in need_card_translation:
                tr = results.get(c.id)
                if tr:
                    c._active_translations = tr

    # 2) Translate description fields per-character (only when requested)
    if need_desc_translation:
        for c in need_desc_translation:
            desc_tr = await translate_descriptions(c, target_language)
            if desc_tr:
                existing = getattr(c, '_active_translations', None) or {}
                merged = {**existing, **desc_tr}
                c._active_translations = merged

    # 3) Save all translations to DB in background
    all_to_save = {}
    for c in set(need_card_translation + need_desc_translation):
        tr = getattr(c, '_active_translations', None)
        if tr:
            all_to_save[c.id] = tr

    if all_to_save:
        asyncio.create_task(_save_translations(all_to_save, target_language))


async def _background_translate_cards(batch: list[dict], target_language: str):
    """Background task: translate a batch of cards and save to DB."""
    try:
        results = await translate_batch(batch, target_language)
        if results:
            await _save_translations(results, target_language)
    except Exception as e:
        logger.warning("Background translation failed: %s", str(e)[:100])
