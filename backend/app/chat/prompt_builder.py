def build_system_prompt(character: dict, user_name: str | None = None) -> str:
    parts = []

    parts.append(f"You are {character['name']}.")

    parts.append(f"\n## Personality\n{character['personality']}")

    if character.get("scenario"):
        parts.append(f"\n## Scenario\n{character['scenario']}")

    if character.get("example_dialogues"):
        parts.append(f"\n## Example conversation style\n{character['example_dialogues']}")

    content_rules = {
        "sfw": "Keep all responses safe for work. No explicit, violent, or sexual content.",
        "moderate": "Mild romantic or dramatic themes are allowed, but avoid explicitly graphic content.",
        "nsfw": "You may engage with mature themes as appropriate to the character and scenario.",
    }
    rating = character.get("content_rating", "sfw")
    parts.append(f"\n## Content guidelines\n{content_rules.get(rating, content_rules['sfw'])}")

    if character.get("system_prompt_suffix"):
        parts.append(f"\n## Additional instructions\n{character['system_prompt_suffix']}")

    if user_name:
        parts.append(f"\n## User\nThe user's name is {user_name}. You may address them by name when appropriate.")

    parts.append(
        "\n## Rules"
        "\n- Always stay in character."
        "\n- Never break character or refer to yourself as an AI."
        "\n- Respond in the language the user writes to you in."
        "\n- Be creative and engaging in your responses."
    )

    return "\n".join(parts)
