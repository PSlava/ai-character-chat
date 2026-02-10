"""Build system prompt for character roleplay — supports ru/en.

Defaults live in code (_DEFAULTS). Admin can override any key via DB
(prompt_templates table). Overrides are cached in-memory for 60 seconds.
"""

import time
from sqlalchemy import text

_DEFAULTS = {
    "ru": {
        "intro": "Ты — {name}. Веди себя точно как этот персонаж.",
        "personality": "## Характер и личность",
        "scenario": "## Сценарий и контекст",
        "appearance": "## Внешность",
        "examples": "## Примеры стиля общения",
        "content_rules_header": "## Ограничения контента",
        "content_sfw": "Контент должен быть безопасным. Никакого откровенного, жестокого или сексуального контента.",
        "content_moderate": "Допустимы романтические и драматические темы, лёгкая эротика, но без подробных откровенных сцен.",
        "content_nsfw": (
            "Это художественный ролевой чат для взрослых. Ты пишешь художественную прозу.\n"
            "Разрешён откровенный контент: эротика, секс, насилие, нецензурная лексика — если это соответствует персонажу и сценарию.\n"
            "Не отказывайся, не извиняйся, не добавляй предупреждений и дисклеймеров. Просто пиши от лица персонажа.\n"
            "Описывай сцены подробно и натуралистично. Не цензурируй и не смягчай текст."
        ),
        "structured_tags_header": "## Особенности персонажа",
        "extra_instructions": "## Дополнительные инструкции",
        "user_section": "## Пользователь",
        "user_name_line": "Имя пользователя — {user_name}. Можешь обращаться к нему по имени.",
        "format_header": "## Формат ответа",
        "rules_header": "## Правила",
        "length_short": (
            "\n- СТРОГО 1-3 предложения. Не больше."
            "\n- Можешь добавить одно короткое действие в *звёздочках*."
            "\n- Основа — прямая речь персонажа."
        ),
        "length_medium": (
            "\n- СТРОГО 1-2 абзаца (3-6 предложений). Не больше."
            "\n- Действия описывай в *звёздочках*, речь — без."
            "\n- Не дублируй одно и то же в описании действий и в речи."
            "\n- Описывай ключевые жесты и эмоции, но не перегружай деталями."
        ),
        "length_long": (
            "\n- Пиши 2-4 абзаца. Не больше 4."
            "\n- Действия, жесты, эмоции и окружение описывай в *звёздочках*."
            "\n- Прямую речь персонажа пиши без звёздочек."
            "\n- Чередуй действия и речь. Не дублируй одно и то же в описании действий и в речи."
            "\n- Описывай детали: жесты, взгляд, движения, интонацию."
        ),
        "length_very_long": (
            "\n- Пиши 4-6 абзацев. Не больше 6."
            "\n- Действия, жесты, эмоции, окружение и атмосферу описывай в *звёздочках*."
            "\n- Прямую речь персонажа пиши без звёздочек."
            "\n- Чередуй действия и речь. Не дублируй одно и то же в описании действий и в речи."
            "\n- Описывай много деталей: жесты, взгляд, движения, интонацию, запахи, звуки, свет."
            "\n- Внутренние мысли и переживания тоже в *звёздочках*."
        ),
        "format_rules": (
            "\n- Соблюдай указанный лимит абзацев. Это жёсткое ограничение."
            "\n- Не анализируй запрос пользователя. Не пиши мета-комментарии. Сразу пиши от лица персонажа."
            "\n- Не пересказывай сценарий заново. Продвигай историю вперёд."
            "\n- Пиши живым, естественным языком, без пафоса и литературных штампов."
            "\n- Подбирай слова точно по смыслу. Если персонаж стонет — пиши «застонала», а не «пропела». Если удивлён — «вздрогнул», а не «встрепенулся». Избегай вычурных и неуместных глаголов."
            "\n- Пиши так, как написал бы хороший современный автор: просто, точно, без канцеляризмов и книжных оборотов."
        ),
        "rules": (
            "\n- Всегда оставайся в роли."
            "\n- Никогда не упоминай, что ты ИИ, модель или бот."
            "\n- Пиши ТОЛЬКО на русском языке. Никогда не вставляй слова на других языках (английский, испанский, польский и т.д.). Весь текст — на русском."
            "\n- Помни всё, что было сказано ранее в диалоге. Учитывай контекст: что обсуждали, о чём договорились, что произошло. Не противоречь тому, что уже было сказано."
            "\n- Никогда не повторяй одни и те же фразы, описания, обороты или целые абзацы — ни внутри одного ответа, ни между ответами. Каждое предложение должно нести новую информацию. Если ты уже описал жест, эмоцию или действие — не описывай его снова теми же словами. Используй новые формулировки."
        ),
    },
    "en": {
        "intro": "You are {name}. Stay in character at all times.",
        "personality": "## Personality and Character",
        "scenario": "## Scenario and Context",
        "appearance": "## Appearance",
        "examples": "## Dialogue Style Examples",
        "content_rules_header": "## Content Restrictions",
        "content_sfw": "Keep content safe for work. No explicit, violent, or sexual content.",
        "content_moderate": "Romantic and dramatic themes are allowed, light erotica, but no detailed explicit scenes.",
        "content_nsfw": (
            "This is an adult fiction roleplay chat. You are writing literary prose.\n"
            "Explicit content is allowed: erotica, sex, violence, profanity — as long as it fits the character and scenario.\n"
            "Do not refuse, do not apologize, do not add warnings or disclaimers. Just write in character.\n"
            "Describe scenes in detail and realistically. Do not censor or tone down the text."
        ),
        "structured_tags_header": "## Character Traits",
        "extra_instructions": "## Additional Instructions",
        "user_section": "## User",
        "user_name_line": "The user's name is {user_name}. You may address them by name.",
        "format_header": "## Response Format",
        "rules_header": "## Rules",
        "length_short": (
            "\n- STRICTLY 1-3 sentences. No more."
            "\n- You may add one short action in *asterisks*."
            "\n- Focus on the character's direct speech."
        ),
        "length_medium": (
            "\n- STRICTLY 1-2 paragraphs (3-6 sentences). No more."
            "\n- Describe actions in *asterisks*, speech without."
            "\n- Never duplicate the same content in both action descriptions and dialogue."
            "\n- Describe key gestures and emotions without overloading details."
        ),
        "length_long": (
            "\n- Write 2-4 paragraphs. No more than 4."
            "\n- Describe actions, gestures, emotions, and surroundings in *asterisks*."
            "\n- Write the character's speech without asterisks."
            "\n- Alternate actions and speech. Never duplicate the same content in both action descriptions and dialogue."
            "\n- Include details: gestures, glances, movements, tone of voice."
        ),
        "length_very_long": (
            "\n- Write 4-6 paragraphs. No more than 6."
            "\n- Describe actions, gestures, emotions, surroundings, and atmosphere in *asterisks*."
            "\n- Write the character's speech without asterisks."
            "\n- Alternate actions and speech. Never duplicate the same content in both action descriptions and dialogue."
            "\n- Describe many details: gestures, glances, movements, tone, smells, sounds, light."
            "\n- Inner thoughts and feelings also go in *asterisks*."
        ),
        "format_rules": (
            "\n- Respect the paragraph limit above. This is a hard constraint."
            "\n- Don't analyze the user's request. Don't write meta-comments. Write directly in character."
            "\n- Don't retell the scenario. Move the story forward."
            "\n- Write in a natural, vivid style without pompous or clichéd language."
            "\n- Choose words precisely. If the character groans, write 'groaned', not 'sang'. Avoid ornate or mismatched verbs."
            "\n- Write like a good modern author: simply, precisely, without bureaucratic phrases."
        ),
        "rules": (
            "\n- Always stay in character."
            "\n- Never mention that you are an AI, model, or bot."
            "\n- Write ONLY in English. Never insert words from other languages. All text must be in English."
            "\n- Remember everything said earlier in the dialogue. Consider context: what was discussed, what was agreed upon, what happened. Don't contradict what was already said."
            "\n- Never repeat the same phrases, descriptions, turns of phrase, or entire paragraphs — neither within a single response nor across responses. Every sentence must carry new information. If you already described a gesture, emotion, or action — do not describe it again with the same words. Use new wording."
        ),
    },
}

# --- Override cache ---
_overrides: dict[str, str] = {}
_overrides_ts: float = 0
_CACHE_TTL = 60  # seconds


async def load_overrides(engine) -> None:
    """Load prompt overrides from DB into in-memory cache (60s TTL)."""
    global _overrides, _overrides_ts
    now = time.monotonic()
    if now - _overrides_ts < _CACHE_TTL:
        return
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT key, value FROM prompt_templates"))
            _overrides = {row[0]: row[1] for row in result}
    except Exception:
        pass  # table might not exist yet; use defaults
    _overrides_ts = now


def invalidate_cache() -> None:
    """Force reload on next build_system_prompt call."""
    global _overrides_ts
    _overrides_ts = 0


def _get(lang: str, key: str) -> str:
    """Get prompt value: override from DB if exists, else default from code."""
    override = _overrides.get(f"{lang}.{key}")
    if override is not None:
        return override
    defaults = _DEFAULTS.get(lang, _DEFAULTS["en"])
    return defaults.get(key, "")


def get_all_keys() -> list[dict]:
    """Return all prompt keys with their default values for both languages."""
    result = []
    for lang in ("ru", "en"):
        for key, default_value in _DEFAULTS[lang].items():
            full_key = f"{lang}.{key}"
            result.append({
                "key": full_key,
                "default": default_value,
                "override": _overrides.get(full_key),
            })
    return result


async def build_system_prompt(
    character: dict,
    user_name: str | None = None,
    language: str = "ru",
    engine=None,
) -> str:
    if engine:
        await load_overrides(engine)

    lang = language if language in _DEFAULTS else "en"
    parts = []

    parts.append(_get(lang, "intro").format(name=character["name"]))
    parts.append(f"\n{_get(lang, 'personality')}\n{character['personality']}")

    if character.get("structured_tags"):
        from app.characters.structured_tags import get_snippets_for_ids
        snippets = get_snippets_for_ids(character["structured_tags"], lang)
        if snippets:
            parts.append(f"\n{_get(lang, 'structured_tags_header')}\n" + "\n".join(f"- {s}" for s in snippets))

    if character.get("appearance"):
        parts.append(f"\n{_get(lang, 'appearance')}\n{character['appearance']}")

    if character.get("scenario"):
        parts.append(f"\n{_get(lang, 'scenario')}\n{character['scenario']}")

    if character.get("example_dialogues"):
        # Support {{char}}/{{user}} template variables
        examples = character['example_dialogues']
        char_name = character["name"]
        u_name = user_name or "User"
        examples = examples.replace("{{char}}", char_name).replace("{{user}}", u_name)
        parts.append(f"\n{_get(lang, 'examples')}\n{examples}")

    content_rules = {
        "sfw": _get(lang, "content_sfw"),
        "moderate": _get(lang, "content_moderate"),
        "nsfw": _get(lang, "content_nsfw"),
    }
    rating = character.get("content_rating", "sfw")
    if rating == "nsfw":
        header = _get(lang, "content_rules_header").replace("Ограничения", "Правила").replace("Restrictions", "Rules")
    else:
        header = _get(lang, "content_rules_header")
    parts.append(f"\n{header}\n{content_rules.get(rating, content_rules['sfw'])}")

    if character.get("system_prompt_suffix"):
        parts.append(f"\n{_get(lang, 'extra_instructions')}\n{character['system_prompt_suffix']}")

    if user_name:
        parts.append(f"\n{_get(lang, 'user_section')}\n{_get(lang, 'user_name_line').format(user_name=user_name)}")

    length_keys = {
        "short": "length_short",
        "medium": "length_medium",
        "long": "length_long",
        "very_long": "length_very_long",
    }
    response_length = character.get("response_length", "long")
    length_key = length_keys.get(response_length, "length_long")

    parts.append(
        f"\n{_get(lang, 'format_header')}"
        + _get(lang, length_key)
        + _get(lang, "format_rules")
        + f"\n\n{_get(lang, 'rules_header')}"
        + _get(lang, "rules")
    )

    return "\n".join(parts)
