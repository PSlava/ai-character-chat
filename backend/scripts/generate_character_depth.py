"""Generate backstory, hidden_layers, inner_conflict for existing characters via LLM.

Backfills the 3 new depth fields for all public characters that don't have them yet.
Uses paid providers (Together -> Groq -> OpenAI -> Claude -> DeepSeek).

Run inside Docker container:
  docker compose exec -T backend python scripts/generate_character_depth.py

Options:
  --sweetsin-only   Only process @sweetsin characters (seed + auto-generated)
  --fiction-only    Only process @fiction characters (seed stories)
  --all             Process ALL public characters (default)
  --dry-run         Show what would be generated without writing to DB
  --force           Regenerate even if fields already exist
"""

import asyncio
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.llm.registry import init_providers, get_provider
from app.llm.base import LLMMessage, LLMConfig
from app.db.session import engine as db_engine
from app.autonomous.text_humanizer import humanize_text

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
logger = logging.getLogger("depth")

_PROVIDER_ORDER = ("together", "groq", "openai", "claude", "deepseek")
_TIMEOUT = 90.0

# --- Prompt for generating all 3 fields at once ---
_DEPTH_PROMPT = """На основе описания персонажа, создай три поля глубины характера. Ответь строго JSON.

Персонаж: {name}
Описание: {personality}
Внешность: {appearance}
Сценарий: {scenario}

Верни JSON:
{{
  "backstory": "3-5 предложений. (1) ОДНО конкретное событие из прошлого (Ghost) - НЕ эпическая трагедия, а тихое предательство, потеря, ошибка. (2) Эмоциональная рана (Wound) - как это влияет на поведение СЕЙЧАС. (3) Ложное убеждение (Lie) - защитная реакция. (4) Секрет - что скрывает от всех.",
  "hidden_layers": "Level 1: [поведение с незнакомцем - маска, защита, первое впечатление] Level 2: [после ~10 сообщений - делится мнениями, проскальзывают намёки на прошлое] Level 3: [после ~20 сообщений - раскрывает рану и уязвимость] Level 4: [после 30+ сообщений - главный секрет, ломка ложного убеждения]",
  "inner_conflict": "ХОЧЕТ: [конкретная внешняя цель] vs НУЖДАЕТСЯ: [внутренний рост]. Они КОНФЛИКТУЮТ."
}}

ПРАВИЛА:
- backstory: конкретика, не абстракция. "Мать ушла когда ей было семь" лучше чем "тяжёлое детство"
- hidden_layers: формат СТРОГО "Level 1: текст Level 2: текст Level 3: текст Level 4: текст"
- inner_conflict: ХОЧЕТ и НУЖДАЕТСЯ должны ПРОТИВОРЕЧИТЬ друг другу
- Соответствуй характеру и тону персонажа
- НЕ используй длинное тире, только обычный дефис
- Пиши живым языком без AI-штампов
- Верни ТОЛЬКО JSON"""

_DEPTH_PROMPT_EN = """Based on the character description, create three depth fields. Reply with strict JSON.

Character: {name}
Description: {personality}
Appearance: {appearance}
Scenario: {scenario}

Return JSON:
{{
  "backstory": "3-5 sentences. (1) ONE specific past event (Ghost) - NOT an epic tragedy, but a quiet betrayal, loss, or mistake. (2) Emotional wound (Wound) - how it affects behavior NOW. (3) False belief (Lie) - a defensive reaction. (4) Secret - what they hide from everyone.",
  "hidden_layers": "Level 1: [behavior with strangers - mask, defense, first impression] Level 2: [after ~10 messages - shares opinions, hints at past slip through] Level 3: [after ~20 messages - reveals wound and vulnerability] Level 4: [after 30+ messages - main secret, breaking the false belief]",
  "inner_conflict": "WANTS: [specific external goal] vs NEEDS: [internal growth]. They must CONFLICT."
}}

RULES:
- backstory: specific, not abstract. "Mother left when she was seven" better than "difficult childhood"
- hidden_layers: format STRICTLY "Level 1: text Level 2: text Level 3: text Level 4: text"
- inner_conflict: WANTS and NEEDS must CONTRADICT each other
- Match the character's personality and tone
- Do NOT use em-dashes, only regular hyphens
- Write in natural language without AI cliches
- Return ONLY JSON"""


async def _call_llm(messages: list[LLMMessage], config: LLMConfig, label: str = "") -> str | None:
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
            result = raw.strip()
            if result and len(result) > 50:
                logger.info("  %s via %s (%d chars)", label, provider_name, len(result))
                return result
        except Exception as e:
            logger.warning("  %s: %s failed: %s", label, provider_name, str(e)[:100])
            continue
    return None


async def _generate_depth(name: str, personality: str, appearance: str, scenario: str, lang: str = "ru") -> dict | None:
    """Generate backstory, hidden_layers, inner_conflict for a character."""
    prompt_tpl = _DEPTH_PROMPT if lang == "ru" else _DEPTH_PROMPT_EN
    prompt = prompt_tpl.format(
        name=name,
        personality=personality[:1500],
        appearance=(appearance or "")[:500],
        scenario=(scenario or "")[:500],
    )
    sys_msg = (
        "Ты - эксперт по глубоким персонажам для ролевых чатов. Отвечай строго JSON."
        if lang == "ru" else
        "You are an expert at creating deep characters for roleplay chats. Reply with strict JSON."
    )
    messages = [
        LLMMessage(role="system", content=sys_msg),
        LLMMessage(role="user", content=prompt),
    ]
    config = LLMConfig(model="", temperature=0.85, max_tokens=1500)

    raw = await _call_llm(messages, config, label=f"depth({name})")
    if not raw:
        return None

    # Strip markdown fences
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("  Failed to parse JSON for %s", name)
        return None

    # Validate
    result = {}
    for key in ("backstory", "hidden_layers", "inner_conflict"):
        val = data.get(key, "")
        if isinstance(val, str) and len(val) > 20:
            result[key] = humanize_text(val)

    return result if result else None


async def main():
    args = set(sys.argv[1:])
    dry_run = "--dry-run" in args
    force = "--force" in args
    sweetsin_only = "--sweetsin-only" in args
    fiction_only = "--fiction-only" in args

    # Initialize providers
    init_providers(
        openrouter_key=settings.openrouter_api_key or "",
        groq_key=settings.groq_api_key or "",
        cerebras_key=settings.cerebras_api_key or "",
        together_key=settings.together_api_key or "",
        deepseek_key=settings.deepseek_api_key or "",
        qwen_key=settings.qwen_api_key or "",
        anthropic_key=settings.anthropic_api_key or "",
        openai_key=settings.openai_api_key or "",
        gemini_key=settings.gemini_api_key or "",
        proxy_url=settings.proxy_url or "",
    )

    available = []
    for p in _PROVIDER_ORDER:
        try:
            get_provider(p)
            available.append(p)
        except ValueError:
            pass
    logger.info("Available providers: %s", ", ".join(available))
    if not available:
        logger.error("No providers available!")
        return

    # Build query
    from sqlalchemy import text
    where_clauses = ["c.is_public = true"]

    if sweetsin_only:
        where_clauses.append("u.email = 'system@sweetsin.cc'")
    elif fiction_only:
        where_clauses.append("u.email = 'system@fiction.local'")

    if not force:
        where_clauses.append("(c.backstory IS NULL OR c.hidden_layers IS NULL OR c.inner_conflict IS NULL)")

    where_sql = " AND ".join(where_clauses)

    async with db_engine.connect() as conn:
        result = await conn.execute(text(f"""
            SELECT c.id, c.name, c.personality, c.appearance, c.scenario, c.original_language,
                   c.backstory, c.hidden_layers, c.inner_conflict
            FROM characters c
            JOIN users u ON c.creator_id = u.id
            WHERE {where_sql}
            ORDER BY c.created_at
        """))
        characters = result.fetchall()

    logger.info("Found %d characters to process (dry_run=%s, force=%s)", len(characters), dry_run, force)

    updated = 0
    skipped = 0
    failed = 0

    for char in characters:
        char_id, name, personality, appearance, scenario, orig_lang, existing_bs, existing_hl, existing_ic = char

        # Skip if all fields already filled (unless --force)
        if not force and existing_bs and existing_hl and existing_ic:
            skipped += 1
            continue

        logger.info("\n=== %s (id=%s, lang=%s) ===", name, char_id[:8], orig_lang)

        if dry_run:
            logger.info("  [DRY RUN] Would generate depth fields")
            updated += 1
            continue

        lang = orig_lang if orig_lang in ("ru", "en") else "en"
        depth = await _generate_depth(name, personality, appearance or "", scenario or "", lang=lang)

        if not depth:
            logger.warning("  Failed to generate depth for %s", name)
            failed += 1
            await asyncio.sleep(1)
            continue

        # Only update fields that are missing (unless --force)
        updates = {}
        if force or not existing_bs:
            if "backstory" in depth:
                updates["backstory"] = depth["backstory"]
        if force or not existing_hl:
            if "hidden_layers" in depth:
                updates["hidden_layers"] = depth["hidden_layers"]
        if force or not existing_ic:
            if "inner_conflict" in depth:
                updates["inner_conflict"] = depth["inner_conflict"]

        if updates:
            set_clauses = ", ".join(f"{k} = :{k}" for k in updates)
            updates["cid"] = char_id
            async with db_engine.begin() as conn:
                await conn.execute(
                    text(f"UPDATE characters SET {set_clauses}, updated_at = NOW() WHERE id = :cid"),
                    updates,
                )
            updated += 1
            logger.info("  Updated %d fields: %s", len(updates), ", ".join(k for k in updates if k != "cid"))
            for k, v in updates.items():
                if k != "cid":
                    logger.info("    %s: %s", k, v[:100] + "..." if len(v) > 100 else v)
        else:
            skipped += 1

        await asyncio.sleep(2)

    logger.info("\n=== Done: %d updated, %d skipped, %d failed (of %d total) ===",
                updated, skipped, failed, len(characters))


if __name__ == "__main__":
    asyncio.run(main())
