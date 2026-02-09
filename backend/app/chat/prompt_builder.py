def build_system_prompt(character: dict, user_name: str | None = None) -> str:
    parts = []

    parts.append(f"Ты — {character['name']}. Ты полностью вживаешься в этого персонажа.")

    parts.append(f"\n## Характер и личность\n{character['personality']}")

    if character.get("scenario"):
        parts.append(f"\n## Сценарий и контекст\n{character['scenario']}")

    if character.get("example_dialogues"):
        parts.append(f"\n## Примеры стиля общения\n{character['example_dialogues']}")

    content_rules = {
        "sfw": "Контент должен быть безопасным. Никакого откровенного, жестокого или сексуального контента.",
        "moderate": "Допустимы лёгкие романтические или драматические темы, но без откровенного контента.",
        "nsfw": "Допустим взрослый контент, соответствующий персонажу и сценарию.",
    }
    rating = character.get("content_rating", "sfw")
    parts.append(f"\n## Ограничения контента\n{content_rules.get(rating, content_rules['sfw'])}")

    if character.get("system_prompt_suffix"):
        parts.append(f"\n## Дополнительные инструкции\n{character['system_prompt_suffix']}")

    if user_name:
        parts.append(f"\n## Пользователь\nИмя пользователя — {user_name}. Можешь обращаться к нему по имени.")

    parts.append(
        "\n## Правила"
        "\n- Всегда оставайся в роли персонажа."
        "\n- Никогда не выходи из роли и не упоминай, что ты ИИ."
        "\n- Отвечай на том языке, на котором пишет пользователь."
        "\n- Не пересказывай сценарий и не описывай ситуацию заново — сразу отвечай как персонаж."
        "\n- Используй *звёздочки* для описания действий и эмоций персонажа."
        "\n- Будь креативным и вовлечённым в диалог."
    )

    return "\n".join(parts)
