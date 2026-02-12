from app.db.models import Character


def character_to_dict(c: Character) -> dict:
    tr = getattr(c, '_active_translations', None)
    d = {
        "id": c.id,
        "creator_id": c.creator_id,
        "name": tr["name"] if tr and "name" in tr else c.name,
        "tagline": tr["tagline"] if tr and "tagline" in tr else c.tagline,
        "avatar_url": c.avatar_url,
        "personality": c.personality,
        "scenario": c.scenario,
        "greeting_message": c.greeting_message,
        "example_dialogues": c.example_dialogues,
        "appearance": getattr(c, 'appearance', None),
        "content_rating": c.content_rating.value if hasattr(c.content_rating, 'value') else (c.content_rating or "sfw"),
        "system_prompt_suffix": c.system_prompt_suffix,
        "tags": tr["tags"] if tr and "tags" in tr else ([t for t in c.tags.split(",") if t] if c.tags else []),
        "structured_tags": [t for t in (getattr(c, 'structured_tags', '') or '').split(",") if t],
        "is_public": c.is_public,
        "chat_count": c.chat_count,
        "like_count": c.like_count,
        "preferred_model": c.preferred_model,
        "max_tokens": getattr(c, 'max_tokens', None) or 2048,
        "response_length": getattr(c, 'response_length', None) or "long",
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }
    if c.creator:
        d["profiles"] = {
            "username": c.creator.username,
            "display_name": c.creator.display_name,
            "avatar_url": c.creator.avatar_url,
        }
    return d
