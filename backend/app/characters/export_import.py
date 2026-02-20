"""SillyTavern / Chub character card v2 export/import."""

from app.db.models import Character


def character_to_card(char: Character) -> dict:
    """Export a character to SillyTavern character card v2 format."""
    tags = [t.strip() for t in (char.tags or "").split(",") if t.strip()]
    return {
        "spec": "chara_card_v2",
        "spec_version": "2.0",
        "data": {
            "name": char.name,
            "description": char.personality or "",
            "personality": char.tagline or "",
            "scenario": char.scenario or "",
            "first_mes": char.greeting_message or "",
            "mes_example": char.example_dialogues or "",
            "system_prompt": char.system_prompt_suffix or "",
            "tags": tags,
            "creator_notes": char.appearance or "",
            "character_version": "1.0",
            "extensions": {
                "sweetsin": {
                    "content_rating": char.content_rating.value if char.content_rating else "sfw",
                    "appearance": char.appearance or "",
                    "speech_pattern": getattr(char, 'speech_pattern', None) or "",
                    "tagline": char.tagline or "",
                }
            },
        },
    }


def card_to_character_data(card: dict) -> dict:
    """Parse a SillyTavern character card v2 (or v1) into character fields."""
    # Support both v2 (data.X) and v1 (top-level X)
    data = card.get("data", card)

    extensions = data.get("extensions", {})
    sweetsin_ext = extensions.get("sweetsin", {})

    # Map fields
    name = data.get("name") or data.get("char_name") or "Imported Character"
    personality = data.get("description") or data.get("char_persona") or ""
    tagline = sweetsin_ext.get("tagline") or data.get("personality") or ""
    scenario = data.get("scenario") or data.get("world_scenario") or ""
    greeting = data.get("first_mes") or data.get("char_greeting") or "Hello!"
    example_dialogues = data.get("mes_example") or data.get("example_dialogue") or ""
    system_prompt = data.get("system_prompt") or data.get("post_history_instructions") or ""
    appearance = sweetsin_ext.get("appearance") or data.get("creator_notes") or ""
    speech_pattern = sweetsin_ext.get("speech_pattern") or ""

    # Tags
    tags_raw = data.get("tags", [])
    if isinstance(tags_raw, list):
        tags_str = ",".join(str(t) for t in tags_raw if t)
    else:
        tags_str = str(tags_raw) if tags_raw else ""

    # Content rating
    content_rating = sweetsin_ext.get("content_rating", "sfw")
    if content_rating not in ("sfw", "moderate", "nsfw"):
        content_rating = "sfw"

    return {
        "name": name[:100],
        "tagline": tagline[:200] if tagline else None,
        "personality": personality,
        "scenario": scenario if scenario else None,
        "greeting_message": greeting,
        "example_dialogues": example_dialogues if example_dialogues else None,
        "system_prompt_suffix": system_prompt if system_prompt else None,
        "appearance": appearance if appearance else None,
        "speech_pattern": speech_pattern if speech_pattern else None,
        "tags": tags_str,
        "content_rating": content_rating,
        "is_public": True,
    }
