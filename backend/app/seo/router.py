import json
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.db.models import Character
from app.seo.jsonld import (
    character_jsonld, website_jsonld, faq_jsonld,
    breadcrumb_jsonld, collection_jsonld, SITE_URL,
)

router = APIRouter(prefix="/api/seo", tags=["seo"])

LANGS = ["en", "es", "ru"]

# Tag slug → search values (match characters in any language)
TAG_PAGES = [
    {
        "slug": "fantasy",
        "search": ["фэнтези", "fantasy", "fantasía"],
        "labels": {"en": "Fantasy", "es": "Fantasía", "ru": "Фэнтези"},
        "descriptions": {
            "en": "Explore fantasy AI characters — elves, mages, dragons, and mythical worlds. Immersive roleplay without limits.",
            "es": "Explora personajes de fantasía — elfos, magos, dragones y mundos míticos. Roleplay inmersivo sin límites.",
            "ru": "Фэнтезийные AI-персонажи — эльфы, маги, драконы и мифические миры. Иммерсивный ролеплей без ограничений.",
        },
    },
    {
        "slug": "romance",
        "search": ["романтика", "romance"],
        "labels": {"en": "Romance", "es": "Romance", "ru": "Романтика"},
        "descriptions": {
            "en": "Chat with romantic AI characters — love stories, dating simulation, and intimate conversations.",
            "es": "Chatea con personajes románticos — historias de amor, simulación de citas y conversaciones íntimas.",
            "ru": "Романтические AI-персонажи — любовные истории, симулятор свиданий и интимные разговоры.",
        },
    },
    {
        "slug": "anime",
        "search": ["аниме", "anime"],
        "labels": {"en": "Anime", "es": "Anime", "ru": "Аниме"},
        "descriptions": {
            "en": "Anime-inspired AI characters — waifu, shonen heroes, isekai adventures. Your favorite anime worlds come alive.",
            "es": "Personajes AI inspirados en anime — waifu, héroes shonen, aventuras isekai. Tus mundos anime favoritos cobran vida.",
            "ru": "Аниме AI-персонажи — вайфу, сёнэн-герои, исекай-приключения. Твои любимые аниме-миры оживают.",
        },
    },
    {
        "slug": "modern",
        "search": ["современность", "modern", "moderno", "реалистичный"],
        "labels": {"en": "Modern", "es": "Moderno", "ru": "Современность"},
        "descriptions": {
            "en": "Modern-day AI characters — realistic scenarios, everyday life, contemporary settings and stories.",
            "es": "Personajes AI modernos — escenarios realistas, vida cotidiana, entornos y historias contemporáneas.",
            "ru": "Современные AI-персонажи — реалистичные сценарии, повседневная жизнь, актуальные истории.",
        },
    },
]


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


def _hreflang_tags(path: str) -> str:
    """Generate hreflang link tags for all languages. path should NOT include lang prefix."""
    tags = []
    for l in LANGS:
        url = f"{SITE_URL}/{l}{path}" if path else f"{SITE_URL}/{l}"
        tags.append(f'<link rel="alternate" hreflang="{l}" href="{url}">')
    tags.append(f'<link rel="alternate" hreflang="x-default" href="{SITE_URL}/en{path}">')
    return "\n".join(tags)


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
    canonical = f"{SITE_URL}/{lang}/c/{slug}"

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
{_hreflang_tags(f"/c/{slug}")}
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


@router.get("/tags/{slug}", response_class=HTMLResponse)
async def prerender_tag(
    slug: str,
    lang: str = Query("en"),
    db: AsyncSession = Depends(get_db),
):
    tag_config = next((t for t in TAG_PAGES if t["slug"] == slug), None)
    if not tag_config:
        return HTMLResponse("<html><body><h1>Not Found</h1></body></html>", status_code=404)

    label = tag_config["labels"].get(lang, tag_config["labels"]["en"])
    description = tag_config["descriptions"].get(lang, tag_config["descriptions"]["en"])
    search_values = tag_config["search"]

    # Build OR filter for multiple tag values
    from sqlalchemy import or_
    tag_filters = or_(*[Character.tags.contains(v) for v in search_values])

    result = await db.execute(
        select(Character)
        .where(Character.is_public == True, Character.slug.isnot(None), tag_filters)
        .order_by(Character.chat_count.desc())
        .limit(50)
    )
    characters = result.scalars().all()

    canonical = f"{SITE_URL}/{lang}/tags/{slug}"
    title = f"{label} — AI Characters | SweetSin"

    char_links = []
    for c in characters:
        name = _escape(c.name)
        tagline = _escape(c.tagline or "")
        url = f"{SITE_URL}/{lang}/c/{c.slug}"
        char_links.append(f'<li><a href="{url}">{name}</a> — {tagline}</li>')

    ld_collection = json.dumps(
        collection_jsonld(label, slug, lang, len(characters)), ensure_ascii=False
    )
    ld_breadcrumb = json.dumps(breadcrumb_jsonld([
        ("SweetSin", SITE_URL),
        (label, None),
    ]), ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="{_escape(lang)}">
<head>
<meta charset="UTF-8">
<title>{_escape(title)}</title>
<meta name="description" content="{_escape(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{_escape(label)} — AI Characters">
<meta property="og:description" content="{_escape(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="SweetSin">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{_escape(label)} — AI Characters">
<meta name="twitter:description" content="{_escape(description)}">
{_hreflang_tags(f"/tags/{slug}")}
<script type="application/ld+json">{ld_collection}</script>
<script type="application/ld+json">{ld_breadcrumb}</script>
</head>
<body>
<h1>{_escape(label)} — AI Characters</h1>
<p>{_escape(description)}</p>
<h2>Characters</h2>
<ul>
{"".join(char_links)}
</ul>
<a href="{SITE_URL}/{lang}">Back to SweetSin</a>
</body>
</html>"""
    return HTMLResponse(html)


@router.get("/faq", response_class=HTMLResponse)
async def prerender_faq(lang: str = Query("en")):
    # FAQ Q&A pairs per language
    _faq = {
        "en": [
            ("Is SweetSin free?", "Yes! Core features are free. We offer multiple free providers."),
            ("What models are available?", "We support OpenRouter, Groq, Cerebras, Together, DeepSeek, and direct API access to Claude, GPT-4o, and Gemini."),
            ("Can I create NSFW content?", "Yes, for users 18+. You can set content ratings per character. Some models may have content restrictions."),
            ("How do I create a character?", "Click 'Create' in the header. You can build manually or paste text to auto-generate."),
            ("Is my chat history private?", "Yes. Your conversations are private and only visible to you."),
            ("Can I delete my data?", "Yes. Go to Profile and use 'Delete Account' in the Danger Zone section."),
        ],
        "es": [
            ("¿Es SweetSin gratis?", "¡Sí! Las funciones principales son gratuitas. Ofrecemos múltiples proveedores gratuitos."),
            ("¿Qué modelos están disponibles?", "Soportamos OpenRouter, Groq, Cerebras, Together, DeepSeek y acceso directo a Claude, GPT-4o y Gemini."),
            ("¿Puedo crear contenido NSFW?", "Sí, para usuarios mayores de 18 años. Puedes establecer clasificaciones de contenido por personaje."),
            ("¿Cómo creo un personaje?", "Haz clic en 'Crear' en el encabezado. Puedes construir manualmente o pegar texto para generar automáticamente."),
            ("¿Mi historial de chat es privado?", "Sí. Tus conversaciones son privadas y solo visibles para ti."),
            ("¿Puedo eliminar mis datos?", "Sí. Ve a Perfil y usa 'Eliminar cuenta' en la sección Zona de Peligro."),
        ],
        "ru": [
            ("SweetSin бесплатный?", "Да! Основные функции бесплатны. Мы предлагаем несколько бесплатных провайдеров."),
            ("Какие модели доступны?", "Поддерживаем OpenRouter, Groq, Cerebras, Together, DeepSeek и прямой доступ к Claude, GPT-4o и Gemini."),
            ("Можно ли создавать NSFW-контент?", "Да, для пользователей 18+. Можно задать рейтинг контента для каждого персонажа."),
            ("Как создать персонажа?", "Нажмите «Создать» в шапке. Можно создать вручную или вставить текст для автоматической генерации."),
            ("Мой чат приватный?", "Да. Ваши разговоры приватны и видны только вам."),
            ("Можно ли удалить данные?", "Да. Зайдите в Профиль → «Удалить аккаунт» в разделе «Опасная зона»."),
        ],
    }
    pairs = _faq.get(lang, _faq["en"])
    canonical = f"{SITE_URL}/{lang}/faq"

    qa_html = "\n".join(
        f"<h3>{_escape(q)}</h3><p>{_escape(a)}</p>" for q, a in pairs
    )
    ld_faq = json.dumps(faq_jsonld(pairs), ensure_ascii=False)
    ld_breadcrumb = json.dumps(breadcrumb_jsonld([
        ("SweetSin", SITE_URL),
        ("FAQ", None),
    ]), ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="{_escape(lang)}">
<head>
<meta charset="UTF-8">
<title>FAQ | SweetSin</title>
<meta name="description" content="Frequently asked questions about SweetSin — AI character chat, roleplay, and creating characters.">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="FAQ — SweetSin">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
{_hreflang_tags("/faq")}
<script type="application/ld+json">{ld_faq}</script>
<script type="application/ld+json">{ld_breadcrumb}</script>
</head>
<body>
<h1>Frequently Asked Questions</h1>
{qa_html}
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
        url = f"{SITE_URL}/{lang}/c/{c.slug}"
        char_links.append(f'<li><a href="{url}">{name}</a> — {tagline}</li>')

    canonical = f"{SITE_URL}/{lang}"

    html = f"""<!DOCTYPE html>
<html lang="{_escape(lang)}">
<head>
<meta charset="UTF-8">
<title>SweetSin — AI Character Chat | Roleplay &amp; Fantasy</title>
<meta name="description" content="Chat with unique AI characters without limits. Immersive roleplay, uncensored conversations, and endless fantasy.">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="SweetSin — Where Fantasy Comes Alive">
<meta property="og:description" content="AI Character Chat Platform. Immersive roleplay, uncensored conversations, no limits.">
<meta property="og:image" content="{SITE_URL}/og-image.svg">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
{_hreflang_tags("")}
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

    def alternates(path: str) -> str:
        """xhtml:link alternates for all languages."""
        links = []
        for l in LANGS:
            url = f"{SITE_URL}/{l}{path}" if path else f"{SITE_URL}/{l}"
            links.append(f'<xhtml:link rel="alternate" hreflang="{l}" href="{url}"/>')
        links.append(f'<xhtml:link rel="alternate" hreflang="x-default" href="{SITE_URL}/en{path}"/>')
        return "".join(links)

    urls = []

    # Static pages × languages
    static_pages = [
        ("", "daily", "1.0", now),
        ("/about", "monthly", "0.3", None),
        ("/terms", "monthly", "0.2", None),
        ("/privacy", "monthly", "0.2", None),
        ("/faq", "monthly", "0.3", None),
    ]
    # Tag landing pages
    for tp in TAG_PAGES:
        static_pages.append((f"/tags/{tp['slug']}", "weekly", "0.7", now))
    for path, freq, prio, lastmod in static_pages:
        for l in LANGS:
            loc = f"{SITE_URL}/{l}{path}" if path else f"{SITE_URL}/{l}"
            lm = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
            urls.append(
                f"<url><loc>{loc}</loc>{lm}"
                f"<changefreq>{freq}</changefreq><priority>{prio}</priority>"
                f"{alternates(path)}</url>"
            )

    # Character pages × languages
    for slug, updated_at in characters:
        lastmod = updated_at.strftime("%Y-%m-%d") if updated_at else now
        path = f"/c/{slug}"
        for l in LANGS:
            urls.append(
                f"<url><loc>{SITE_URL}/{l}{path}</loc><lastmod>{lastmod}</lastmod>"
                f"<changefreq>weekly</changefreq><priority>0.8</priority>"
                f"{alternates(path)}</url>"
            )

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
{"".join(urls)}
</urlset>"""
    return Response(content=xml, media_type="application/xml")


@router.get("/feed.xml")
async def rss_feed(db: AsyncSession = Depends(get_db)):
    """RSS 2.0 feed of latest public characters."""
    result = await db.execute(
        select(Character)
        .where(Character.is_public == True, Character.slug.isnot(None))
        .order_by(Character.created_at.desc())
        .limit(30)
    )
    characters = result.scalars().all()

    now = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    items = []
    for c in characters:
        name = _escape(c.name)
        tagline = _escape(c.tagline or "")
        desc = _escape(_truncate(c.scenario or c.tagline or "", 300))
        link = f"{SITE_URL}/en/c/{c.slug}"
        pub_date = c.created_at.strftime("%a, %d %b %Y %H:%M:%S +0000") if c.created_at else now
        avatar = ""
        if c.avatar_url:
            avatar_url = c.avatar_url if c.avatar_url.startswith("http") else f"{SITE_URL}{c.avatar_url}"
            avatar = f'<enclosure url="{_escape(avatar_url)}" type="image/webp" />'
        tags_xml = "".join(f"<category>{_escape(t)}</category>" for t in (c.tags.split(",") if c.tags else []) if t.strip())
        items.append(f"""<item>
<title>{name}{f' — {tagline}' if tagline else ''}</title>
<link>{link}</link>
<guid isPermaLink="true">{link}</guid>
<description>{desc}</description>
<pubDate>{pub_date}</pubDate>
{avatar}
{tags_xml}
</item>""")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
<title>SweetSin — New AI Characters</title>
<link>{SITE_URL}</link>
<description>Latest AI characters for roleplay and chat on SweetSin</description>
<language>en</language>
<lastBuildDate>{now}</lastBuildDate>
<atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml" />
{"".join(items)}
</channel>
</rss>"""
    return Response(content=xml, media_type="application/rss+xml; charset=utf-8")


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
