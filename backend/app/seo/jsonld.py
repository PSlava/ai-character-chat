from app.db.models import Character

SITE_URL = "https://sweetsin.cc"


def character_jsonld(c: Character, language: str = "en") -> dict:
    tr = getattr(c, '_active_translations', None)
    name = tr["name"] if tr and "name" in tr else c.name
    tagline = tr["tagline"] if tr and "tagline" in tr else (c.tagline or "")
    scenario = tr["scenario"] if tr and "scenario" in tr else (c.scenario or "")
    tags = tr["tags"] if tr and "tags" in tr else ([t for t in c.tags.split(",") if t] if c.tags else [])

    lang = language or "en"
    base_chat = (c.base_chat_count or {}).get(lang, 0)
    chat_count = (c.chat_count or 0) + base_chat

    avatar = c.avatar_url
    if avatar and avatar.startswith("/"):
        avatar = f"{SITE_URL}{avatar}"

    data = {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "name": name,
        "description": tagline or scenario[:160] if scenario else name,
        "url": f"{SITE_URL}/c/{c.slug}" if c.slug else f"{SITE_URL}/character/{c.id}",
        "datePublished": c.created_at.isoformat() if c.created_at else None,
        "dateModified": c.updated_at.isoformat() if c.updated_at else None,
        "keywords": ", ".join(tags) if isinstance(tags, list) else tags,
        "interactionStatistic": {
            "@type": "InteractionCounter",
            "interactionType": "https://schema.org/CommentAction",
            "userInteractionCount": chat_count,
        },
    }
    if avatar:
        data["image"] = avatar
    if c.creator:
        data["author"] = {
            "@type": "Person",
            "name": c.creator.display_name or c.creator.username,
        }
    return {k: v for k, v in data.items() if v is not None}


def website_jsonld() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "SweetSin",
        "url": SITE_URL,
        "description": "AI Character Chat Platform — Roleplay & Fantasy",
    }
