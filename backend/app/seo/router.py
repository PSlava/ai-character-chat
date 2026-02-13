import json
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.db.models import Character
from app.seo.jsonld import character_jsonld, website_jsonld, SITE_URL

router = APIRouter(prefix="/api/seo", tags=["seo"])


def _escape(text: str | None) -> str:
    if not text:
        return ""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _truncate(text: str | None, length: int = 160) -> str:
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    if len(text) <= length:
        return text
    return text[:length - 3] + "..."


@router.get("/c/{slug}", response_class=HTMLResponse)
async def prerender_character(
    slug: str,
    lang: str = Query("en"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Character)
        .options(selectinload(Character.creator))
        .where(Character.slug == slug, Character.is_public == True)
    )
    character = result.scalar_one_or_none()
    if not character:
        return HTMLResponse("<html><body><h1>Not Found</h1></body></html>", status_code=404)

    # Apply translations if available
    tr = (character.translations or {}).get(lang)
    if tr:
        character._active_translations = tr

    name = _escape(tr["name"] if tr and "name" in tr else character.name)
    tagline = _escape(tr["tagline"] if tr and "tagline" in tr else (character.tagline or ""))
    scenario = tr["scenario"] if tr and "scenario" in tr else (character.scenario or "")
    appearance = tr["appearance"] if tr and "appearance" in tr else (character.appearance or "")
    greeting = tr["greeting_message"] if tr and "greeting_message" in tr else (character.greeting_message or "")
    tags = tr["tags"] if tr and "tags" in tr else ([t for t in character.tags.split(",") if t] if character.tags else [])

    description = _escape(_truncate(scenario or tagline))
    keywords = _escape(", ".join(tags) if isinstance(tags, list) else tags)
    canonical = f"{SITE_URL}/c/{slug}"

    avatar = character.avatar_url or ""
    if avatar and avatar.startswith("/"):
        avatar = f"{SITE_URL}{avatar}"

    title = f"{name} — {tagline}" if tagline else name
    title_full = f"{title} | SweetSin"

    ld_json = json.dumps(character_jsonld(character, lang), ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="{_escape(lang)}">
<head>
<meta charset="UTF-8">
<title>{_escape(title_full)}</title>
<meta name="description" content="{description}">
<meta name="keywords" content="{keywords}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{_escape(title)}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="{_escape(avatar)}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="SweetSin">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{_escape(title)}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{_escape(avatar)}">
<link rel="alternate" hreflang="en" href="{canonical}">
<link rel="alternate" hreflang="es" href="{canonical}">
<link rel="alternate" hreflang="ru" href="{canonical}">
<link rel="alternate" hreflang="x-default" href="{canonical}">
<script type="application/ld+json">{ld_json}</script>
</head>
<body>
<h1>{_escape(name)}</h1>
{f'<p>{_escape(tagline)}</p>' if tagline else ''}
{f'<p>{_escape(_truncate(scenario, 500))}</p>' if scenario else ''}
{f'<p>{_escape(_truncate(appearance, 300))}</p>' if appearance else ''}
{f'<p>{_escape(_truncate(greeting, 300))}</p>' if greeting else ''}
<p>Tags: {_escape(", ".join(tags) if isinstance(tags, list) else tags)}</p>
<a href="{canonical}">Chat with {_escape(name)} on SweetSin</a>
</body>
</html>"""
    return HTMLResponse(html)


@router.get("/home", response_class=HTMLResponse)
async def prerender_home(
    lang: str = Query("en"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Character)
        .where(Character.is_public == True, Character.slug.isnot(None))
        .order_by(Character.chat_count.desc())
        .limit(50)
    )
    characters = result.scalars().all()

    ld_json = json.dumps(website_jsonld(), ensure_ascii=False)

    char_links = []
    for c in characters:
        name = _escape(c.name)
        tagline = _escape(c.tagline or "")
        url = f"{SITE_URL}/c/{c.slug}"
        char_links.append(f'<li><a href="{url}">{name}</a> — {tagline}</li>')

    html = f"""<!DOCTYPE html>
<html lang="{_escape(lang)}">
<head>
<meta charset="UTF-8">
<title>SweetSin — AI Character Chat | Roleplay &amp; Fantasy</title>
<meta name="description" content="Chat with unique AI characters without limits. Immersive roleplay, uncensored conversations, and endless fantasy.">
<link rel="canonical" href="{SITE_URL}/">
<meta property="og:title" content="SweetSin — Where Fantasy Comes Alive">
<meta property="og:description" content="AI Character Chat Platform. Immersive roleplay, uncensored conversations, no limits.">
<meta property="og:image" content="{SITE_URL}/og-image.svg">
<meta property="og:url" content="{SITE_URL}/">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" hreflang="en" href="{SITE_URL}/">
<link rel="alternate" hreflang="es" href="{SITE_URL}/">
<link rel="alternate" hreflang="ru" href="{SITE_URL}/">
<link rel="alternate" hreflang="x-default" href="{SITE_URL}/">
<script type="application/ld+json">{ld_json}</script>
</head>
<body>
<h1>SweetSin — AI Character Chat</h1>
<p>Chat with unique AI characters. Immersive roleplay, uncensored conversations, and endless fantasy.</p>
<h2>Characters</h2>
<ul>
{"".join(char_links)}
</ul>
</body>
</html>"""
    return HTMLResponse(html)


@router.get("/sitemap.xml")
async def sitemap(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Character.slug, Character.updated_at)
        .where(Character.is_public == True, Character.slug.isnot(None))
        .order_by(Character.updated_at.desc())
    )
    characters = result.all()

    now = datetime.utcnow().strftime("%Y-%m-%d")
    urls = [
        f'<url><loc>{SITE_URL}/</loc><lastmod>{now}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>',
        f'<url><loc>{SITE_URL}/about</loc><changefreq>monthly</changefreq><priority>0.3</priority></url>',
        f'<url><loc>{SITE_URL}/terms</loc><changefreq>monthly</changefreq><priority>0.2</priority></url>',
        f'<url><loc>{SITE_URL}/privacy</loc><changefreq>monthly</changefreq><priority>0.2</priority></url>',
        f'<url><loc>{SITE_URL}/faq</loc><changefreq>monthly</changefreq><priority>0.3</priority></url>',
    ]
    for slug, updated_at in characters:
        lastmod = updated_at.strftime("%Y-%m-%d") if updated_at else now
        urls.append(
            f'<url><loc>{SITE_URL}/c/{slug}</loc><lastmod>{lastmod}</lastmod>'
            f'<changefreq>weekly</changefreq><priority>0.8</priority></url>'
        )

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{"".join(urls)}
</urlset>"""
    return Response(content=xml, media_type="application/xml")


@router.get("/robots.txt")
async def robots():
    content = f"""User-agent: *
Allow: /
Disallow: /api/
Disallow: /chat/
Disallow: /profile
Disallow: /admin/
Disallow: /favorites
Disallow: /create
Disallow: /auth
Sitemap: {SITE_URL}/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")
