"""Rewrite @sweetsin character descriptions via paid LLM models for better quality.

Run inside Docker container:
  docker compose exec -T backend python scripts/rewrite_characters.py
"""

import asyncio
import json
import logging
import os
import sys

# Add parent to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.llm.registry import init_providers, get_provider
from app.llm.base import LLMMessage, LLMConfig
from app.db.session import engine as db_engine
from app.autonomous.text_humanizer import humanize_text

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
logger = logging.getLogger("rewrite")

_PROVIDER_ORDER = ("claude", "openai", "gemini", "deepseek", "together", "groq", "cerebras", "openrouter")
_TIMEOUT = 60.0

_REWRITE_PROMPT = """Перепиши текст описания персонажа для ролевого чат-сайта. Сохрани смысл, но сделай текст:

1. ЖИВЫМ и конкретным — убери абстрактные описания, добавь детали
2. БЕЗ AI-клише — никаких "пронизан", "гобелен чувств", "поистине", "бесчисленный", "многогранный", "tapestry", "delve", "vibrant", "enigmatic", "realm", "journey"
3. ЕСТЕСТВЕННЫМ — как написал бы живой автор, а не ИИ
4. В ТОМ ЖЕ ФОРМАТЕ — сохрани структуру, длину примерно ту же (±20%), стиль от 2-го лица для personality

Верни ТОЛЬКО переписанный текст, без пояснений и кавычек.

Оригинал:
{text}"""

_REWRITE_GREETING_PROMPT = """Перепиши приветственное сообщение персонажа для ролевого чат-сайта. Сохрани:
- Литературный формат: 3-е лицо (он/она), действия обычным текстом, диалоги через тире «—», мысли через *звёздочки*
- Смысл и сюжет сцены
- Примерную длину (±20%)

Сделай текст:
1. Живым и конкретным — конкретные действия, физические детали
2. Без AI-клише — никаких "пронизан", "таинственный", "enigmatic" и т.п.
3. Естественным — как написал бы живой автор

Верни ТОЛЬКО переписанный текст.

Оригинал:
{text}"""


async def _rewrite_field(text: str, is_greeting: bool = False) -> str | None:
    """Rewrite a single text field via LLM."""
    if not text or len(text) < 30:
        return None

    prompt = (_REWRITE_GREETING_PROMPT if is_greeting else _REWRITE_PROMPT).format(text=text)
    messages = [
        LLMMessage(role="system", content="Ты — литературный редактор. Переписываешь текст, делая его живым и естественным. Отвечай ТОЛЬКО переписанным текстом."),
        LLMMessage(role="user", content=prompt),
    ]
    config = LLMConfig(model="", temperature=0.7, max_tokens=2048)

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
            if result and len(result) > 20:
                # Apply humanizer as safety net
                result = humanize_text(result)
                logger.info("  Rewritten via %s (%d → %d chars)", provider_name, len(text), len(result))
                return result
        except Exception as e:
            logger.warning("  %s failed: %s", provider_name, str(e)[:100])
            continue

    return None


async def main():
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

    # Show available providers
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

    # Fetch @sweetsin characters
    from sqlalchemy import text
    async with db_engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT c.id, c.name, c.personality, c.appearance, c.scenario, c.greeting_message
            FROM characters c
            JOIN users u ON c.creator_id = u.id
            WHERE u.email = 'system@sweetsin.cc'
            ORDER BY c.created_at
        """))
        characters = result.fetchall()

    logger.info("Found %d @sweetsin characters to rewrite", len(characters))

    updated = 0
    for char in characters:
        char_id, name, personality, appearance, scenario, greeting = char
        logger.info("\n=== %s (id=%s) ===", name, char_id[:8])

        updates = {}

        # Rewrite personality
        if personality:
            new_val = await _rewrite_field(personality)
            if new_val:
                updates["personality"] = new_val

        # Rewrite appearance
        if appearance:
            new_val = await _rewrite_field(appearance)
            if new_val:
                updates["appearance"] = new_val

        # Rewrite scenario
        if scenario:
            new_val = await _rewrite_field(scenario)
            if new_val:
                updates["scenario"] = new_val

        # Rewrite greeting
        if greeting:
            new_val = await _rewrite_field(greeting, is_greeting=True)
            if new_val:
                updates["greeting_message"] = new_val

        if updates:
            # Update DB + clear translation cache
            set_clauses = ", ".join(f"{k} = :{k}" for k in updates)
            updates["cid"] = char_id
            async with db_engine.begin() as conn:
                await conn.execute(
                    text(f"UPDATE characters SET {set_clauses}, translations = '{{}}'::jsonb, updated_at = NOW() WHERE id = :cid"),
                    updates,
                )
            updated += 1
            logger.info("  Updated %d fields, cleared translations", len(updates))
        else:
            logger.info("  No changes needed")

        # Small delay between characters
        await asyncio.sleep(1)

    logger.info("\n=== Done: %d/%d characters updated ===", updated, len(characters))


if __name__ == "__main__":
    asyncio.run(main())
