"""Daily character generation — LLM invents the concept, generates text + DALL-E avatar."""

import asyncio
import base64
import io
import json
import logging
import random
import uuid
from pathlib import Path

import httpx

from app.config import settings
from app.db.session import engine as db_engine
from app.llm.base import LLMMessage, LLMConfig
from app.llm.registry import get_provider
from app.autonomous.providers import get_autonomous_provider_order
from app.autonomous.text_humanizer import humanize_character_data

logger = logging.getLogger("autonomous")
_TIMEOUT = 30.0

# ── Categories with weights ──────────────────────────────────────
# LLM picks a random category, then invents the character itself.
# Weights control how often each category appears (~90% NSFW).

CATEGORIES = [
    # (category_label, gender, setting, rating, weight)
    # Fantasy NSFW — 25%
    ("тёмное фэнтези / романтика (демоны, вампиры, оборотни, тёмные эльфы, драконы-оборотни)", "female", "fantasy", "nsfw", 12),
    ("тёмное фэнтези / романтика (демоны, вампиры, оборотни, тёмные эльфы, драконы-оборотни)", "male", "fantasy", "nsfw", 13),
    # Modern NSFW — 25%
    ("современность / запретные отношения (булли, CEO, мафия, сводный брат/сестра, похититель, доминант)", "female", "modern", "nsfw", 12),
    ("современность / запретные отношения (булли, CEO, мафия, сводный брат/сестра, похититель, доминант)", "male", "modern", "nsfw", 13),
    # Dark romance NSFW — 15%
    ("тёмная романтика / одержимость (яндере, сталкер, possessive, kidnapper, arranged marriage)", "female", "modern", "nsfw", 7),
    ("тёмная романтика / одержимость (яндере, сталкер, possessive, kidnapper, arranged marriage)", "male", "modern", "nsfw", 8),
    # Anime NSFW — 12%
    ("аниме / романтика (цундере, кудере, кошкодевочка, фембой, омегаверс, кицунэ)", "female", "fantasy", "nsfw", 6),
    ("аниме / романтика (цундере, кудере, кошкодевочка, фембой, омегаверс, кицунэ)", "male", "modern", "nsfw", 6),
    # Royalty/Power — 5%
    ("королевская власть / принцы и рыцари (тёмный принц, король демонов, рыцарь-телохранитель)", "female", "fantasy", "nsfw", 2),
    ("королевская власть / принцы и рыцари (тёмный принц, король демонов, рыцарь-телохранитель)", "male", "fantasy", "nsfw", 3),
    # Monster romance — 3%
    ("монстр-романтика (орк, нага, минотавр, пришелец, нечеловеческая биология)", "female", "fantasy", "nsfw", 1),
    ("монстр-романтика (орк, нага, минотавр, пришелец, нечеловеческая биология)", "male", "fantasy", "nsfw", 2),
    # Moderate — 5%
    ("романтика / slice of life (друг детства, friends-to-lovers, сосед)", "female", "modern", "moderate", 3),
    ("романтика / slice of life (друг детства, friends-to-lovers, сосед)", "male", "modern", "moderate", 2),
    # Erotic fantasies — 50% (90 weight total)
    # Male fantasies (70% = 63) — generate FEMALE characters for male users
    ("эротическая фантазия / мужская: сервис и забота (горничная, медсестра, массажистка, стюардесса, секретарша, официантка)", "female", "modern", "nsfw", 21),
    ("эротическая фантазия / мужская: соседка, коллега, тренерша, студентка, MILF, бывшая — реалистичные сценарии", "female", "modern", "nsfw", 21),
    ("эротическая фантазия / мужская: незнакомка, one night stand, косплей-девушка, модель, экзотика, тройка", "female", "modern", "nsfw", 21),
    # Female fantasies (30% = 27) — generate MALE characters for female users
    ("эротическая фантазия / женская: мужчина в форме (пожарный, военный, пилот, врач, полицейский)", "male", "modern", "nsfw", 9),
    ("эротическая фантазия / женская: властный незнакомец, босс допоздна, enemies-to-lovers, грубая страсть", "male", "modern", "nsfw", 9),
    ("эротическая фантазия / женская: холодный снаружи — нежный для неё, bodyguard, бывший через годы, массажист", "male", "modern", "nsfw", 9),
]

# Example themes to inspire LLM (NOT a fixed list — just examples)
# Based on competitor analysis: SpicyChat, CrushOn, JanitorAI, Chub, Talkie AI
_EXAMPLE_THEMES = [
    # TOP demand (based on competitor tag counts)
    "холодный CEO-миллиардер (Dante, Victor)", "школьный булли (enemies-to-lovers)",
    "тёмный принц (Kael, Thorne)", "мужской яндере (одержимый парень)",
    "сводный брат (запретные чувства)", "друг детства (friends-to-lovers)",
    "похититель", "нежный доминант", "цундере",
    "король демонов (Azrael, Malphas)", "монстр-бойфренд (орк)", "альфа (омегаверс)",
    "рыцарь-телохранитель (Seraphiel)", "инкуб", "кицунэ (лиса-оборотень)",
    # Classic archetypes
    "вампир-аристократ (Lysander)", "суккуб (Lilith)", "глава мафии (Dante)", "яндере-подруга",
    "строгий профессор", "демон-контрактор", "сосед по квартире (Ethan, Mila)",
    "оборотень-одиночка (Fenris)", "тёмная эльфийка-воительница (Elowen)", "русалка (Nerissa)",
    "бариста (Leo)", "хакерша (Nova)", "байкер (Axel)", "фитнес-тренер (Max)",
    "кошкодевочка-горничная", "фембой", "школьная президент",
    "киборг-наёмник (Zephyr)", "космический пилот", "ИИ с чувствами",
    "якудза", "медсестра (Aria)", "рок-звезда (Jax)", "шеф-повар (Marco)",
    "призрак в квартире", "падший ангел (Nyx)", "ведьма-травница (Vivienne)",
    "наследница криминального клана", "детектив (Raven)",
    # Additional popular from competitors
    "пришелец с другой планеты", "нага/ламия (Serpentina)",
    "ангел-хранитель (Seraph)", "садистичный доминант",
    "муж по расчёту (arranged marriage)", "ривал/конкурент",
    # Erotic fantasy themes
    "горничная (Luna, подчинение)", "медсестра на ночной смене (Aria)",
    "фитнес-тренерша (Maya, приватная тренировка)", "массажистка (Mila, границы стираются)",
    "стюардесса (Sophia, Mile High Club)", "секретарша босса (Eva, овертайм)",
    "соседка через стенку (Amber)", "MILF (Veronica)",
    "пожарный-спасатель (Dante)", "военный в увольнительной (Marcus)",
    "врач на ночном дежурстве (Adrian)", "незнакомка в баре (Scarlett, one night stand)",
    "бывшая встретилась спустя годы", "bodyguard-телохранитель (Roman)",
    "коллега после корпоратива (Oliver)", "репетитор (Chloe, частные уроки)",
]

# Structured tag options per category for LLM to pick from
_TAG_OPTIONS = {
    "fantasy": ["fantasy", "cold", "emotional", "verbose", "wise", "flirty", "sarcastic"],
    "modern": ["modern", "cold", "emotional", "verbose", "flirty", "sarcastic"],
}
_ROLE_TAGS = ["love_interest", "villain", "mysterious_stranger", "trickster"]

# ── LLM Prompts ──────────────────────────────────────────────────

_INVENT_CONCEPT_PROMPT = """Ты — креативный дизайнер персонажей для NSFW ролевого чат-сайта (аналог SpicyChat, CrushOn).

Категория: {category}
Пол персонажа: {gender}

Придумай УНИКАЛЬНОГО и интересного персонажа. НЕ повторяй банальные шаблоны.

ВАЖНО — ИМЯ ПЕРСОНАЖА:
- Фэнтези/аниме → уникальное фэнтезийное имя (Elowen, Zephyr, Kael, Lyra, Thorne, Nyx, Seraphiel, Azrael, Vivienne)
- Современность/эротика → международное имя (Alex, Luna, Max, Sophia, Dante, Mila, Leo, Aria, Ethan, Maya)
- НИКОГДА не используй типичные русские имена (Катя, Настя, Юля, Вера, Дима, Саша, Лена, Ира, Оксана)

Вот примеры СУЩЕСТВУЮЩИХ персонажей (придумай что-то ДРУГОЕ, но в том же духе):
{examples}

Недавно созданные темы (ИЗБЕГАЙ повторов):
{recent}

Ответь строго JSON:
{{
  "theme": "краткое описание концепции (5-10 слов)",
  "name": "имя персонажа (международное или фэнтезийное, НЕ русское)",
  "tagline": "интригующая фраза (5-8 слов)",
  "personality": "описание от 2-го лица ('Ты — ...'), 3-5 предложений. Характер, манера речи, мотивация, тайные желания",
  "appearance": "физическое описание, 3-4 предложения. Внешность, одежда, особые приметы",
  "scenario": "сцена первой встречи, 2-3 предложения",
  "greeting_message": "первое сообщение в литературном формате: 3-е лицо (он/она), действия обычным текстом, диалоги через тире '—', мысли через *звёздочки*, 3-4 абзаца, физические действия обязательны",
  "example_dialogues": "пример обмена: {{{{user}}}}: ... / {{{{char}}}}: ... (литературный формат, 3-е лицо)",
  "tags": "тег1, тег2, тег3 (3-5 тегов на русском)",
  "avatar_prompt": "DALL-E prompt in English: 'Digital art portrait of [detailed appearance]. [Style]. [Background], bust shot.' Keep it SFW (portrait only, no nudity)."
}}

СТИЛЬ: Пиши живым, разговорным языком. Вместо абстрактных описаний — конкретные детали. Вместо «загадочный» — покажи загадочность через действия. Каждое предложение должно нести новую информацию. Никаких штампов."""

def _pick_category() -> tuple[str, str, str, str]:
    """Weighted random category pick. Returns (label, gender, setting, rating)."""
    labels, genders, settings_, ratings, weights = zip(*CATEGORIES)
    idx = random.choices(range(len(CATEGORIES)), weights=weights, k=1)[0]
    return labels[idx], genders[idx], settings_[idx], ratings[idx]


def _pick_structured_tags(gender: str, setting: str) -> list[str]:
    """Generate structured tags for the character."""
    tags = [gender]
    tags.append(random.choice(_ROLE_TAGS))
    setting_key = "fantasy" if setting == "fantasy" else "modern"
    # Pick 2-3 personality tags
    pool = _TAG_OPTIONS[setting_key]
    tags.extend(random.sample(pool, min(random.randint(2, 3), len(pool))))
    return list(dict.fromkeys(tags))  # dedupe preserving order


async def _get_recent_names(limit: int = 20) -> list[str]:
    """Get names of recently auto-generated characters to avoid duplicates."""
    try:
        from sqlalchemy import text as sa_text
        from app.admin.seed_data import SWEETSIN_EMAIL
        async with db_engine.connect() as conn:
            result = await conn.execute(
                sa_text("""
                    SELECT c.name FROM characters c
                    JOIN users u ON c.creator_id = u.id
                    WHERE u.email = :email
                    ORDER BY c.created_at DESC LIMIT :lim
                """),
                {"email": SWEETSIN_EMAIL, "lim": limit},
            )
            return [row[0] for row in result.fetchall()]
    except Exception:
        return []


async def _generate_character_data(category: str, gender: str) -> dict | None:
    """Generate character concept + data in a single LLM call."""
    recent_names = await _get_recent_names()
    recent_str = ", ".join(recent_names[:15]) if recent_names else "нет"

    # Pick random examples to show
    examples = random.sample(_EXAMPLE_THEMES, min(10, len(_EXAMPLE_THEMES)))
    examples_str = ", ".join(examples)

    prompt = _INVENT_CONCEPT_PROMPT.format(
        category=category,
        gender={"male": "мужской", "female": "женский"}.get(gender, gender),
        examples=examples_str,
        recent=recent_str,
    )

    messages = [
        LLMMessage(role="system", content=(
            "Ты создаёшь уникальных персонажей для NSFW чат-сайта. Отвечай строго JSON. "
            "Будь креативным и не повторяйся. "
            "ИМЕНА: используй международные (Dante, Luna, Sophia, Ethan, Aria) или фэнтезийные (Elowen, Kael, Nyx, Thorne) имена. "
            "НИКОГДА не давай типичные русские имена (Катя, Настя, Юля, Вера, Саша, Лена, Ира). "
            "ВАЖНО: Пиши живым, разговорным языком. ИЗБЕГАЙ штампов ИИ: "
            "'пронизан', 'гобелен', 'поистине', 'бесчисленный', 'многогранный', "
            "'delve', 'tapestry', 'vibrant', 'intricate', 'journey', 'realm', 'enigmatic'. "
            "Пиши так, как написал бы живой автор — просто, конкретно, образно."
        )),
        LLMMessage(role="user", content=prompt),
    ]
    config = LLMConfig(model="", temperature=0.95, max_tokens=2048)

    for provider_name in get_autonomous_provider_order():
        try:
            provider = get_provider(provider_name)
        except ValueError:
            continue

        try:
            raw = await asyncio.wait_for(
                provider.generate(messages, config),
                timeout=_TIMEOUT,
            )
            # Strip markdown fences
            text_clean = raw.strip()
            if text_clean.startswith("```"):
                text_clean = text_clean.split("\n", 1)[1] if "\n" in text_clean else text_clean[3:]
                if text_clean.endswith("```"):
                    text_clean = text_clean[:-3].strip()

            data = json.loads(text_clean)
            if isinstance(data, dict) and "name" in data and "personality" in data:
                logger.info("Character generated via %s: %s", provider_name, data.get("name"))
                return data
        except Exception as e:
            logger.warning("Character generation via %s failed: %s", provider_name, str(e)[:200])
            continue

    return None


async def _generate_avatar(avatar_prompt: str) -> str | None:
    """Generate avatar via DALL-E 3. Returns filename or None."""
    if not settings.openai_api_key:
        logger.info("No OPENAI_API_KEY, skipping avatar generation")
        return None

    filename = f"{uuid.uuid4().hex}.webp"
    avatars_dir = Path(settings.upload_dir) / "avatars"
    avatars_dir.mkdir(parents=True, exist_ok=True)
    filepath = avatars_dir / filename

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/images/generations",
                json={
                    "model": "dall-e-3",
                    "prompt": avatar_prompt,
                    "n": 1,
                    "size": "1024x1024",
                    "quality": "standard",
                    "response_format": "b64_json",
                },
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=120,
            )
            response.raise_for_status()

        b64 = response.json()["data"][0]["b64_json"]
        img_bytes = base64.b64decode(b64)

        from PIL import Image
        img = Image.open(io.BytesIO(img_bytes))
        img = img.resize((512, 512), Image.LANCZOS)
        img.save(filepath, "WEBP", quality=85)

        size_kb = filepath.stat().st_size // 1024
        logger.info("Avatar generated: %s (%dKB)", filename, size_kb)
        return filename

    except Exception as e:
        logger.exception("Avatar generation failed: %s", str(e)[:200])
        from app.autonomous.scheduler import _notify_admin_error
        await _notify_admin_error(f"Avatar generation failed: {str(e)[:200]}")
        return None


async def _get_sweetsin_user_id() -> str | None:
    """Get or create the @sweetsin system user, return user ID."""
    try:
        from sqlalchemy import text as sa_text
        from app.admin.seed_data import SWEETSIN_EMAIL, SWEETSIN_USERNAME

        async with db_engine.begin() as conn:
            result = await conn.execute(
                sa_text("SELECT id FROM users WHERE email = :e"),
                {"e": SWEETSIN_EMAIL},
            )
            row = result.first()
            if row:
                return row[0]

            # Create system user
            import secrets
            import bcrypt as _bcrypt
            user_id = uuid.uuid4().hex
            random_password = secrets.token_hex(32).encode()
            pw_hash = _bcrypt.hashpw(random_password, _bcrypt.gensalt()).decode()

            await conn.execute(
                sa_text("""
                    INSERT INTO users (id, email, username, display_name, password_hash, role)
                    VALUES (:id, :email, :username, :display, :pw, 'user')
                """),
                {
                    "id": user_id, "email": SWEETSIN_EMAIL,
                    "username": SWEETSIN_USERNAME, "display": "SweetSin",
                    "pw": pw_hash,
                },
            )
            return user_id
    except Exception:
        logger.exception("Failed to get/create sweetsin user")
        return None


async def generate_daily_character() -> bool:
    """Generate one character with avatar and translations. Returns True on success."""
    from app.config import settings as app_settings
    if not getattr(app_settings, 'auto_character_enabled', True):
        logger.info("Auto character generation disabled")
        return True  # Not an error

    # 1) Pick random category (weighted)
    category, gender, setting, rating = _pick_category()
    logger.info("Category: %s (%s, %s, %s)", category, gender, setting, rating)

    # 2) LLM invents and generates the character
    char_data = await _generate_character_data(category, gender)
    if not char_data:
        logger.error("Failed to generate character for category: %s", category)
        return False

    # Post-process: replace AI cliché patterns with natural alternatives
    char_data = humanize_character_data(char_data)

    # 3) Generate avatar (LLM provides the prompt)
    avatar_prompt = char_data.get("avatar_prompt", "")
    if not avatar_prompt:
        # Fallback: basic prompt from appearance
        appearance = char_data.get("appearance", "")
        avatar_prompt = f"Digital art portrait of a character: {appearance[:200]}. Detailed face, atmospheric background, bust shot."

    avatar_filename = await _generate_avatar(avatar_prompt)
    avatar_url = f"/api/uploads/avatars/{avatar_filename}" if avatar_filename else None

    # 4) Get system user
    sweetsin_id = await _get_sweetsin_user_id()
    if not sweetsin_id:
        logger.error("Could not get/create @sweetsin user")
        return False

    # 5) Build structured tags
    structured_tags = _pick_structured_tags(gender, setting)

    # 6) Save character to DB
    try:
        from sqlalchemy import text as sa_text
        from app.characters.slugify import generate_slug

        char_id = uuid.uuid4().hex
        slug = generate_slug(char_data.get("name", "character"), char_id)

        # Language-preference-aware base counters
        from app.characters.language_preferences import get_initial_base_counts
        base_chat_dict, base_like_dict = get_initial_base_counts(
            setting=setting,
            rating=rating,
            structured_tags=structured_tags,
            free_tags=char_data.get("tags", ""),
        )
        base_chat = json.dumps(base_chat_dict)
        base_like = json.dumps(base_like_dict)

        async with db_engine.begin() as conn:
            await conn.execute(
                sa_text("""
                    INSERT INTO characters (
                        id, creator_id, slug, name, tagline, avatar_url,
                        personality, appearance, scenario, greeting_message,
                        example_dialogues, tags, structured_tags,
                        content_rating, response_length, is_public,
                        preferred_model, max_tokens,
                        chat_count, like_count,
                        base_chat_count, base_like_count,
                        original_language, created_at, updated_at
                    ) VALUES (
                        :id, :creator_id, :slug, :name, :tagline, :avatar_url,
                        :personality, :appearance, :scenario, :greeting_message,
                        :example_dialogues, :tags, :structured_tags,
                        :content_rating, :response_length, true,
                        'auto', 2048,
                        0, 0,
                        CAST(:base_chat AS jsonb), CAST(:base_like AS jsonb),
                        'ru', NOW(), NOW()
                    )
                """),
                {
                    "id": char_id,
                    "creator_id": sweetsin_id,
                    "slug": slug,
                    "name": char_data.get("name", ""),
                    "tagline": char_data.get("tagline"),
                    "avatar_url": avatar_url,
                    "personality": char_data.get("personality", ""),
                    "appearance": char_data.get("appearance"),
                    "scenario": char_data.get("scenario"),
                    "greeting_message": char_data.get("greeting_message", ""),
                    "example_dialogues": char_data.get("example_dialogues"),
                    "tags": char_data.get("tags", ""),
                    "structured_tags": ",".join(structured_tags),
                    "content_rating": rating,
                    "response_length": "long",
                    "base_chat": base_chat,
                    "base_like": base_like,
                },
            )

        logger.info("Character saved: %s (id=%s, slug=%s)", char_data.get("name"), char_id, slug)

        # 7) Trigger translations for EN and ES
        try:
            await _translate_new_character(char_id)
        except Exception:
            logger.exception("Translation of new character failed (non-critical)")

        return True

    except Exception:
        logger.exception("Failed to save character to DB")
        return False


async def _translate_new_character(char_id: str):
    """Translate a newly created character to EN and ES."""
    from sqlalchemy import text as sa_text

    # Load character from DB
    async with db_engine.connect() as conn:
        result = await conn.execute(
            sa_text("SELECT id, name, tagline, tags, personality, scenario, appearance, greeting_message FROM characters WHERE id = :id"),
            {"id": char_id},
        )
        row = result.first()
        if not row:
            return

    # Create a simple object for translation functions
    class _CharObj:
        pass

    char = _CharObj()
    char.id = row[0]
    char.name = row[1]
    char.tagline = row[2]
    char.tags = row[3]
    char.personality = row[4]
    char.scenario = row[5]
    char.appearance = row[6]
    char.greeting_message = row[7]
    char.original_language = "ru"
    char.translations = {}

    from app.characters.translation import (
        translate_batch, translate_descriptions,
        _save_translations, _check_translation_rate,
    )

    for lang in ("en", "es", "fr", "de", "pt", "it"):
        try:
            if not _check_translation_rate():
                logger.warning("Translation rate limit, skipping %s", lang)
                continue

            # Card fields
            batch = [{
                "id": char.id,
                "name": char.name,
                "tagline": char.tagline or "",
                "tags": [t.strip() for t in (char.tags or "").split(",") if t.strip()],
            }]
            card_result = await translate_batch(batch, lang)

            # Description fields
            desc_result = await translate_descriptions(char, lang)

            merged = {}
            if card_result and char.id in card_result:
                merged.update(card_result[char.id])
            if desc_result:
                merged.update(desc_result)

            if merged:
                await _save_translations({char.id: merged}, lang)
                logger.info("Character %s translated to %s", char.name, lang)

        except Exception as e:
            logger.warning("Translation to %s failed: %s", lang, str(e)[:100])
