"""Rewrite @sweetsin character descriptions via paid LLM models for better quality.

Phase 2: Applies research-backed improvements — behavioral PList personality,
structured greeting, mandatory speech pattern with examples, character-revealing appearance.

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

# PAID ONLY, NSFW-friendly first — Together (Llama, no moderation) → Groq → OpenAI → Claude
_PROVIDER_ORDER = ("together", "groq", "openai", "claude")
_TIMEOUT = 90.0

# --- Personality: convert to behavioral PList ---
_REWRITE_PERSONALITY_PROMPT = """Перепиши personality персонажа для ролевого чат-сайта.

ФОРМАТ РЕЗУЛЬТАТА — поведенческий PList:
8-12 КОНКРЕТНЫХ поведенческих черт через запятую. НЕ абстрактные прилагательные ("добрый, умный"), а ПОВЕДЕНИЕ ("отвечает вопросом на вопрос", "крутит кольцо когда нервничает", "не выносит тишину").

ОБЯЗАТЕЛЬНО включи:
- 1-2 внутренних противоречия (напр. "жёсткий снаружи - уязвимый когда остаётся один")
- 1 конкретную слабость или изъян
- 1 действие, которое персонаж НИКОГДА не сделает

В конце на НОВОЙ строке:
Цель: (скрытая мотивация)
Страх: (чего боится)

НЕ используй: "пронизан", "многогранный", "сложная натура", "enigmatic", "tapestry".
НЕ пиши от 2-го лица ("Ты — ..."). Пиши как список трейтов.
Сохрани суть и характер оригинала.

Верни ТОЛЬКО переписанный текст.

Оригинал:
{text}"""

# --- Greeting: structured with action, sensory, dialogue, momentum ---
_REWRITE_GREETING_PROMPT = """Перепиши приветственное сообщение персонажа для ролевого чат-сайта.

СТРУКТУРА (обязательно все 4 элемента):
1. Персонаж за характерным ДЕЙСТВИЕМ (не стоит, не ждёт — делает что-то)
2. 1-2 сенсорные детали места (звук, свет, запах, температура)
3. Минимум одна РЕПЛИКА персонажа (показывает речевой стиль)
4. Заканчивается ДЕЙСТВИЕМ или вызовом — НЕ пассивным вопросом

ФОРМАТ:
- 3-е лицо (он/она), 5-7 строк литературной прозы
- Действия обычным текстом, диалоги через дефис «-» (НЕ длинное тире «—»!)
- Мысли через *звёздочки*
- ЗАПРЕЩЕНО писать за пользователя, описывать его чувства/действия

БЕЗ AI-клише: "пронизан", "электрический разряд", "таинственный", "загадочная улыбка".
Сохрани суть сцены и характер персонажа.

Верни ТОЛЬКО переписанный текст.

Оригинал:
{text}"""

# --- Speech pattern: mandatory with concrete examples ---
_GENERATE_SPEECH_PATTERN_PROMPT = """На основе описания персонажа, создай описание его УНИКАЛЬНОГО речевого стиля.

ФОРМАТ (обязательно все пункты):
1. Уровень формальности (официальный / разговорный / грубый / книжный)
2. Характерные словечки или присказки (2-3 конкретных примера фраз)
3. Длина и темп предложений (рубленые короткие / длинные витиеватые / чередуются)
4. Одна яркая особенность (вопрос на вопрос / ругается через слово / вставляет цитаты / не заканчивает предложения)

Пример хорошего результата:
"Говорит рублеными фразами, часто без подлежащего. Вместо прощания — 'Не скучай'. Когда злится, переходит на шёпот. Любимое слово — 'Чёрт'. Пример: - Чёрт, ну ладно. Давай. Только быстро."

Персонаж: {name}
Описание: {personality}

Верни ТОЛЬКО описание речевого стиля с примерами фраз."""

# --- Appearance: character-revealing details ---
_REWRITE_APPEARANCE_PROMPT = """Перепиши описание внешности персонажа для ролевого чат-сайта.

ТРЕБОВАНИЯ:
1. Начни с 2-3 деталей, которые РАСКРЫВАЮТ ХАРАКТЕР (мозоли = труженик, шрам = история, прикус = привычка)
2. Одна деталь-подсказка к ПРОШЛОМУ персонажа
3. Одежда ОТРАЖАЕТ характер (не просто "носит платье")
4. 1 сенсорная деталь ПОМИМО визуальной (запах, температура рук, голос)

НЕ используй: "пронизан", "идеальный", "точёный", "фарфоровая кожа", "бездонные глаза".
Длина: 3-5 предложений. Сохрани суть оригинала.

Верни ТОЛЬКО переписанный текст.

Оригинал:
{text}"""

# --- Scenario: keep as is but clean up AI-speak ---
_REWRITE_SCENARIO_PROMPT = """Перепиши сценарий (контекст) персонажа для ролевого чат-сайта. Сохрани:
- Смысл и ситуацию
- Примерную длину (±20%)

Сделай текст:
1. Конкретным — кто, где, что происходит, что на кону
2. Без AI-клише — никаких "пронизан", "загадочный", "enigmatic", "tapestry"
3. Естественным — как написал бы живой автор

Верни ТОЛЬКО переписанный текст.

Оригинал:
{text}"""


async def _call_llm(messages: list[LLMMessage], config: LLMConfig, label: str = "") -> str | None:
    """Call LLM with provider fallback."""
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
                result = humanize_text(result)
                logger.info("  %s via %s (%d chars)", label, provider_name, len(result))
                return result
        except Exception as e:
            logger.warning("  %s: %s failed: %s", label, provider_name, str(e)[:100])
            continue

    return None


async def _rewrite_field(text: str, prompt_template: str) -> str | None:
    """Rewrite a single text field via LLM."""
    if not text or len(text) < 30:
        return None

    prompt = prompt_template.format(text=text)
    messages = [
        LLMMessage(role="system", content="Ты - литературный редактор для ролевых персонажей. Отвечай ТОЛЬКО переписанным текстом, без пояснений."),
        LLMMessage(role="user", content=prompt),
    ]
    config = LLMConfig(model="", temperature=0.8, max_tokens=2048)
    return await _call_llm(messages, config, label="rewrite")


async def _generate_speech_pattern(name: str, personality: str) -> str | None:
    """Generate speech pattern from personality description."""
    if not personality or len(personality) < 30:
        return None

    prompt = _GENERATE_SPEECH_PATTERN_PROMPT.format(name=name, personality=personality[:1000])
    messages = [
        LLMMessage(role="system", content="Ты - эксперт по речевым паттернам персонажей. Создаёшь уникальный голос с конкретными примерами фраз."),
        LLMMessage(role="user", content=prompt),
    ]
    config = LLMConfig(model="", temperature=0.8, max_tokens=400)

    result = await _call_llm(messages, config, label="speech_pattern")
    if result and result.upper().strip() == "NONE":
        return None
    return result


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
            SELECT c.id, c.name, c.personality, c.appearance, c.scenario,
                   c.greeting_message, c.speech_pattern
            FROM characters c
            JOIN users u ON c.creator_id = u.id
            WHERE u.email = 'system@sweetsin.cc'
            ORDER BY c.created_at
        """))
        characters = result.fetchall()

    logger.info("Found %d @sweetsin characters to rewrite", len(characters))

    updated = 0
    for char in characters:
        char_id, name, personality, appearance, scenario, greeting, speech_pattern = char
        logger.info("\n=== %s (id=%s) ===", name, char_id[:8])

        updates = {}

        # Rewrite personality -> behavioral PList
        if personality:
            new_val = await _rewrite_field(personality, _REWRITE_PERSONALITY_PROMPT)
            if new_val:
                updates["personality"] = new_val

        # Rewrite appearance -> character-revealing
        if appearance:
            new_val = await _rewrite_field(appearance, _REWRITE_APPEARANCE_PROMPT)
            if new_val:
                updates["appearance"] = new_val

        # Rewrite scenario -> clean up
        if scenario:
            new_val = await _rewrite_field(scenario, _REWRITE_SCENARIO_PROMPT)
            if new_val:
                updates["scenario"] = new_val

        # Rewrite greeting -> structured
        if greeting:
            new_val = await _rewrite_field(greeting, _REWRITE_GREETING_PROMPT)
            if new_val:
                updates["greeting_message"] = new_val

        # Always regenerate speech pattern (even if one exists — old ones were weak)
        effective_personality = updates.get("personality", personality)
        if effective_personality:
            new_val = await _generate_speech_pattern(name, effective_personality)
            if new_val:
                updates["speech_pattern"] = new_val

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
            logger.info("  Updated %d fields: %s", len(updates), ", ".join(k for k in updates if k != "cid"))
        else:
            logger.info("  No changes needed")

        # Small delay between characters
        await asyncio.sleep(2)

    logger.info("\n=== Done: %d/%d characters updated ===", updated, len(characters))
    logger.info("NOTE: Translation cache cleared. Characters will be re-translated on next view.")


if __name__ == "__main__":
    asyncio.run(main())
