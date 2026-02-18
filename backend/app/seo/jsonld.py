from app.db.models import Character

SITE_URL = "https://sweetsin.cc"


def character_jsonld(c: Character, language: str = "en", vote_count: int = 0) -> dict:
    tr = getattr(c, '_active_translations', None)
    name = tr["name"] if tr and "name" in tr else c.name
    tagline = tr["tagline"] if tr and "tagline" in tr else (c.tagline or "")
    scenario = tr["scenario"] if tr and "scenario" in tr else (c.scenario or "")
    tags = tr["tags"] if tr and "tags" in tr else ([t for t in c.tags.split(",") if t] if c.tags else [])

    lang = language or "en"
    # Real counts only — no inflated base_chat_count (avoid suspicious numbers)
    chat_count = c.chat_count or 0

    avatar = c.avatar_url
    if avatar and avatar.startswith("/"):
        avatar = f"{SITE_URL}{avatar}"

    data = {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "name": name,
        "description": tagline or scenario[:160] if scenario else name,
        "url": f"{SITE_URL}/{lang}/c/{c.slug}" if c.slug else f"{SITE_URL}/character/{c.id}",
        "inLanguage": lang,
        "datePublished": (c.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if c.created_at else None),
        "dateModified": (c.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ") if c.updated_at else None),
        "keywords": ", ".join(tags) if isinstance(tags, list) else tags,
        "isPartOf": {"@type": "WebSite", "name": "SweetSin", "url": SITE_URL},
    }
    if chat_count > 0:
        data["interactionStatistic"] = {
            "@type": "InteractionCounter",
            "interactionType": "https://schema.org/CommentAction",
            "userInteractionCount": chat_count,
        }
    if avatar:
        data["image"] = avatar
    if c.creator:
        data["author"] = {
            "@type": "Person",
            "name": c.creator.display_name or c.creator.username,
        }
    # AggregateRating from votes — only if enough engagement
    like_count = getattr(c, "like_count", 0) or 0
    v_score = getattr(c, "vote_score", 0) or 0
    total_votes = max(vote_count, 1)
    if like_count >= 3:
        ratio = max(-1.0, min(1.0, v_score / total_votes))
        rating_value = round(4.0 + ratio, 1)
        rating_value = max(3.0, min(5.0, rating_value))
        data["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": rating_value,
            "bestRating": 5,
            "worstRating": 1,
            "ratingCount": like_count,
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


def software_application_jsonld() -> dict:
    return {
        "@type": "SoftwareApplication",
        "name": "SweetSin",
        "url": SITE_URL,
        "applicationCategory": "EntertainmentApplication",
        "operatingSystem": "Web",
        "description": "AI Character Chat — Roleplay & Fantasy with 9 AI providers",
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD",
        },
    }


def faq_jsonld(qa_pairs: list[tuple[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in qa_pairs
        ],
    }


def breadcrumb_jsonld(items: list[tuple[str, str | None]]) -> dict:
    """items = [(name, url), ...]. Last item may have url=None."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": name,
                **({"item": url} if url else {}),
            }
            for i, (name, url) in enumerate(items)
        ],
    }


def collection_jsonld(
    tag_name: str, tag_slug: str, language: str, total: int
) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"{tag_name} — AI Characters",
        "url": f"{SITE_URL}/{language}/tags/{tag_slug}",
        "description": f"Chat with {tag_name} AI characters on SweetSin. {total} characters available.",
        "inLanguage": language,
        "numberOfItems": total,
        "isPartOf": {"@type": "WebSite", "name": "SweetSin", "url": SITE_URL},
    }
