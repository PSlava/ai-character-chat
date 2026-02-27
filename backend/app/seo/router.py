import json
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.db.models import Character, Vote
from app.config import settings
from app.seo.jsonld import (
    character_jsonld, website_jsonld, software_application_jsonld,
    faq_jsonld, breadcrumb_jsonld, collection_jsonld, SITE_URL, SITE_NAME,
)


def _brand(text: str) -> str:
    """Replace hardcoded 'SweetSin' with actual site name for multi-site support."""
    return text.replace("SweetSin", SITE_NAME)

router = APIRouter(prefix="/api/seo", tags=["seo"])

LANGS = ["en", "es", "ru", "fr", "de", "pt", "it"]

# Tag slug → search values (match characters in any language)
TAG_PAGES = [
    {
        "slug": "fantasy",
        "search": ["фэнтези", "fantasy", "fantasía"],
        "labels": {"en": "Fantasy", "es": "Fantasía", "ru": "Фэнтези", "fr": "Fantaisie", "de": "Fantasy", "pt": "Fantasia", "it": "Fantasy"},
        "descriptions": {
            "en": "Explore fantasy AI characters — elves, mages, dragons, and mythical worlds. Immersive roleplay without limits.",
            "es": "Explora personajes de fantasía — elfos, magos, dragones y mundos míticos. Roleplay inmersivo sin límites.",
            "ru": "Фэнтезийные AI-персонажи — эльфы, маги, драконы и мифические миры. Иммерсивный ролеплей без ограничений.",
            "fr": "Explorez des personnages IA fantastiques — elfes, mages, dragons et mondes mythiques. Jeu de rôle immersif sans limites.",
            "de": "Entdecke Fantasy-KI-Charaktere — Elfen, Magier, Drachen und mythische Welten. Immersives Rollenspiel ohne Grenzen.",
            "pt": "Explore personagens de fantasia com IA — elfos, magos, dragões e mundos míticos. Roleplay imersivo sem limites.",
            "it": "Esplora personaggi fantasy IA — elfi, maghi, draghi e mondi mitici. Gioco di ruolo immersivo senza limiti.",
        },
    },
    {
        "slug": "romance",
        "search": ["романтика", "romance"],
        "labels": {"en": "Romance", "es": "Romance", "ru": "Романтика", "fr": "Romance", "de": "Romantik", "pt": "Romance", "it": "Romantico"},
        "descriptions": {
            "en": "Chat with romantic AI characters — love stories, dating simulation, and intimate conversations.",
            "es": "Chatea con personajes románticos — historias de amor, simulación de citas y conversaciones íntimas.",
            "ru": "Романтические AI-персонажи — любовные истории, симулятор свиданий и интимные разговоры.",
            "fr": "Chattez avec des personnages IA romantiques — histoires d'amour, simulation de rendez-vous et conversations intimes.",
            "de": "Chatte mit romantischen KI-Charakteren — Liebesgeschichten, Dating-Simulation und intime Gespräche.",
            "pt": "Converse com personagens românticos de IA — histórias de amor, simulação de encontros e conversas íntimas.",
            "it": "Chatta con personaggi IA romantici — storie d'amore, simulazione di appuntamenti e conversazioni intime.",
        },
    },
    {
        "slug": "anime",
        "search": ["аниме", "anime"],
        "labels": {"en": "Anime", "es": "Anime", "ru": "Аниме", "fr": "Anime", "de": "Anime", "pt": "Anime", "it": "Anime"},
        "descriptions": {
            "en": "Anime-inspired AI characters — waifu, shonen heroes, isekai adventures. Your favorite anime worlds come alive.",
            "es": "Personajes AI inspirados en anime — waifu, héroes shonen, aventuras isekai. Tus mundos anime favoritos cobran vida.",
            "ru": "Аниме AI-персонажи — вайфу, сёнэн-герои, исекай-приключения. Твои любимые аниме-миры оживают.",
            "fr": "Personnages IA inspirés de l'anime — waifu, héros shonen, aventures isekai. Vos mondes anime préférés prennent vie.",
            "de": "Anime-inspirierte KI-Charaktere — Waifu, Shonen-Helden, Isekai-Abenteuer. Deine liebsten Anime-Welten erwachen zum Leben.",
            "pt": "Personagens de IA inspirados em anime — waifu, heróis shonen, aventuras isekai. Seus mundos anime favoritos ganham vida.",
            "it": "Personaggi IA ispirati agli anime — waifu, eroi shonen, avventure isekai. I tuoi mondi anime preferiti prendono vita.",
        },
    },
    {
        "slug": "modern",
        "search": ["современность", "modern", "moderno", "реалистичный"],
        "labels": {"en": "Modern", "es": "Moderno", "ru": "Современность", "fr": "Moderne", "de": "Modern", "pt": "Moderno", "it": "Moderno"},
        "descriptions": {
            "en": "Modern-day AI characters — realistic scenarios, everyday life, contemporary settings and stories.",
            "es": "Personajes AI modernos — escenarios realistas, vida cotidiana, entornos y historias contemporáneas.",
            "ru": "Современные AI-персонажи — реалистичные сценарии, повседневная жизнь, актуальные истории.",
            "fr": "Personnages IA modernes — scénarios réalistes, vie quotidienne, contextes et histoires contemporains.",
            "de": "Moderne KI-Charaktere — realistische Szenarien, Alltagsleben, zeitgenössische Settings und Geschichten.",
            "pt": "Personagens de IA modernos — cenários realistas, vida cotidiana, ambientes e histórias contemporâneas.",
            "it": "Personaggi IA moderni — scenari realistici, vita quotidiana, ambientazioni e storie contemporanee.",
        },
    },
    {
        "slug": "horror",
        "search": ["horror", "хоррор", "ужасы", "terror"],
        "labels": {"en": "Horror", "es": "Terror", "ru": "Хоррор", "fr": "Horreur", "de": "Horror", "pt": "Terror", "it": "Horror"},
        "descriptions": {
            "en": "Horror interactive fiction — dark atmosphere, suspense, and terrifying choices. Survive the night.",
            "es": "Ficcion interactiva de terror — atmosfera oscura, suspenso y decisiones aterradoras. Sobrevive la noche.",
            "ru": "Хоррор интерактивная литература — темная атмосфера, саспенс и пугающий выбор.",
            "fr": "Fiction interactive d'horreur — atmosphere sombre, suspense et choix terrifiants. Survivez a la nuit.",
            "de": "Horror interaktive Fiktion — dunkle Atmosphare, Spannung und erschreckende Entscheidungen. Uberlebe die Nacht.",
            "pt": "Ficcao interativa de terror — atmosfera sombria, suspense e escolhas aterrorizantes. Sobreviva a noite.",
            "it": "Narrativa interattiva horror — atmosfera cupa, suspense e scelte terrificanti. Sopravvivi alla notte.",
        },
    },
    {
        "slug": "sci-fi",
        "search": ["sci-fi", "sci_fi", "научная фантастика", "ciencia ficcion", "science-fiction"],
        "labels": {"en": "Sci-Fi", "es": "Ciencia Ficcion", "ru": "Фантастика", "fr": "Science-Fiction", "de": "Sci-Fi", "pt": "Ficcao Cientifica", "it": "Fantascienza"},
        "descriptions": {
            "en": "Sci-fi interactive fiction — space exploration, futuristic tech, and cosmic mysteries await.",
            "es": "Ficcion interactiva de ciencia ficcion — exploracion espacial, tecnologia futurista y misterios cosmicos.",
            "ru": "Научно-фантастическая литература — космос, технологии будущего и космические тайны.",
            "fr": "Fiction interactive de science-fiction — exploration spatiale, technologies futuristes et mysteres cosmiques.",
            "de": "Sci-Fi interaktive Fiktion — Weltraumerkundung, futuristische Technologie und kosmische Geheimnisse.",
            "pt": "Ficcao interativa de ficcao cientifica — exploracao espacial, tecnologia futurista e misterios cosmicos.",
            "it": "Narrativa interattiva fantascientifica — esplorazione spaziale, tecnologia futuristica e misteri cosmici.",
        },
    },
    {
        "slug": "mystery",
        "search": ["mystery", "детектив", "тайна", "misterio", "detective"],
        "labels": {"en": "Mystery", "es": "Misterio", "ru": "Детектив", "fr": "Mystere", "de": "Krimi", "pt": "Misterio", "it": "Giallo"},
        "descriptions": {
            "en": "Mystery interactive fiction — solve puzzles, uncover clues, and crack the case.",
            "es": "Ficcion interactiva de misterio — resuelve acertijos, descubre pistas y resuelve el caso.",
            "ru": "Детективная литература — разгадывайте загадки, находите улики, раскрывайте дела.",
            "fr": "Fiction interactive de mystere — resolvez des enigmes, decouvrez des indices et elucidez l'affaire.",
            "de": "Krimi interaktive Fiktion — lose Ratsel, finde Hinweise und klare den Fall.",
            "pt": "Ficcao interativa de misterio — resolva enigmas, descubra pistas e desvende o caso.",
            "it": "Narrativa interattiva gialla — risolvi enigmi, scopri indizi e risolvi il caso.",
        },
    },
    {
        "slug": "adventure",
        "search": ["adventure", "приключения", "aventura", "exploration"],
        "labels": {"en": "Adventure", "es": "Aventura", "ru": "Приключения", "fr": "Aventure", "de": "Abenteuer", "pt": "Aventura", "it": "Avventura"},
        "descriptions": {
            "en": "Adventure interactive fiction — explore unknown lands, face challenges, and discover treasures.",
            "es": "Ficcion interactiva de aventura — explora tierras desconocidas, enfrenta desafios y descubre tesoros.",
            "ru": "Приключенческая литература — исследуйте неизвестные земли, преодолевайте испытания.",
            "fr": "Fiction interactive d'aventure — explorez des terres inconnues, affrontez des defis et decouvrez des tresors.",
            "de": "Abenteuer interaktive Fiktion — erkunde unbekannte Lander, stelle dich Herausforderungen und entdecke Schatze.",
            "pt": "Ficcao interativa de aventura — explore terras desconhecidas, enfrente desafios e descubra tesouros.",
            "it": "Narrativa interattiva d'avventura — esplora terre sconosciute, affronta sfide e scopri tesori.",
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
    personality = tr.get("personality", "") if tr else (character.personality or "")
    appearance = tr["appearance"] if tr and "appearance" in tr else (character.appearance or "")
    greeting = tr["greeting_message"] if tr and "greeting_message" in tr else (character.greeting_message or "")
    tags = tr["tags"] if tr and "tags" in tr else ([t for t in character.tags.split(",") if t] if character.tags else [])

    # Build rich meta description: tagline + scenario snippet (120-160 chars target)
    desc_parts = []
    if tagline:
        desc_parts.append(tagline)
    if scenario and scenario != tagline:
        desc_parts.append(scenario)
    description = _escape(_truncate(" — ".join(desc_parts) if desc_parts else name, 160))
    keywords = _escape(", ".join(tags) if isinstance(tags, list) else tags)
    canonical = f"{SITE_URL}/{lang}/c/{slug}"

    avatar = character.avatar_url or ""
    if avatar and avatar.startswith("/"):
        avatar = f"{SITE_URL}{avatar}"

    title = f"{name} — {tagline}" if tagline else name
    title_full = f"{title} | {SITE_NAME}"

    # Check if NSFW — truncate content for bots
    _rating = getattr(character.content_rating, 'value', character.content_rating) or "sfw"
    is_nsfw = _rating == "nsfw"
    if is_nsfw:
        personality = _truncate(personality, 100)
        scenario = _truncate(scenario, 100)
        appearance = ""
        greeting = ""

    # noindex for thin pages: short content without substantial description
    content_length = len(scenario) + len(personality) + len(appearance) + len(greeting)
    noindex = content_length < 100

    # Creator info for E-E-A-T
    creator_name = ""
    if character.creator:
        creator_name = character.creator.display_name or character.creator.username or ""
    date_str = ""
    if character.created_at:
        date_str = character.created_at.strftime("%Y-%m-%d")

    # Count votes for AggregateRating
    vote_result = await db.execute(
        select(func.count()).select_from(Vote).where(Vote.character_id == character.id)
    )
    vote_count = vote_result.scalar() or 0

    from app.characters.service import get_character_rating
    rating_data = await get_character_rating(db, character.id)
    ld_json = json.dumps(character_jsonld(character, lang, vote_count=vote_count, rating_data=rating_data), ensure_ascii=False)
    ld_breadcrumb = json.dumps(breadcrumb_jsonld([
        (SITE_NAME, SITE_URL),
        (name, None),
    ]), ensure_ascii=False)

    # Build body sections — vary order/headings based on slug hash for anti-template
    slug_hash = sum(ord(c) for c in slug) % 6
    _h2_scenario = ["About", "Story", "Background", "Scenario", "Overview", "Setting"][slug_hash]
    _h2_personality = ["Personality", "Character", "Traits", "Nature", "Temperament", "Profile"][slug_hash]
    _h2_appearance = ["Appearance", "Looks", "Description", "Physical", "Visual", "Features"][slug_hash]
    _h2_greeting = ["Greeting", "Introduction", "First Words", "Welcome", "Opening", "Hello"][slug_hash]
    _cta_texts = [
        f"Chat with {_escape(name)} on {SITE_NAME}",
        f"Start a conversation with {_escape(name)}",
        f"Talk to {_escape(name)} now",
        f"Begin your story with {_escape(name)}",
        f"Meet {_escape(name)} on {SITE_NAME}",
        f"Explore {_escape(name)}'s world",
    ]
    cta = _cta_texts[slug_hash]

    # Build sections list — vary ordering based on hash
    sections = []
    if avatar:
        sections.append(f'<img src="{_escape(avatar)}" alt="{_escape(name)}" width="256" height="256">')
    if tagline:
        sections.append(f'<p><em>{_escape(tagline)}</em></p>')

    # Core content sections — vary order for anti-template
    content_blocks = []
    if scenario:
        content_blocks.append(("scenario", f'<h2>{_h2_scenario}</h2><p>{_escape(_truncate(scenario, 500))}</p>'))
    if personality:
        content_blocks.append(("personality", f'<h2>{_h2_personality}</h2><p>{_escape(_truncate(personality, 400))}</p>'))
    if appearance:
        content_blocks.append(("appearance", f'<h2>{_h2_appearance}</h2><p>{_escape(_truncate(appearance, 300))}</p>'))
    if greeting:
        content_blocks.append(("greeting", f'<h2>{_h2_greeting}</h2><p>{_escape(_truncate(greeting, 300))}</p>'))

    # Rotate section order based on hash
    if content_blocks:
        rotation = slug_hash % len(content_blocks)
        content_blocks = content_blocks[rotation:] + content_blocks[:rotation]
    sections.extend(html for _, html in content_blocks)

    # Meta info: creator, date, tags
    meta_parts = []
    if creator_name:
        meta_parts.append(f'Created by {_escape(creator_name)}')
    if date_str:
        meta_parts.append(f'<time datetime="{date_str}">{date_str}</time>')
    if meta_parts:
        sections.append(f'<p>{" | ".join(meta_parts)}</p>')
    if tags:
        sections.append(f'<p>Tags: {_escape(", ".join(tags) if isinstance(tags, list) else tags)}</p>')
    sections.append(f'<a href="{canonical}">{cta}</a>')

    body_html = "\n".join(sections)

    html = f"""<!DOCTYPE html>
<html lang="{_escape(lang)}">
<head>
<meta charset="UTF-8">
<title>{_escape(title_full)}</title>
<meta name="description" content="{description}">
<meta name="keywords" content="{keywords}">
{'<meta name="robots" content="noindex, follow">' if noindex else ''}
{'<meta name="rating" content="adult">' if is_nsfw else ''}
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{_escape(title)}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="{_escape(avatar)}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:locale" content="{lang}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{_escape(title)}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{_escape(avatar)}">
{_hreflang_tags(f"/c/{slug}")}
<script type="application/ld+json">{ld_json}</script>
<script type="application/ld+json">{ld_breadcrumb}</script>
</head>
<body>
<h1>{_escape(name)}</h1>
{body_html}
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
    title = f"{label} — AI Characters | {SITE_NAME}"

    char_links = []
    for c in characters:
        tr = (c.translations or {}).get(lang)
        name = _escape(tr["name"] if tr and "name" in tr else c.name)
        _cr = getattr(c.content_rating, 'value', c.content_rating) or "sfw"
        if _cr == "nsfw":
            tagline = ""
        else:
            tagline = _escape(tr["tagline"] if tr and "tagline" in tr else (c.tagline or ""))
        url = f"{SITE_URL}/{lang}/c/{c.slug}"
        line = f'<li><a href="{url}">{name}</a> — {tagline}</li>' if tagline else f'<li><a href="{url}">{name}</a></li>'
        char_links.append(line)

    ld_collection = json.dumps(
        collection_jsonld(label, slug, lang, len(characters)), ensure_ascii=False
    )
    ld_breadcrumb = json.dumps(breadcrumb_jsonld([
        (SITE_NAME, SITE_URL),
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
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:image" content="{SITE_URL}/og-image.png">
<meta property="og:locale" content="{lang}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{_escape(label)} — AI Characters">
<meta name="twitter:description" content="{_escape(description)}">
<meta name="twitter:image" content="{SITE_URL}/og-image.png">
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
<a href="{SITE_URL}/{lang}">Back to {SITE_NAME}</a>
</body>
</html>"""
    return HTMLResponse(html)


@router.get("/faq", response_class=HTMLResponse)
async def prerender_faq(lang: str = Query("en")):
    # Fiction-mode FAQ (GrimQuill — interactive fiction & D&D)
    _faq_fiction = {
        "en": [
            ("Is GrimQuill free?", "Yes! All adventures and the AI Game Master are completely free. We use multiple AI providers with automatic fallback to ensure the best experience at no cost."),
            ("How does interactive fiction work?", "Choose a story, read the opening scene, and make choices that shape the narrative. The AI generates unique responses based on your decisions — no two playthroughs are the same."),
            ("How does D&D mode work?", "The AI acts as your Game Master running D&D 5e rules. Create a character, explore dungeons, fight monsters, and make decisions. The GM tracks your stats, manages combat, and adapts the story to your choices."),
            ("How does dice rolling work?", "The AI Game Master rolls dice automatically using standard D&D notation (d20, 2d6+3, etc.). Attack rolls, saving throws, ability checks — all resolved with visible dice results that affect the outcome."),
            ("What is the combat tracker?", "During encounters, the GM tracks hit points, armor class, conditions, and turn order. You see your character's status and can make tactical decisions each round."),
            ("Can I create my own adventures?", "Yes! Click 'Create' to build your own interactive fiction story or D&D campaign. Define the setting, characters, and opening scene — the AI handles the rest."),
            ("Is my progress saved?", "Yes. Your chat history and campaign progress are saved automatically. You can return to any adventure and continue where you left off."),
            ("What languages are supported?", "The interface supports English, Spanish, Russian, French, German, Portuguese, and Italian. The AI Game Master responds in whatever language you write in."),
            ("How does the AI Game Master work?", "The GM uses advanced language models to generate narrative responses, manage game mechanics, and adapt to your playstyle. It follows D&D 5e rules while maintaining an engaging story."),
            ("Can I play with friends?", "Currently GrimQuill is designed for solo play — one player with the AI Game Master. Multiplayer campaigns are on our roadmap for future updates."),
            ("What D&D rules are supported?", "GrimQuill follows D&D 5e core rules: ability checks, saving throws, attack rolls, spell slots, conditions, and more. The GM handles the mechanics so you can focus on the adventure."),
            ("Is my data private?", "Yes. Your conversations and campaign data are private and visible only to you. We do not share your data with anyone."),
        ],
        "es": [
            ("¿GrimQuill es gratis?", "¡Sí! Todas las aventuras y el Game Master con IA son completamente gratis. Usamos múltiples proveedores de IA con cambio automático para garantizar la mejor experiencia sin costo."),
            ("¿Cómo funciona la ficción interactiva?", "Elige una historia, lee la escena inicial y toma decisiones que dan forma a la narrativa. La IA genera respuestas únicas basadas en tus decisiones — ninguna partida es igual."),
            ("¿Cómo funciona el modo D&D?", "La IA actúa como tu Game Master siguiendo las reglas de D&D 5e. Crea un personaje, explora mazmorras, lucha contra monstruos y toma decisiones. El GM rastrea tus estadísticas y adapta la historia."),
            ("¿Cómo funcionan las tiradas de dados?", "El Game Master tira dados automáticamente usando notación estándar de D&D (d20, 2d6+3, etc.). Tiradas de ataque, salvación, habilidad — todo se resuelve con resultados visibles."),
            ("¿Qué es el rastreador de combate?", "Durante los encuentros, el GM rastrea puntos de vida, clase de armadura, condiciones y orden de turno. Ves el estado de tu personaje y puedes tomar decisiones tácticas cada ronda."),
            ("¿Puedo crear mis propias aventuras?", "¡Sí! Haz clic en 'Crear' para construir tu propia historia interactiva o campaña de D&D. Define el escenario, los personajes y la escena inicial — la IA se encarga del resto."),
            ("¿Se guarda mi progreso?", "Sí. Tu historial de chat y progreso de campaña se guardan automáticamente. Puedes volver a cualquier aventura y continuar donde lo dejaste."),
            ("¿Qué idiomas están disponibles?", "La interfaz soporta inglés, español, ruso, francés, alemán, portugués e italiano. El Game Master responde en el idioma en que le escribas."),
            ("¿Cómo funciona el Game Master con IA?", "El GM usa modelos de lenguaje avanzados para generar respuestas narrativas, gestionar mecánicas de juego y adaptarse a tu estilo. Sigue las reglas de D&D 5e manteniendo una historia envolvente."),
            ("¿Puedo jugar con amigos?", "Actualmente GrimQuill está diseñado para juego en solitario — un jugador con el Game Master. Las campañas multijugador están en nuestra hoja de ruta."),
            ("¿Qué reglas de D&D se soportan?", "GrimQuill sigue las reglas básicas de D&D 5e: pruebas de habilidad, salvaciones, ataques, espacios de conjuro, condiciones y más. El GM maneja las mecánicas para que te centres en la aventura."),
            ("¿Mis datos son privados?", "Sí. Tus conversaciones y datos de campaña son privados y solo visibles para ti. No compartimos tus datos con nadie."),
        ],
        "ru": [
            ("GrimQuill бесплатный?", "Да! Все приключения и AI Game Master полностью бесплатны. Мы используем несколько провайдеров ИИ с автоматическим переключением для лучшего опыта без затрат."),
            ("Как работает интерактивная фантастика?", "Выберите историю, прочитайте вступительную сцену и принимайте решения, которые формируют сюжет. ИИ генерирует уникальные ответы на основе ваших решений — каждое прохождение уникально."),
            ("Как работает режим D&D?", "ИИ выступает в роли вашего Game Master по правилам D&D 5e. Создайте персонажа, исследуйте подземелья, сражайтесь с монстрами и принимайте решения. GM отслеживает ваши характеристики и адаптирует историю."),
            ("Как работают броски кубиков?", "AI Game Master автоматически бросает кубики по стандартной нотации D&D (d20, 2d6+3 и т.д.). Броски атаки, спасброски, проверки способностей — все с видимыми результатами."),
            ("Что такое трекер боя?", "Во время столкновений GM отслеживает очки здоровья, класс брони, состояния и порядок хода. Вы видите статус персонажа и принимаете тактические решения каждый раунд."),
            ("Могу ли я создавать свои приключения?", "Да! Нажмите 'Создать', чтобы построить свою интерактивную историю или кампанию D&D. Задайте сеттинг, персонажей и вступительную сцену — ИИ сделает остальное."),
            ("Мой прогресс сохраняется?", "Да. История чата и прогресс кампании сохраняются автоматически. Вы можете вернуться к любому приключению и продолжить с того места, где остановились."),
            ("Какие языки поддерживаются?", "Интерфейс поддерживает английский, испанский, русский, французский, немецкий, португальский и итальянский. AI Game Master отвечает на том языке, на котором вы пишете."),
            ("Как работает AI Game Master?", "GM использует продвинутые языковые модели для генерации нарратива, управления игровыми механиками и адаптации к вашему стилю игры. Он следует правилам D&D 5e, поддерживая увлекательный сюжет."),
            ("Можно играть с друзьями?", "Сейчас GrimQuill рассчитан на одиночную игру — один игрок с AI Game Master. Мультиплеерные кампании в планах на будущее."),
            ("Какие правила D&D поддерживаются?", "GrimQuill следует базовым правилам D&D 5e: проверки способностей, спасброски, атаки, ячейки заклинаний, состояния и многое другое. GM берет механику на себя, чтобы вы могли сосредоточиться на приключении."),
            ("Мои данные приватны?", "Да. Ваши разговоры и данные кампаний приватны и видны только вам. Мы не передаем ваши данные третьим лицам."),
        ],
        "fr": [
            ("GrimQuill est-il gratuit ?", "Oui ! Toutes les aventures et le Game Master IA sont entierement gratuits. Nous utilisons plusieurs fournisseurs d'IA avec basculement automatique pour la meilleure experience sans frais."),
            ("Comment fonctionne la fiction interactive ?", "Choisissez une histoire, lisez la scene d'ouverture et faites des choix qui faconnent le recit. L'IA genere des reponses uniques basees sur vos decisions — chaque partie est unique."),
            ("Comment fonctionne le mode D&D ?", "L'IA agit comme votre Game Master en suivant les regles de D&D 5e. Creez un personnage, explorez des donjons, combattez des monstres et prenez des decisions. Le GM suit vos statistiques et adapte l'histoire."),
            ("Comment fonctionnent les lancers de des ?", "Le Game Master lance les des automatiquement en notation D&D standard (d20, 2d6+3, etc.). Jets d'attaque, de sauvegarde, de competence — tous resolus avec des resultats visibles."),
            ("Qu'est-ce que le suivi de combat ?", "Pendant les rencontres, le GM suit les points de vie, la classe d'armure, les conditions et l'ordre de tour. Vous voyez l'etat de votre personnage et prenez des decisions tactiques chaque tour."),
            ("Puis-je creer mes propres aventures ?", "Oui ! Cliquez sur 'Creer' pour construire votre propre fiction interactive ou campagne D&D. Definissez le cadre, les personnages et la scene d'ouverture — l'IA fait le reste."),
            ("Ma progression est-elle sauvegardee ?", "Oui. Votre historique de chat et votre progression de campagne sont sauvegardes automatiquement. Vous pouvez revenir a n'importe quelle aventure et continuer la ou vous en etiez."),
            ("Quelles langues sont disponibles ?", "L'interface supporte l'anglais, l'espagnol, le russe, le francais, l'allemand, le portugais et l'italien. Le Game Master repond dans la langue dans laquelle vous ecrivez."),
            ("Comment fonctionne le Game Master IA ?", "Le GM utilise des modeles de langage avances pour generer des reponses narratives, gerer les mecaniques de jeu et s'adapter a votre style. Il suit les regles de D&D 5e tout en maintenant une histoire captivante."),
            ("Puis-je jouer avec des amis ?", "Actuellement GrimQuill est concu pour le jeu solo — un joueur avec le Game Master IA. Les campagnes multijoueurs sont prevues dans les futures mises a jour."),
            ("Quelles regles de D&D sont supportees ?", "GrimQuill suit les regles de base de D&D 5e : tests de competence, jets de sauvegarde, attaques, emplacements de sorts, conditions et plus. Le GM gere les mecaniques pour que vous vous concentriez sur l'aventure."),
            ("Mes donnees sont-elles privees ?", "Oui. Vos conversations et donnees de campagne sont privees et visibles uniquement par vous. Nous ne partageons vos donnees avec personne."),
        ],
        "de": [
            ("Ist GrimQuill kostenlos?", "Ja! Alle Abenteuer und der KI-Spielleiter sind komplett kostenlos. Wir nutzen mehrere KI-Anbieter mit automatischem Wechsel fuer das beste Erlebnis ohne Kosten."),
            ("Wie funktioniert interaktive Fiktion?", "Waehle eine Geschichte, lies die Eroeffnungsszene und triff Entscheidungen, die die Handlung formen. Die KI generiert einzigartige Antworten basierend auf deinen Entscheidungen — kein Durchgang gleicht dem anderen."),
            ("Wie funktioniert der D&D-Modus?", "Die KI agiert als dein Spielleiter nach D&D-5e-Regeln. Erstelle einen Charakter, erkunde Dungeons, kaempfe gegen Monster und triff Entscheidungen. Der GM verfolgt deine Werte und passt die Geschichte an."),
            ("Wie funktionieren Wuerfelwuerfe?", "Der Spielleiter wuerfelt automatisch in Standard-D&D-Notation (d20, 2d6+3 usw.). Angriffswuerfe, Rettungswuerfe, Faehigkeitsproben — alles mit sichtbaren Ergebnissen."),
            ("Was ist der Kampftracker?", "Waehrend Begegnungen verfolgt der GM Trefferpunkte, Ruestungsklasse, Zustaende und Zugreihenfolge. Du siehst den Status deines Charakters und triffst jede Runde taktische Entscheidungen."),
            ("Kann ich eigene Abenteuer erstellen?", "Ja! Klicke auf 'Erstellen', um deine eigene interaktive Geschichte oder D&D-Kampagne zu bauen. Definiere Setting, Charaktere und Eroeffnungsszene — die KI erledigt den Rest."),
            ("Wird mein Fortschritt gespeichert?", "Ja. Dein Chatverlauf und Kampagnenfortschritt werden automatisch gespeichert. Du kannst zu jedem Abenteuer zurueckkehren und dort weitermachen, wo du aufgehoert hast."),
            ("Welche Sprachen werden unterstuetzt?", "Die Oberflaeche unterstuetzt Englisch, Spanisch, Russisch, Franzoesisch, Deutsch, Portugiesisch und Italienisch. Der Spielleiter antwortet in der Sprache, in der du schreibst."),
            ("Wie funktioniert der KI-Spielleiter?", "Der GM nutzt fortschrittliche Sprachmodelle, um Erzaehlungen zu generieren, Spielmechaniken zu verwalten und sich an deinen Spielstil anzupassen. Er folgt den D&D-5e-Regeln und haelt die Geschichte spannend."),
            ("Kann ich mit Freunden spielen?", "Derzeit ist GrimQuill fuer Einzelspieler konzipiert — ein Spieler mit dem KI-Spielleiter. Mehrspieler-Kampagnen sind fuer zukuenftige Updates geplant."),
            ("Welche D&D-Regeln werden unterstuetzt?", "GrimQuill folgt den D&D-5e-Grundregeln: Faehigkeitsproben, Rettungswuerfe, Angriffe, Zauberplaetze, Zustaende und mehr. Der GM uebernimmt die Mechanik, damit du dich auf das Abenteuer konzentrieren kannst."),
            ("Sind meine Daten privat?", "Ja. Deine Gespraeche und Kampagnendaten sind privat und nur fuer dich sichtbar. Wir geben deine Daten an niemanden weiter."),
        ],
        "pt": [
            ("O GrimQuill e gratuito?", "Sim! Todas as aventuras e o Mestre de Jogo com IA sao completamente gratuitos. Usamos multiplos provedores de IA com troca automatica para garantir a melhor experiencia sem custo."),
            ("Como funciona a ficcao interativa?", "Escolha uma historia, leia a cena de abertura e faca escolhas que moldam a narrativa. A IA gera respostas unicas baseadas nas suas decisoes — nenhuma partida e igual."),
            ("Como funciona o modo D&D?", "A IA atua como seu Mestre de Jogo seguindo as regras de D&D 5e. Crie um personagem, explore masmorras, lute contra monstros e tome decisoes. O GM rastreia suas estatisticas e adapta a historia."),
            ("Como funcionam as rolagens de dados?", "O Mestre de Jogo rola dados automaticamente usando notacao padrao de D&D (d20, 2d6+3, etc.). Rolagens de ataque, salvamento, habilidade — todas resolvidas com resultados visiveis."),
            ("O que e o rastreador de combate?", "Durante encontros, o GM rastreia pontos de vida, classe de armadura, condicoes e ordem de turno. Voce ve o status do seu personagem e pode tomar decisoes taticas a cada rodada."),
            ("Posso criar minhas proprias aventuras?", "Sim! Clique em 'Criar' para construir sua propria ficcao interativa ou campanha de D&D. Defina o cenario, personagens e cena de abertura — a IA cuida do resto."),
            ("Meu progresso e salvo?", "Sim. Seu historico de chat e progresso de campanha sao salvos automaticamente. Voce pode voltar a qualquer aventura e continuar de onde parou."),
            ("Quais idiomas sao suportados?", "A interface suporta ingles, espanhol, russo, frances, alemao, portugues e italiano. O Mestre de Jogo responde no idioma em que voce escreve."),
            ("Como funciona o Mestre de Jogo com IA?", "O GM usa modelos de linguagem avancados para gerar respostas narrativas, gerenciar mecanicas de jogo e se adaptar ao seu estilo. Segue as regras de D&D 5e mantendo uma historia envolvente."),
            ("Posso jogar com amigos?", "Atualmente o GrimQuill e projetado para jogo solo — um jogador com o Mestre de Jogo IA. Campanhas multiplayer estao no nosso roteiro para futuras atualizacoes."),
            ("Quais regras de D&D sao suportadas?", "GrimQuill segue as regras basicas de D&D 5e: testes de habilidade, salvamentos, ataques, espacos de magia, condicoes e mais. O GM gerencia as mecanicas para que voce foque na aventura."),
            ("Meus dados sao privados?", "Sim. Suas conversas e dados de campanha sao privados e visiveis apenas para voce. Nao compartilhamos seus dados com ninguem."),
        ],
        "it": [
            ("GrimQuill e gratuito?", "Si! Tutte le avventure e il Game Master IA sono completamente gratuiti. Utilizziamo piu fornitori di IA con cambio automatico per garantire la migliore esperienza senza costi."),
            ("Come funziona la narrativa interattiva?", "Scegli una storia, leggi la scena di apertura e fai scelte che plasmano la trama. L'IA genera risposte uniche basate sulle tue decisioni — ogni partita e diversa."),
            ("Come funziona la modalita D&D?", "L'IA agisce come il tuo Game Master seguendo le regole di D&D 5e. Crea un personaggio, esplora dungeon, combatti mostri e prendi decisioni. Il GM tiene traccia delle tue statistiche e adatta la storia."),
            ("Come funzionano i tiri di dado?", "Il Game Master tira i dadi automaticamente usando la notazione D&D standard (d20, 2d6+3, ecc.). Tiri di attacco, tiri salvezza, prove di abilita — tutti risolti con risultati visibili."),
            ("Cos'e il tracker di combattimento?", "Durante gli scontri, il GM tiene traccia di punti ferita, classe armatura, condizioni e ordine di turno. Vedi lo stato del tuo personaggio e prendi decisioni tattiche ogni turno."),
            ("Posso creare le mie avventure?", "Si! Clicca 'Crea' per costruire la tua narrativa interattiva o campagna D&D. Definisci l'ambientazione, i personaggi e la scena di apertura — l'IA fa il resto."),
            ("I miei progressi vengono salvati?", "Si. La cronologia delle chat e i progressi della campagna vengono salvati automaticamente. Puoi tornare a qualsiasi avventura e continuare da dove avevi lasciato."),
            ("Quali lingue sono supportate?", "L'interfaccia supporta inglese, spagnolo, russo, francese, tedesco, portoghese e italiano. Il Game Master risponde nella lingua in cui scrivi."),
            ("Come funziona il Game Master IA?", "Il GM utilizza modelli linguistici avanzati per generare risposte narrative, gestire le meccaniche di gioco e adattarsi al tuo stile. Segue le regole di D&D 5e mantenendo una storia avvincente."),
            ("Posso giocare con gli amici?", "Attualmente GrimQuill e progettato per il gioco in solitario — un giocatore con il Game Master IA. Le campagne multiplayer sono nella nostra roadmap per futuri aggiornamenti."),
            ("Quali regole di D&D sono supportate?", "GrimQuill segue le regole base di D&D 5e: prove di abilita, tiri salvezza, attacchi, slot incantesimo, condizioni e altro. Il GM gestisce le meccaniche per farti concentrare sull'avventura."),
            ("I miei dati sono privati?", "Si. Le tue conversazioni e i dati delle campagne sono privati e visibili solo a te. Non condividiamo i tuoi dati con nessuno."),
        ],
    }

    # FAQ Q&A pairs per language — synced with frontend locales (12 questions)
    _faq = {
        "en": [
            ("Is SweetSin free?", "Yes! Core features are completely free. We offer dozens of free models via Groq, Cerebras, and OpenRouter. Premium models (GPT-4o, Gemini) require your own API key."),
            ("What AI models are available?", "8 providers: Groq (Llama 3.3, Kimi K2, Scout, Maverick), Cerebras, OpenRouter (Hermes 405B, Gemma, DeepSeek R1), Together, DeepSeek, Qwen, OpenAI GPT-4o, and Google Gemini. Auto-fallback switches models if one is unavailable."),
            ("Can I create NSFW content?", "Yes, for users 18+. You control the content rating per character. Some models (like GPT-OSS) have built-in content restrictions, but most free models support unrestricted content."),
            ("How do I create a character?", "Click 'Create' in the header. You can build a character manually with personality, appearance, scenario, and example dialogues — or paste any text and let AI generate a character from it. You can also import SillyTavern character cards."),
            ("Is my chat history private?", "Yes. Your conversations are private and only visible to you. We do not share chat content with anyone."),
            ("Can I delete my data?", "Yes. Go to Profile and use 'Delete Account' in the Danger Zone section. This permanently removes your account, characters, chats, and all associated data."),
            ("What are personas?", "Personas let you roleplay as different characters. Create a persona with a name and description in your profile, then select it when starting a new chat. The AI will address you by your persona's name."),
            ("How do group chats work?", "Open a chat and add other characters via the group chat panel. Each character responds in turn based on the conversation context. They interact with you and with each other."),
            ("What are lorebooks?", "Lorebooks are world-building tools. Add entries with keywords — when those keywords appear in chat, the related lore is automatically included in the AI's context. Great for consistent world details."),
            ("How does chat memory work?", "For long conversations, the AI automatically summarizes earlier messages so it remembers important details even as the context window fills up. You can toggle this per chat in settings."),
            ("Can I import SillyTavern characters?", "Yes! Go to Create, then the Import tab. Upload a SillyTavern character card (JSON, v1 or v2 format) or paste the JSON directly. All fields are mapped automatically."),
            ("Can I have multiple chats with the same character?", "Yes. Click 'New Chat' on the character page or in the chat header. Each chat has its own independent history, context, and model settings."),
        ],
        "es": [
            ("¿SweetSin es gratis?", "¡Sí! Las funciones principales son completamente gratuitas. Docenas de modelos gratuitos a través de Groq, Cerebras y OpenRouter. Los modelos premium (GPT-4o, Gemini) requieren tu propia clave API."),
            ("¿Qué modelos de IA están disponibles?", "8 proveedores: Groq (Llama 3.3, Kimi K2, Scout, Maverick), Cerebras, OpenRouter (Hermes 405B, Gemma, DeepSeek R1), Together, DeepSeek, Qwen, OpenAI GPT-4o y Google Gemini. El auto-fallback cambia de modelo automáticamente si uno no está disponible."),
            ("¿Puedo crear contenido NSFW?", "Sí, para usuarios de 18+. Tú controlas la clasificación de contenido por personaje. Algunos modelos (como GPT-OSS) tienen restricciones integradas, pero la mayoría de los modelos gratuitos soportan contenido sin restricciones."),
            ("¿Cómo creo un personaje?", "Haz clic en 'Crear' en la barra superior. Crea un personaje manualmente con personalidad, apariencia, escenario y diálogos de ejemplo — o pega cualquier texto y deja que la IA genere un personaje. También puedes importar tarjetas de SillyTavern."),
            ("¿Mi historial de chat es privado?", "Sí. Tus conversaciones son privadas y solo visibles para ti. No compartimos el contenido de los chats con nadie."),
            ("¿Puedo eliminar mis datos?", "Sí. Ve a Perfil, sección Zona de peligro, y usa 'Eliminar cuenta'. Esto elimina permanentemente tu cuenta, personajes, chats y todos los datos asociados."),
            ("¿Qué son las personas?", "Las personas te permiten interpretar diferentes personajes. Crea una persona con nombre y descripción en tu perfil, luego selecciónala al iniciar un nuevo chat. La IA se dirigirá a ti por el nombre de tu persona."),
            ("¿Cómo funcionan los chats grupales?", "Abre un chat y añade otros personajes a través del panel de chat grupal. Cada personaje responde por turnos según el contexto de la conversación. Interactúan contigo y entre ellos."),
            ("¿Qué son los lorebooks?", "Los lorebooks son herramientas de construcción de mundo. Añade entradas con palabras clave — cuando esas palabras aparecen en el chat, la información relacionada se incluye automáticamente en el contexto de la IA."),
            ("¿Cómo funciona la memoria del chat?", "Para conversaciones largas, la IA resume automáticamente los mensajes anteriores para recordar detalles importantes incluso cuando la ventana de contexto se llena. Puedes activar/desactivar esto por chat en configuración."),
            ("¿Puedo importar personajes de SillyTavern?", "¡Sí! Ve a Crear, pestaña Importar. Sube una tarjeta de SillyTavern (JSON, formato v1 o v2) o pega el JSON directamente. Todos los campos se mapean automáticamente."),
            ("¿Puedo tener múltiples chats con el mismo personaje?", "Sí. Haz clic en 'Nuevo chat' en la página del personaje o en la cabecera del chat. Cada chat tiene su propio historial, contexto y configuración de modelo independiente."),
        ],
        "ru": [
            ("SweetSin бесплатный?", "Да! Основные функции полностью бесплатны. Десятки бесплатных моделей через Groq, Cerebras и OpenRouter. Премиум-модели (GPT-4o, Gemini) требуют собственного API-ключа."),
            ("Какие AI-модели доступны?", "8 провайдеров: Groq (Llama 3.3, Kimi K2, Scout, Maverick), Cerebras, OpenRouter (Hermes 405B, Gemma, DeepSeek R1), Together, DeepSeek, Qwen, OpenAI GPT-4o и Google Gemini. Авто-фоллбэк автоматически переключает модели при недоступности."),
            ("Можно создавать NSFW контент?", "Да, для пользователей 18+. Вы контролируете рейтинг контента для каждого персонажа. Некоторые модели (GPT-OSS) имеют встроенные ограничения, но большинство бесплатных моделей поддерживают контент без ограничений."),
            ("Как создать персонажа?", "Нажмите 'Создать' в шапке. Создайте персонажа вручную с личностью, внешностью, сценарием и примерами диалогов — или вставьте любой текст, и AI сгенерирует персонажа. Также можно импортировать карточки SillyTavern."),
            ("Моя история чатов приватна?", "Да. Ваши разговоры приватны и видны только вам. Мы не делимся содержимым чатов ни с кем."),
            ("Могу ли я удалить свои данные?", "Да. Перейдите в Профиль, раздел 'Опасная зона', и нажмите 'Удалить аккаунт'. Все данные, персонажи, чаты и связанная информация будут удалены безвозвратно."),
            ("Что такое персоны?", "Персоны позволяют отыгрывать разных персонажей. Создайте персону с именем и описанием в профиле, затем выберите её при начале нового чата. AI будет обращаться к вам по имени персоны."),
            ("Как работают групповые чаты?", "Откройте чат и добавьте других персонажей через панель группового чата. Каждый персонаж отвечает по очереди на основе контекста разговора. Они взаимодействуют с вами и друг с другом."),
            ("Что такое лорбуки?", "Лорбуки — инструменты для построения мира. Добавьте записи с ключевыми словами — когда эти слова появляются в чате, связанная информация автоматически включается в контекст AI. Отлично подходит для поддержания деталей мира."),
            ("Как работает память чата?", "Для длинных разговоров AI автоматически суммаризирует ранние сообщения, чтобы помнить важные детали даже при заполнении контекстного окна. Можно включить/выключить для каждого чата в настройках."),
            ("Можно импортировать персонажей из SillyTavern?", "Да! Перейдите в Создать, вкладка Импорт. Загрузите карточку SillyTavern (JSON, формат v1 или v2) или вставьте JSON напрямую. Все поля маппятся автоматически."),
            ("Можно вести несколько чатов с одним персонажем?", "Да. Нажмите 'Новый чат' на странице персонажа или в шапке чата. Каждый чат имеет свою независимую историю, контекст и настройки модели."),
        ],
        "fr": [
            ("SweetSin est-il gratuit ?", "Oui ! Les fonctionnalités principales sont entièrement gratuites. Nous proposons des dizaines de modèles gratuits via Groq, Cerebras et OpenRouter. Les modèles premium (GPT-4o, Gemini) nécessitent votre propre clé API."),
            ("Quels modèles d'IA sont disponibles ?", "8 fournisseurs : Groq (Llama 3.3, Kimi K2, Scout, Maverick), Cerebras, OpenRouter (Hermes 405B, Gemma, DeepSeek R1), Together, DeepSeek, Qwen, OpenAI GPT-4o et Google Gemini. Le basculement automatique change de modèle si l'un est indisponible."),
            ("Puis-je créer du contenu NSFW ?", "Oui, pour les utilisateurs de 18 ans et plus. Vous contrôlez la classification du contenu par personnage. Certains modèles (comme GPT-OSS) ont des restrictions intégrées, mais la plupart des modèles gratuits prennent en charge le contenu sans restriction."),
            ("Comment créer un personnage ?", "Cliquez sur 'Créer' dans l'en-tête. Vous pouvez construire un personnage manuellement avec personnalité, apparence, scénario et exemples de dialogues — ou coller n'importe quel texte et laisser l'IA générer un personnage. Vous pouvez aussi importer des fiches SillyTavern."),
            ("Mon historique de discussion est-il privé ?", "Oui. Vos conversations sont privées et visibles uniquement par vous. Nous ne partageons le contenu des discussions avec personne."),
            ("Puis-je supprimer mes données ?", "Oui. Allez dans Profil, section Zone de danger, et utilisez 'Supprimer le compte'. Cela supprime définitivement votre compte, vos personnages, vos discussions et toutes les données associées."),
            ("Que sont les personas ?", "Les personas vous permettent d'incarner différents personnages. Créez un persona avec un nom et une description dans votre profil, puis sélectionnez-le en démarrant une nouvelle discussion. L'IA vous appellera par le nom de votre persona."),
            ("Comment fonctionnent les discussions de groupe ?", "Ouvrez une discussion et ajoutez d'autres personnages via le panneau de discussion de groupe. Chaque personnage répond à son tour en fonction du contexte de la conversation. Ils interagissent avec vous et entre eux."),
            ("Que sont les lorebooks ?", "Les lorebooks sont des outils de construction d'univers. Ajoutez des entrées avec des mots-clés — lorsque ces mots-clés apparaissent dans la discussion, le lore associé est automatiquement inclus dans le contexte de l'IA."),
            ("Comment fonctionne la mémoire du chat ?", "Pour les longues conversations, l'IA résume automatiquement les messages précédents afin de se souvenir des détails importants même lorsque la fenêtre de contexte se remplit. Vous pouvez activer ou désactiver cette fonctionnalité par discussion dans les paramètres."),
            ("Puis-je importer des personnages SillyTavern ?", "Oui ! Allez dans Créer puis l'onglet Import. Téléversez une fiche personnage SillyTavern (JSON, format v1 ou v2) ou collez le JSON directement. Tous les champs sont mappés automatiquement."),
            ("Puis-je avoir plusieurs discussions avec le même personnage ?", "Oui. Cliquez sur 'Nouvelle discussion' sur la page du personnage ou dans l'en-tête de la discussion. Chaque discussion a son propre historique, contexte et paramètres de modèle indépendants."),
        ],
        "de": [
            ("Ist SweetSin kostenlos?", "Ja! Die Kernfunktionen sind vollständig kostenlos. Wir bieten Dutzende kostenloser Modelle über Groq, Cerebras und OpenRouter an. Premium-Modelle (GPT-4o, Gemini) erfordern Ihren eigenen API-Schlüssel."),
            ("Welche KI-Modelle sind verfügbar?", "8 Anbieter: Groq (Llama 3.3, Kimi K2, Scout, Maverick), Cerebras, OpenRouter (Hermes 405B, Gemma, DeepSeek R1), Together, DeepSeek, Qwen, OpenAI GPT-4o und Google Gemini. Automatisches Fallback wechselt Modelle, wenn eines nicht verfügbar ist."),
            ("Kann ich NSFW-Inhalte erstellen?", "Ja, für Benutzer ab 18 Jahren. Sie steuern die Inhaltsbewertung pro Charakter. Einige Modelle (wie GPT-OSS) haben integrierte Inhaltsbeschränkungen, aber die meisten kostenlosen Modelle unterstützen uneingeschränkte Inhalte."),
            ("Wie erstelle ich einen Charakter?", "Klicken Sie auf 'Erstellen' in der Kopfzeile. Sie können einen Charakter manuell mit Persönlichkeit, Aussehen, Szenario und Beispieldialogen erstellen — oder einen beliebigen Text einfügen und die KI daraus einen Charakter generieren lassen. Sie können auch SillyTavern-Charakterkarten importieren."),
            ("Ist mein Chatverlauf privat?", "Ja. Ihre Gespräche sind privat und nur für Sie sichtbar. Wir teilen Chat-Inhalte mit niemandem."),
            ("Kann ich meine Daten löschen?", "Ja. Gehen Sie zum Profil, Bereich Gefahrenzone, und nutzen Sie 'Konto löschen'. Dies entfernt dauerhaft Ihr Konto, Charaktere, Chats und alle zugehörigen Daten."),
            ("Was sind Personas?", "Personas ermöglichen es Ihnen, als verschiedene Charaktere zu spielen. Erstellen Sie eine Persona mit Name und Beschreibung in Ihrem Profil und wählen Sie sie beim Starten eines neuen Chats aus. Die KI wird Sie mit dem Namen Ihrer Persona ansprechen."),
            ("Wie funktionieren Gruppenchats?", "Öffnen Sie einen Chat und fügen Sie andere Charaktere über das Gruppenchat-Panel hinzu. Jeder Charakter antwortet abwechselnd basierend auf dem Gesprächskontext. Sie interagieren mit Ihnen und miteinander."),
            ("Was sind Lorebooks?", "Lorebooks sind Weltenbau-Werkzeuge. Fügen Sie Einträge mit Schlüsselwörtern hinzu — wenn diese Schlüsselwörter im Chat erscheinen, wird die zugehörige Lore automatisch in den KI-Kontext eingefügt. Ideal für konsistente Weltdetails."),
            ("Wie funktioniert die Chat-Erinnerung?", "Bei langen Gesprächen fasst die KI automatisch frühere Nachrichten zusammen, damit sie sich an wichtige Details erinnert, auch wenn das Kontextfenster sich füllt. Sie können dies pro Chat in den Einstellungen umschalten."),
            ("Kann ich SillyTavern-Charaktere importieren?", "Ja! Gehen Sie zu Erstellen, dann der Import-Tab. Laden Sie eine SillyTavern-Charakterkarte hoch (JSON, v1- oder v2-Format) oder fügen Sie das JSON direkt ein. Alle Felder werden automatisch zugeordnet."),
            ("Kann ich mehrere Chats mit demselben Charakter haben?", "Ja. Klicken Sie auf 'Neuer Chat' auf der Charakterseite oder in der Chat-Kopfzeile. Jeder Chat hat seinen eigenen unabhängigen Verlauf, Kontext und Modelleinstellungen."),
        ],
        "pt": [
            ("O SweetSin é gratuito?", "Sim! Os recursos principais são totalmente gratuitos. Oferecemos dezenas de modelos gratuitos via Groq, Cerebras e OpenRouter. Modelos premium (GPT-4o, Gemini) exigem sua própria chave de API."),
            ("Quais modelos de IA estão disponíveis?", "8 provedores: Groq (Llama 3.3, Kimi K2, Scout, Maverick), Cerebras, OpenRouter (Hermes 405B, Gemma, DeepSeek R1), Together, DeepSeek, Qwen, OpenAI GPT-4o e Google Gemini. O auto-fallback troca de modelo se um estiver indisponível."),
            ("Posso criar conteúdo NSFW?", "Sim, para usuários maiores de 18 anos. Você controla a classificação de conteúdo por personagem. Alguns modelos (como GPT-OSS) têm restrições de conteúdo embutidas, mas a maioria dos modelos gratuitos suporta conteúdo sem restrições."),
            ("Como eu crio um personagem?", "Clique em 'Criar' no cabeçalho. Você pode construir um personagem manualmente com personalidade, aparência, cenário e diálogos de exemplo — ou colar qualquer texto e deixar a IA gerar um personagem a partir dele. Você também pode importar cards do SillyTavern."),
            ("Meu histórico de conversas é privado?", "Sim. Suas conversas são privadas e visíveis apenas para você. Não compartilhamos o conteúdo das conversas com ninguém."),
            ("Posso excluir meus dados?", "Sim. Vá ao Perfil, seção Zona de Perigo, e use 'Excluir Conta'. Isso remove permanentemente sua conta, personagens, conversas e todos os dados associados."),
            ("O que são personas?", "Personas permitem que você interprete diferentes personagens. Crie uma persona com nome e descrição no seu perfil, depois selecione-a ao iniciar uma nova conversa. A IA vai se dirigir a você pelo nome da sua persona."),
            ("Como funcionam os chats em grupo?", "Abra uma conversa e adicione outros personagens pelo painel de chat em grupo. Cada personagem responde por vez baseado no contexto da conversa. Eles interagem com você e entre si."),
            ("O que são lorebooks?", "Lorebooks são ferramentas de construção de mundo. Adicione entradas com palavras-chave — quando essas palavras-chave aparecerem no chat, o lore relacionado é automaticamente incluído no contexto da IA."),
            ("Como funciona a memória do chat?", "Para conversas longas, a IA automaticamente resume mensagens anteriores para lembrar detalhes importantes mesmo quando a janela de contexto enche. Você pode ativar ou desativar isso por conversa nas configurações."),
            ("Posso importar personagens do SillyTavern?", "Sim! Vá em Criar, aba Importar. Envie um card de personagem do SillyTavern (JSON, formato v1 ou v2) ou cole o JSON diretamente. Todos os campos são mapeados automaticamente."),
            ("Posso ter múltiplas conversas com o mesmo personagem?", "Sim. Clique em 'Nova Conversa' na página do personagem ou no cabeçalho do chat. Cada conversa tem seu próprio histórico, contexto e configurações de modelo independentes."),
        ],
        "it": [
            ("SweetSin è gratuito?", "Sì! Le funzionalità principali sono completamente gratuite. Offriamo decine di modelli gratuiti tramite Groq, Cerebras e OpenRouter. I modelli premium (GPT-4o, Gemini) richiedono la propria chiave API."),
            ("Quali modelli AI sono disponibili?", "8 provider: Groq (Llama 3.3, Kimi K2, Scout, Maverick), Cerebras, OpenRouter (Hermes 405B, Gemma, DeepSeek R1), Together, DeepSeek, Qwen, OpenAI GPT-4o e Google Gemini. Il fallback automatico cambia modello se uno non è disponibile."),
            ("Posso creare contenuti NSFW?", "Sì, per utenti 18+. Puoi controllare la classificazione dei contenuti per ogni personaggio. Alcuni modelli (come GPT-OSS) hanno restrizioni integrate, ma la maggior parte dei modelli gratuiti supporta contenuti senza restrizioni."),
            ("Come posso creare un personaggio?", "Clicca 'Crea' nell'intestazione. Puoi costruire un personaggio manualmente con personalità, aspetto, scenario e dialoghi di esempio — oppure incolla qualsiasi testo e lascia che l'IA generi un personaggio. Puoi anche importare schede SillyTavern."),
            ("La mia cronologia delle chat è privata?", "Sì. Le tue conversazioni sono private e visibili solo a te. Non condividiamo il contenuto delle chat con nessuno."),
            ("Posso eliminare i miei dati?", "Sì. Vai al Profilo, sezione Zona pericolosa, e usa 'Elimina account'. Questa azione rimuove definitivamente il tuo account, i personaggi, le chat e tutti i dati associati."),
            ("Cosa sono le persona?", "Le persona ti permettono di interpretare ruoli diversi. Crea una persona con un nome e una descrizione nel tuo profilo, poi selezionala quando inizi una nuova chat. L'IA ti chiamerà con il nome della tua persona."),
            ("Come funzionano le chat di gruppo?", "Apri una chat e aggiungi altri personaggi tramite il pannello chat di gruppo. Ogni personaggio risponde a turno in base al contesto della conversazione. Interagiscono con te e tra loro."),
            ("Cosa sono i lorebook?", "I lorebook sono strumenti di world-building. Aggiungi voci con parole chiave — quando quelle parole chiave appaiono nella chat, le informazioni correlate vengono automaticamente incluse nel contesto dell'IA."),
            ("Come funziona la memoria della chat?", "Per le conversazioni lunghe, l'IA riassume automaticamente i messaggi precedenti in modo da ricordare i dettagli importanti anche quando la finestra di contesto si riempie. Puoi attivare o disattivare questa funzione per ogni chat nelle impostazioni."),
            ("Posso importare personaggi di SillyTavern?", "Sì! Vai su Crea, scheda Importa. Carica una scheda personaggio SillyTavern (JSON, formato v1 o v2) oppure incolla direttamente il JSON. Tutti i campi vengono mappati automaticamente."),
            ("Posso avere più chat con lo stesso personaggio?", "Sì. Clicca 'Nuova chat' nella pagina del personaggio o nell'intestazione della chat. Ogni chat ha la propria cronologia, contesto e impostazioni del modello indipendenti."),
        ],
    }

    _faq_titles = {
        "en": "Frequently Asked Questions",
        "es": "Preguntas frecuentes",
        "ru": "Часто задаваемые вопросы",
        "fr": "Questions fréquentes",
        "de": "Häufig gestellte Fragen",
        "pt": "Perguntas Frequentes",
        "it": "Domande frequenti",
    }
    _faq_descriptions = {
        "en": "Frequently asked questions about SweetSin — AI character chat, roleplay, models, personas, group chats, and more.",
        "es": "Preguntas frecuentes sobre SweetSin — chat con personajes IA, roleplay, modelos, personas, chats grupales y más.",
        "ru": "Часто задаваемые вопросы о SweetSin — чат с AI-персонажами, ролеплей, модели, персоны, групповые чаты и другое.",
        "fr": "Questions fréquentes sur SweetSin — chat avec personnages IA, jeu de rôle, modèles, personas, discussions de groupe et plus.",
        "de": "Häufig gestellte Fragen zu SweetSin — KI-Charakter-Chat, Rollenspiel, Modelle, Personas, Gruppenchats und mehr.",
        "pt": "Perguntas frequentes sobre SweetSin — chat com personagens IA, roleplay, modelos, personas, chats em grupo e mais.",
        "it": "Domande frequenti su SweetSin — chat con personaggi IA, gioco di ruolo, modelli, persona, chat di gruppo e altro.",
    }
    _faq_descriptions_fiction = {
        "en": "Frequently asked questions about GrimQuill — AI interactive fiction, D&D Game Master, dice rolling, combat, and adventures.",
        "es": "Preguntas frecuentes sobre GrimQuill — ficcion interactiva con IA, Game Master de D&D, dados, combate y aventuras.",
        "ru": "Часто задаваемые вопросы о GrimQuill — интерактивная фантастика с ИИ, D&D Game Master, кубики, бой и приключения.",
        "fr": "Questions frequentes sur GrimQuill — fiction interactive IA, Game Master D&D, des, combat et aventures.",
        "de": "Haeufig gestellte Fragen zu GrimQuill — KI-interaktive Fiktion, D&D-Spielleiter, Wuerfel, Kampf und Abenteuer.",
        "pt": "Perguntas frequentes sobre GrimQuill — ficcao interativa com IA, Mestre de Jogo D&D, dados, combate e aventuras.",
        "it": "Domande frequenti su GrimQuill — narrativa interattiva IA, Game Master D&D, dadi, combattimento e avventure.",
    }

    faq_source = _faq_fiction if settings.is_fiction_mode else _faq
    desc_source = _faq_descriptions_fiction if settings.is_fiction_mode else _faq_descriptions
    pairs = [(_brand(q), _brand(a)) for q, a in faq_source.get(lang, faq_source["en"])]
    faq_title = _faq_titles.get(lang, _faq_titles["en"])
    faq_desc = _brand(desc_source.get(lang, desc_source["en"]))
    canonical = f"{SITE_URL}/{lang}/faq"

    qa_html = "\n".join(
        f"<h2>{_escape(q)}</h2><p>{_escape(a)}</p>" for q, a in pairs
    )
    ld_faq = json.dumps(faq_jsonld(pairs), ensure_ascii=False)
    ld_breadcrumb = json.dumps(breadcrumb_jsonld([
        (SITE_NAME, SITE_URL),
        ("FAQ", None),
    ]), ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="{_escape(lang)}">
<head>
<meta charset="UTF-8">
<title>{_escape(faq_title)} | {SITE_NAME}</title>
<meta name="description" content="{_escape(faq_desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{_escape(faq_title)} — {SITE_NAME}">
<meta property="og:description" content="{_escape(faq_desc)}">
<meta property="og:image" content="{SITE_URL}/og-image.png">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{_escape(faq_title)} — {SITE_NAME}">
<meta name="twitter:description" content="{_escape(faq_desc)}">
<meta name="twitter:image" content="{SITE_URL}/og-image.png">
{_hreflang_tags("/faq")}
<script type="application/ld+json">{ld_faq}</script>
<script type="application/ld+json">{ld_breadcrumb}</script>
</head>
<body>
<h1>{_escape(faq_title)}</h1>
{qa_html}
</body>
</html>"""
    return HTMLResponse(html)


@router.get("/about", response_class=HTMLResponse)
async def prerender_about(lang: str = Query("en")):
    _titles = {"en": "About SweetSin", "es": "Acerca de SweetSin", "ru": "О SweetSin", "fr": "À propos de SweetSin", "de": "Über SweetSin", "pt": "Sobre o SweetSin", "it": "Informazioni su SweetSin"}
    _titles_fiction = {"en": "About GrimQuill", "es": "Acerca de GrimQuill", "ru": "О GrimQuill", "fr": "À propos de GrimQuill", "de": "Über GrimQuill", "pt": "Sobre o GrimQuill", "it": "Informazioni su GrimQuill"}
    _descriptions = {
        "en": "SweetSin is a platform for creative roleplay and character-driven conversations. Richly detailed character profiles meet multiple language models to create immersive, literary-quality chat experiences.",
        "es": "SweetSin es una plataforma de roleplay creativo y conversaciones con personajes. Perfiles detallados combinados con m\u00faltiples modelos de lenguaje para crear experiencias de chat inmersivas con calidad literaria.",
        "ru": "SweetSin \u2014 \u043f\u043b\u0430\u0442\u0444\u043e\u0440\u043c\u0430 \u0434\u043b\u044f \u0442\u0432\u043e\u0440\u0447\u0435\u0441\u043a\u0438\u0445 \u0440\u043e\u043b\u0435\u0432\u044b\u0445 \u0438\u0433\u0440 \u0438 \u043e\u0431\u0449\u0435\u043d\u0438\u044f \u0441 \u043f\u0435\u0440\u0441\u043e\u043d\u0430\u0436\u0430\u043c\u0438. \u0414\u0435\u0442\u0430\u043b\u044c\u043d\u043e \u043f\u0440\u043e\u0440\u0430\u0431\u043e\u0442\u0430\u043d\u043d\u044b\u0435 \u043f\u0440\u043e\u0444\u0438\u043b\u0438 \u043f\u0435\u0440\u0441\u043e\u043d\u0430\u0436\u0435\u0439 \u0432 \u0441\u043e\u0447\u0435\u0442\u0430\u043d\u0438\u0438 \u0441 \u043c\u043d\u043e\u0436\u0435\u0441\u0442\u0432\u043e\u043c \u044f\u0437\u044b\u043a\u043e\u0432\u044b\u0445 \u043c\u043e\u0434\u0435\u043b\u0435\u0439 \u0434\u043b\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f \u0438\u043c\u043c\u0435\u0440\u0441\u0438\u0432\u043d\u043e\u0433\u043e \u043b\u0438\u0442\u0435\u0440\u0430\u0442\u0443\u0440\u043d\u043e\u0433\u043e \u043e\u043f\u044b\u0442\u0430 \u043e\u0431\u0449\u0435\u043d\u0438\u044f.",
        "fr": "SweetSin est une plateforme de jeu de r\u00f4le cr\u00e9atif et de conversations centr\u00e9es sur les personnages. Des profils richement d\u00e9taill\u00e9s associ\u00e9s \u00e0 de multiples mod\u00e8les de langage pour des exp\u00e9riences de chat immersives et de qualit\u00e9 litt\u00e9raire.",
        "de": "SweetSin ist eine Plattform f\u00fcr kreatives Rollenspiel und charaktergesteuerte Gespr\u00e4che. Detaillierte Charakterprofile kombiniert mit zahlreichen Sprachmodellen f\u00fcr immersive Chat-Erlebnisse in literarischer Qualit\u00e4t.",
        "pt": "SweetSin \u00e9 uma plataforma para roleplay criativo e conversas focadas em personagens. Perfis ricamente detalhados combinados com m\u00faltiplos modelos de linguagem para experi\u00eancias de chat imersivas e com qualidade liter\u00e1ria.",
        "it": "SweetSin \u00e8 una piattaforma per roleplay creativo e conversazioni guidate dai personaggi. Profili ricchi di dettagli combinati con molteplici modelli linguistici per esperienze di chat immersive e di qualit\u00e0 letteraria.",
    }
    _descriptions_fiction = {
        "en": "GrimQuill is an AI-powered interactive fiction and D&D Game Master platform. Choose your path through branching stories, roll dice in tabletop adventures, and shape narratives with every decision.",
        "es": "GrimQuill es una plataforma de ficcion interactiva y Game Master de D&D impulsada por IA. Elige tu camino en historias ramificadas, tira dados en aventuras de mesa y da forma a las narrativas con cada decision.",
        "ru": "GrimQuill -- платформа интерактивной фантастики и D&D Game Master на основе ИИ. Выбирайте путь в ветвящихся историях, бросайте кубики в настольных приключениях и формируйте сюжет каждым решением.",
        "fr": "GrimQuill est une plateforme de fiction interactive et de Game Master D&D alimentee par l'IA. Choisissez votre voie dans des histoires a embranchements, lancez les des et faconnez le recit a chaque decision.",
        "de": "GrimQuill ist eine KI-gesteuerte Plattform fuer interaktive Fiktion und D&D-Spielleitung. Waehle deinen Weg durch verzweigte Geschichten, wuerfle in Tabletop-Abenteuern und forme die Handlung mit jeder Entscheidung.",
        "pt": "GrimQuill e uma plataforma de ficcao interativa e Mestre de Jogo D&D com IA. Escolha seu caminho em historias ramificadas, role dados em aventuras de mesa e molde narrativas com cada decisao.",
        "it": "GrimQuill e una piattaforma di narrativa interattiva e Game Master D&D alimentata dall'IA. Scegli il tuo percorso in storie ramificate, tira i dadi in avventure da tavolo e plasma la trama con ogni decisione.",
    }
    t_src = _titles_fiction if settings.is_fiction_mode else _titles
    d_src = _descriptions_fiction if settings.is_fiction_mode else _descriptions
    title = _brand(t_src.get(lang, t_src["en"]))
    desc = _brand(d_src.get(lang, d_src["en"]))
    canonical = f"{SITE_URL}/{lang}/about"
    ld_breadcrumb = json.dumps(breadcrumb_jsonld([(SITE_NAME, SITE_URL), (title, None)]), ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="{_escape(lang)}">
<head>
<meta charset="UTF-8">
<title>{_escape(title)} | {SITE_NAME}</title>
<meta name="description" content="{_escape(_truncate(desc, 160))}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{_escape(title)}">
<meta property="og:description" content="{_escape(_truncate(desc, 160))}">
<meta property="og:image" content="{SITE_URL}/og-image.png">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{_escape(title)}">
<meta name="twitter:description" content="{_escape(_truncate(desc, 160))}">
{_hreflang_tags("/about")}
<script type="application/ld+json">{ld_breadcrumb}</script>
</head>
<body>
<h1>{_escape(title)}</h1>
<p>{_escape(desc)}</p>
</body>
</html>"""
    return HTMLResponse(html)


@router.get("/terms", response_class=HTMLResponse)
async def prerender_terms(lang: str = Query("en")):
    _titles = {"en": "Terms of Service", "es": "Términos de servicio", "ru": "Условия использования", "fr": "Conditions d'utilisation", "de": "Nutzungsbedingungen", "pt": "Termos de Uso", "it": "Termini di servizio"}
    _descriptions = {
        "en": "Terms of Service for SweetSin — AI character chat platform. Eligibility, user content rules, acceptable use, and disclaimers.",
        "es": "Términos de servicio de SweetSin — plataforma de chat con personajes IA. Elegibilidad, reglas de contenido, uso aceptable y descargos.",
        "ru": "Условия использования SweetSin — платформы для чата с AI-персонажами. Требования, правила контента, допустимое использование и отказ от ответственности.",
        "fr": "Conditions d'utilisation de SweetSin — plateforme de chat avec personnages IA. Éligibilité, règles de contenu, utilisation acceptable et avertissements.",
        "de": "Nutzungsbedingungen von SweetSin — KI-Charakter-Chat-Plattform. Berechtigung, Inhaltsregeln, akzeptable Nutzung und Haftungsausschlüsse.",
        "pt": "Termos de Uso do SweetSin — plataforma de chat com personagens IA. Elegibilidade, regras de conteúdo, uso aceitável e isenções.",
        "it": "Termini di servizio di SweetSin — piattaforma di chat con personaggi IA. Idoneità, regole sui contenuti, uso accettabile e dichiarazioni di non responsabilità.",
    }
    _descriptions_fiction = {
        "en": "Terms of Service for GrimQuill — AI interactive fiction and D&D Game Master platform. Eligibility, user content rules, acceptable use, and disclaimers.",
        "es": "Terminos de servicio de GrimQuill — plataforma de ficcion interactiva y Game Master D&D con IA. Elegibilidad, reglas de contenido, uso aceptable y descargos.",
        "ru": "Условия использования GrimQuill -- платформы интерактивной фантастики и D&D Game Master с ИИ. Требования, правила контента, допустимое использование и отказ от ответственности.",
        "fr": "Conditions d'utilisation de GrimQuill -- plateforme de fiction interactive et Game Master D&D avec IA. Eligibilite, regles de contenu, utilisation acceptable et avertissements.",
        "de": "Nutzungsbedingungen von GrimQuill -- KI-Plattform fuer interaktive Fiktion und D&D-Spielleitung. Berechtigung, Inhaltsregeln, akzeptable Nutzung und Haftungsausschluesse.",
        "pt": "Termos de Uso do GrimQuill -- plataforma de ficcao interativa e Mestre de Jogo D&D com IA. Elegibilidade, regras de conteudo, uso aceitavel e isencoes.",
        "it": "Termini di servizio di GrimQuill -- piattaforma di narrativa interattiva e Game Master D&D con IA. Idoneita, regole sui contenuti, uso accettabile e dichiarazioni di non responsabilita.",
    }
    d_src = _descriptions_fiction if settings.is_fiction_mode else _descriptions
    title = _brand(_titles.get(lang, _titles["en"]))
    desc = _brand(d_src.get(lang, d_src["en"]))
    canonical = f"{SITE_URL}/{lang}/terms"
    ld_breadcrumb = json.dumps(breadcrumb_jsonld([(SITE_NAME, SITE_URL), (title, None)]), ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="{_escape(lang)}">
<head>
<meta charset="UTF-8">
<title>{_escape(title)} | {SITE_NAME}</title>
<meta name="description" content="{_escape(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{_escape(title)}">
<meta property="og:description" content="{_escape(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
{_hreflang_tags("/terms")}
<script type="application/ld+json">{ld_breadcrumb}</script>
</head>
<body>
<h1>{_escape(title)}</h1>
<p>{_escape(desc)}</p>
</body>
</html>"""
    return HTMLResponse(html)


@router.get("/privacy", response_class=HTMLResponse)
async def prerender_privacy(lang: str = Query("en")):
    _titles = {"en": "Privacy Policy", "es": "Política de privacidad", "ru": "Политика конфиденциальности", "fr": "Politique de confidentialité", "de": "Datenschutzrichtlinie", "pt": "Política de Privacidade", "it": "Informativa sulla privacy"}
    _descriptions = {
        "en": "Privacy Policy for SweetSin — how we collect, use, and protect your data. Your conversations are private.",
        "es": "Política de privacidad de SweetSin — cómo recopilamos, usamos y protegemos tus datos. Tus conversaciones son privadas.",
        "ru": "Политика конфиденциальности SweetSin — как мы собираем, используем и защищаем ваши данные. Ваши разговоры приватны.",
        "fr": "Politique de confidentialité de SweetSin — comment nous collectons, utilisons et protégeons vos données. Vos conversations sont privées.",
        "de": "Datenschutzrichtlinie von SweetSin — wie wir Ihre Daten erheben, verwenden und schützen. Ihre Gespräche sind privat.",
        "pt": "Política de Privacidade do SweetSin — como coletamos, usamos e protegemos seus dados. Suas conversas são privadas.",
        "it": "Informativa sulla privacy di SweetSin — come raccogliamo, utilizziamo e proteggiamo i tuoi dati. Le tue conversazioni sono private.",
    }
    _descriptions_fiction = {
        "en": "Privacy Policy for GrimQuill — how we collect, use, and protect your data. Your adventures and conversations are private.",
        "es": "Politica de privacidad de GrimQuill -- como recopilamos, usamos y protegemos tus datos. Tus aventuras y conversaciones son privadas.",
        "ru": "Политика конфиденциальности GrimQuill -- как мы собираем, используем и защищаем ваши данные. Ваши приключения и разговоры приватны.",
        "fr": "Politique de confidentialite de GrimQuill -- comment nous collectons, utilisons et protegeons vos donnees. Vos aventures et conversations sont privees.",
        "de": "Datenschutzrichtlinie von GrimQuill -- wie wir Ihre Daten erheben, verwenden und schuetzen. Ihre Abenteuer und Gespraeche sind privat.",
        "pt": "Politica de Privacidade do GrimQuill -- como coletamos, usamos e protegemos seus dados. Suas aventuras e conversas sao privadas.",
        "it": "Informativa sulla privacy di GrimQuill -- come raccogliamo, utilizziamo e proteggiamo i tuoi dati. Le tue avventure e conversazioni sono private.",
    }
    d_src = _descriptions_fiction if settings.is_fiction_mode else _descriptions
    title = _brand(_titles.get(lang, _titles["en"]))
    desc = _brand(d_src.get(lang, d_src["en"]))
    canonical = f"{SITE_URL}/{lang}/privacy"
    ld_breadcrumb = json.dumps(breadcrumb_jsonld([(SITE_NAME, SITE_URL), (title, None)]), ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="{_escape(lang)}">
<head>
<meta charset="UTF-8">
<title>{_escape(title)} | {SITE_NAME}</title>
<meta name="description" content="{_escape(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{_escape(title)}">
<meta property="og:description" content="{_escape(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
{_hreflang_tags("/privacy")}
<script type="application/ld+json">{ld_breadcrumb}</script>
</head>
<body>
<h1>{_escape(title)}</h1>
<p>{_escape(desc)}</p>
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

    ld_graph = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            website_jsonld(),
            {
                "@type": "Organization",
                "name": SITE_NAME,
                "url": SITE_URL,
                "description": "AI Interactive Fiction & D&D Game Master" if settings.is_fiction_mode else "AI Character Chat Platform",
            },
            software_application_jsonld(),
        ],
    }, ensure_ascii=False)

    char_links = []
    for c in characters:
        tr = (c.translations or {}).get(lang)
        name = _escape(tr["name"] if tr and "name" in tr else c.name)
        # Hide NSFW taglines from bots — show only name
        _cr = getattr(c.content_rating, 'value', c.content_rating) or "sfw"
        if _cr == "nsfw":
            tagline = ""
        else:
            tagline = _escape(tr["tagline"] if tr and "tagline" in tr else (c.tagline or ""))
        url = f"{SITE_URL}/{lang}/c/{c.slug}"
        line = f'<li><a href="{url}">{name}</a> — {tagline}</li>' if tagline else f'<li><a href="{url}">{name}</a></li>'
        char_links.append(line)

    canonical = f"{SITE_URL}/{lang}"

    if settings.is_fiction_mode:
        _home_title = f"{SITE_NAME} — AI Interactive Fiction &amp; D&amp;D Game Master"
        _home_desc = "AI-powered interactive fiction and D&D Game Master. Choose your path, roll dice, shape the story."
        _home_og_title = f"{SITE_NAME} — Write Your Fate"
        _home_og_desc = "AI Interactive Fiction & D&D Game Master. Choose your path, roll dice, shape the story."
        _home_h1 = f"{SITE_NAME} — AI Interactive Fiction & D&D"
        _home_p = "AI-powered interactive fiction and D&D Game Master. Choose your path, roll dice, shape the story."
    else:
        _home_title = f"{SITE_NAME} — AI Character Chat | Roleplay &amp; Fantasy"
        _home_desc = "Chat with unique AI characters. Immersive roleplay, creative storytelling, and endless fantasy."
        _home_og_title = f"{SITE_NAME} — Where Fantasy Comes Alive"
        _home_og_desc = "AI Character Chat Platform. Immersive roleplay, creative storytelling, endless possibilities."
        _home_h1 = f"{SITE_NAME} — AI Character Chat"
        _home_p = "Chat with unique AI characters. Immersive roleplay, creative storytelling, and endless fantasy."

    html = f"""<!DOCTYPE html>
<html lang="{_escape(lang)}">
<head>
<meta charset="UTF-8">
<title>{_home_title}</title>
<meta name="description" content="{_home_desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{_home_og_title}">
<meta property="og:description" content="{_home_og_desc}">
<meta property="og:image" content="{SITE_URL}/og-image.png">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:locale" content="{lang}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{_home_og_title}">
<meta name="twitter:description" content="{_home_og_desc}">
<meta name="twitter:image" content="{SITE_URL}/og-image.png">
{_hreflang_tags("")}
<script type="application/ld+json">{ld_graph}</script>
</head>
<body>
<h1>{_home_h1}</h1>
<p>{_home_p}</p>
<h2>Characters</h2>
<ul>
{"".join(char_links)}
</ul>
</body>
</html>"""
    return HTMLResponse(html)


@router.get("/campaigns", response_class=HTMLResponse)
async def prerender_campaigns(
    lang: str = Query("en"),
    db: AsyncSession = Depends(get_db),
):
    """Prerender campaigns/adventures page for bots (fiction mode)."""
    # Query DnD-tagged characters (adventures)
    result = await db.execute(
        select(Character)
        .where(
            Character.is_public == True,
            Character.slug.isnot(None),
            Character.tags.contains("dnd"),
        )
        .order_by(Character.chat_count.desc())
        .limit(50)
    )
    adventures = result.scalars().all()

    canonical = f"{SITE_URL}/{lang}/campaigns"
    title = f"D&D Campaigns — AI Game Master | {SITE_NAME}"
    desc = f"Play D&D 5e with an AI Game Master on {SITE_NAME}. Roll dice, track combat, explore open worlds. {len(adventures)} adventures available."

    adv_links = []
    for c in adventures:
        tr = (c.translations or {}).get(lang)
        name = _escape(tr["name"] if tr and "name" in tr else c.name)
        tagline = _escape(tr["tagline"] if tr and "tagline" in tr else (c.tagline or ""))
        url = f"{SITE_URL}/{lang}/c/{c.slug}"
        line = f'<li><a href="{url}">{name}</a> — {tagline}</li>' if tagline else f'<li><a href="{url}">{name}</a></li>'
        adv_links.append(line)

    ld_breadcrumb = json.dumps(breadcrumb_jsonld([
        (SITE_NAME, SITE_URL),
        ("D&D Campaigns", None),
    ]), ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="{_escape(lang)}">
<head>
<meta charset="UTF-8">
<title>{_escape(title)}</title>
<meta name="description" content="{_escape(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="D&D Campaigns — AI Game Master">
<meta property="og:description" content="{_escape(desc)}">
<meta property="og:image" content="{SITE_URL}/og-image.png">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:locale" content="{lang}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="D&D Campaigns — AI Game Master">
<meta name="twitter:description" content="{_escape(desc)}">
<meta name="twitter:image" content="{SITE_URL}/og-image.png">
{_hreflang_tags("/campaigns")}
<script type="application/ld+json">{ld_breadcrumb}</script>
</head>
<body>
<h1>D&D Campaigns — AI Game Master</h1>
<p>{_escape(desc)}</p>
<h2>Adventures</h2>
<ul>
{"".join(adv_links)}
</ul>
<a href="{SITE_URL}/{lang}">Back to {SITE_NAME}</a>
</body>
</html>"""
    return HTMLResponse(html)


# Sitemap cache (regenerated every 2 hours)
_sitemap_cache: str = ""
_sitemap_cache_time: float = 0
_SITEMAP_TTL = 7200  # 2 hours


@router.api_route("/sitemap.xml", methods=["GET", "HEAD"])
async def sitemap(db: AsyncSession = Depends(get_db)):
    import time as _time

    global _sitemap_cache, _sitemap_cache_time
    if _sitemap_cache and (_time.monotonic() - _sitemap_cache_time) < _SITEMAP_TTL:
        return Response(content=_sitemap_cache, media_type="application/xml")

    # Quality gate: only include characters with substantial content
    result = await db.execute(
        select(Character.slug, Character.updated_at, Character.avatar_url, Character.name, Character.content_rating)
        .where(
            Character.is_public == True,
            Character.slug.isnot(None),
            (func.length(func.coalesce(Character.scenario, ""))
             + func.length(func.coalesce(Character.personality, ""))) >= 100,
        )
        .order_by(Character.updated_at.desc())
    )
    characters = result.all()

    now = datetime.utcnow().strftime("%Y-%m-%d")

    def alternates(path: str) -> str:
        """xhtml:link alternates for all languages."""
        links = []
        for l in LANGS:
            url = f"{SITE_URL}/{l}{path}" if path else f"{SITE_URL}/{l}"
            links.append(f'  <xhtml:link rel="alternate" hreflang="{l}" href="{url}"/>')
        links.append(f'  <xhtml:link rel="alternate" hreflang="x-default" href="{SITE_URL}/en{path}"/>')
        return "\n".join(links)

    def image_tag(avatar_url: str | None, name: str) -> str:
        if not avatar_url:
            return ""
        img_url = avatar_url if avatar_url.startswith("http") else f"{SITE_URL}{avatar_url}"
        safe_name = name.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")
        return (
            f'\n  <image:image>\n    <image:loc>{img_url}</image:loc>'
            f'\n    <image:title>{safe_name}</image:title>\n  </image:image>'
        )

    urls = []

    # Root URL without language prefix
    urls.append(
        f'<url>\n  <loc>{SITE_URL}/</loc>\n  <lastmod>{now}</lastmod>'
        f'\n  <changefreq>daily</changefreq>\n  <priority>1.0</priority>\n</url>'
    )

    # Static pages × languages
    static_pages = [
        ("", "daily", "1.0", now),
        ("/about", "monthly", "0.3", now),
        ("/terms", "monthly", "0.2", now),
        ("/privacy", "monthly", "0.2", now),
        ("/faq", "monthly", "0.3", now),
    ]
    # Campaigns page (fiction mode only)
    if settings.is_fiction_mode:
        static_pages.append(("/campaigns", "weekly", "0.7", now))
    # Tag landing pages
    for tp in TAG_PAGES:
        static_pages.append((f"/tags/{tp['slug']}", "weekly", "0.7", now))
    for path, freq, prio, lastmod in static_pages:
        for l in LANGS:
            loc = f"{SITE_URL}/{l}{path}" if path else f"{SITE_URL}/{l}"
            urls.append(
                f"<url>\n  <loc>{loc}</loc>\n  <lastmod>{lastmod}</lastmod>"
                f"\n  <changefreq>{freq}</changefreq>\n  <priority>{prio}</priority>"
                f"\n{alternates(path)}\n</url>"
            )

    # Character pages × languages (with image extension)
    for slug, updated_at, avatar_url, name, content_rating in characters:
        lastmod = updated_at.strftime("%Y-%m-%d") if updated_at else now
        path = f"/c/{slug}"
        img = image_tag(avatar_url, name)
        _cr = getattr(content_rating, 'value', content_rating) or "sfw"
        prio = "0.4" if _cr == "nsfw" else "0.7"
        for l in LANGS:
            urls.append(
                f"<url>\n  <loc>{SITE_URL}/{l}{path}</loc>\n  <lastmod>{lastmod}</lastmod>"
                f"\n  <changefreq>weekly</changefreq>\n  <priority>{prio}</priority>"
                f"{img}\n{alternates(path)}\n</url>"
            )

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
{chr(10).join(urls)}
</urlset>"""

    _sitemap_cache = xml
    _sitemap_cache_time = _time.monotonic()
    return Response(content=xml, media_type="application/xml")


@router.api_route("/feed.xml", methods=["GET", "HEAD"])
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
        # Use English translations if available (RSS links to /en/)
        tr = (c.translations or {}).get("en")
        name = _escape(tr["name"] if tr and "name" in tr else c.name)
        _cr = getattr(c.content_rating, 'value', c.content_rating) or "sfw"
        # Hide NSFW details from feed
        if _cr == "nsfw":
            tagline = ""
            scenario_text = name
        else:
            tagline = _escape(tr["tagline"] if tr and "tagline" in tr else (c.tagline or ""))
            scenario_text = tr["scenario"] if tr and "scenario" in tr else (c.scenario or c.tagline or "")
        desc = _escape(_truncate(scenario_text, 300))
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
<title>{SITE_NAME} — {"New Adventures" if settings.is_fiction_mode else "New AI Characters"}</title>
<link>{SITE_URL}</link>
<description>{"AI interactive fiction and D&D adventures" if settings.is_fiction_mode else f"Latest AI characters for roleplay and creative storytelling"} on {SITE_NAME}</description>
<language>en</language>
<lastBuildDate>{now}</lastBuildDate>
<atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml" />
{"".join(items)}
</channel>
</rss>"""
    return Response(content=xml, media_type="application/rss+xml; charset=utf-8")


INDEXNOW_KEY = "b1e4d3a7f6c8e2d9a5b0c7f1e3d6a8b4"


@router.api_route(f"/{INDEXNOW_KEY}.txt", methods=["GET", "HEAD"])
async def indexnow_key():
    return Response(content=INDEXNOW_KEY, media_type="text/plain")


@router.api_route("/robots.txt", methods=["GET", "HEAD"])
async def robots():
    nsfw_block = "\nDisallow: /*nsfw*\n" if not settings.is_fiction_mode else ""
    content = f"""User-agent: *
Allow: /
Disallow: /api/
Disallow: /chat/
Disallow: /profile
Disallow: /admin/
Disallow: /favorites
Disallow: /create
Disallow: /auth
{nsfw_block}
Sitemap: {SITE_URL}/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")
