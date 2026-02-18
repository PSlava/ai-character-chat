import json
import logging
import re
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.middleware import get_current_user, get_current_user_optional
from app.db.session import get_db
from app.db.models import Character, ContentRating, Vote, CharacterRelation
from app.characters.schemas import CharacterCreate, CharacterUpdate, GenerateFromStoryRequest
from app.characters import service
from app.characters.serializers import character_to_dict
from app.characters.export_import import character_to_card, card_to_character_data
from app.llm.base import LLMMessage, LLMConfig
from app.llm.registry import get_provider

router = APIRouter(prefix="/api/characters", tags=["characters"])

GENERATE_SYSTEM_PROMPT = """Ты — эксперт по созданию персонажей для ролевых чатов с литературным стилем повествования.
Проанализируй предоставленный текст и создай профиль персонажа в формате JSON.

Верни строго JSON-объект со следующими полями:
{
  "name": "Имя персонажа",
  "tagline": "Краткое описание в 5-10 слов",
  "personality": "Детальное описание характера от второго лица: 'Ты — ...' Включи: темперамент, манеру речи (формальная/неформальная, особенности, любимые выражения), привычки, мотивацию, сильные и слабые стороны, отношение к другим людям. Минимум 5-7 предложений.",
  "appearance": "Детальное описание внешности: рост, телосложение, черты лица, цвет глаз и волос, стиль одежды, особые приметы, характерные жесты и позы.",
  "scenario": "Описание мира и начальной ситуации для диалога. Где происходит действие, какой контекст, что привело к встрече с пользователем.",
  "greeting_message": "Первое сообщение персонажа. Литературный формат: нарратив от третьего лица обычным текстом, прямая речь через '—', внутренние мысли в *звёздочках*. 2-3 абзаца, разделённые пустой строкой.",
  "example_dialogues": "2-3 примера реплик в формате:\\n{{user}}: ...\\n{{char}}: ...",
  "tags": ["тег1", "тег2", "тег3"],
  "structured_tags": ["tag_id1", "tag_id2"],
  "content_rating": "sfw",
  "response_length": "long"
}

## Формат greeting_message

Используй литературный стиль — как художественная проза:
- Нарратив (действия, описания) — обычный текст от ТРЕТЬЕГО лица (она/он/имя)
- Прямая речь — через длинное тире «—»
- Внутренние мысли — в *звёздочках*
- Каждый элемент — отдельный абзац через пустую строку
- НЕ используй *звёздочки* для действий — только для мыслей

Пример greeting_message:
"Она стояла у окна, задумчиво постукивая пальцами по подоконнику. Тусклый свет фонаря выхватывал из темноты её силуэт.\\n\\n— Ты пришёл, — произнесла негромко, не оборачиваясь. — Я ждала.\\n\\n*Наконец-то. Уже начала сомневаться, что он вообще появится.*"

## Формат example_dialogues

Используй {{char}} и {{user}} как плейсхолдеры — они будут заменены на реальные имена:
{{user}}: Привет!
{{char}}: *прикусывает губу, отводя взгляд* — Здравствуй. Давно не виделись.

## structured_tags

Выбери подходящие ID из списка (только те, что точно подходят, 2-5 штук):
Пол: male, female, non_binary, androgynous
Роль: mentor, villain, love_interest, companion, rival, mysterious_stranger
Характер: tsundere, yandere, kuudere, sarcastic, shy, cheerful, cold, flirty, wise, aggressive
Сеттинг: fantasy, sci_fi, modern, historical, post_apocalyptic, school, horror
Стиль: verbose, concise, emotional, stoic, poetic, humorous

## response_length

Выбери одно из: "short", "medium", "long", "very_long" — исходя из персонажа:
- short — лаконичные персонажи, боевые сцены
- medium — обычные диалоговые персонажи
- long — персонажи с богатым внутренним миром (по умолчанию)
- very_long — литературные, поэтичные, многословные персонажи

## Правила

- personality: подробный, от второго лица ("Ты — ..."), минимум 5-7 предложений
- appearance: отдельно от personality, конкретные физические детали
- greeting_message: литературный формат с тремя элементами (нарратив + речь + мысли)
- content_rating: "sfw" для обычного контента, "moderate" если есть насилие/мрачные темы, "nsfw" если явный взрослый контент
- Если указано имя конкретного персонажа — создай профиль для него. Иначе — выбери самого яркого/интересного из текста.
- Верни ТОЛЬКО JSON, без markdown-обёртки, без пояснений."""


@router.post("/generate-from-story")
async def generate_from_story(
    body: GenerateFromStoryRequest,
    user=Depends(get_current_user),
):
    is_admin = getattr(user, "role", None) == "admin"

    # Admin: direct provider selection; Regular users: auto with fallback
    PROVIDER_MODELS = {
        "claude": "claude-sonnet-4-5-20250929",
        "openai": "gpt-4o",
        "gemini": "gemini-2.0-flash",
        "deepseek": "deepseek-chat",
        "qwen": "qwen3-32b",
    }

    # Build provider chain: list of (provider_name, model_id) to try
    if is_admin and body.preferred_model and body.preferred_model != "auto":
        # Admin picked a specific provider
        if "/" in body.preferred_model:
            provider_chain = [("openrouter", body.preferred_model)]
        elif body.preferred_model in ("openrouter",):
            provider_chain = [("openrouter", "")]
        elif body.preferred_model in ("groq",):
            provider_chain = [("groq", "")]
        else:
            pm = body.preferred_model
            provider_chain = [(pm, PROVIDER_MODELS.get(pm, ""))]
        # Admin always gets groq fallback if not already groq
        if provider_chain[0][0] != "groq":
            provider_chain.append(("groq", ""))
        if provider_chain[0][0] != "openrouter":
            provider_chain.append(("openrouter", ""))
    else:
        # Regular users: openrouter auto → groq fallback
        provider_chain = [("openrouter", ""), ("groq", "")]

    rating_instructions = {
        "sfw": "Контент должен быть полностью безопасным (SFW). Никакого насилия, откровенного контента или мрачных тем.",
        "moderate": "Допускается умеренный контент: лёгкое насилие, мрачные темы, конфликты. Без откровенного взрослого контента.",
        "nsfw": "Допускается взрослый контент (NSFW): откровенные сцены, насилие, тёмные темы.",
    }
    user_msg = body.story_text
    if body.character_name:
        user_msg += f"\n\nСоздай профиль для персонажа: {body.character_name}"
    user_msg += f"\n\nРейтинг контента: {body.content_rating}. {rating_instructions.get(body.content_rating, '')}"
    if body.extra_instructions:
        user_msg += f"\n\nДополнительные пожелания: {body.extra_instructions}"

    messages = [
        LLMMessage(role="system", content=GENERATE_SYSTEM_PROMPT),
        LLMMessage(role="user", content=user_msg),
    ]

    # Try each provider in chain
    last_error = None
    for prov_name, model_id in provider_chain:
        try:
            provider = get_provider(prov_name)
        except ValueError:
            continue
        config = LLMConfig(model=model_id, temperature=0.7, max_tokens=2048)
        try:
            raw = await provider.generate(messages, config)
            break  # success
        except Exception as e:
            last_error = e
            logging.getLogger(__name__).warning(
                "LLM generation failed (%s): %s", prov_name, str(e)[:200]
            )
    else:
        logging.getLogger(__name__).error("All providers failed for character generation")
        raise HTTPException(status_code=502, detail="Character generation failed. Please try again.")

    # Strip markdown code fences if present
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Failed to parse LLM response as JSON")

    # Normalize: LLM sometimes returns arrays instead of strings
    for field in ("name", "tagline", "personality", "appearance", "scenario",
                  "greeting_message", "example_dialogues"):
        if isinstance(data.get(field), list):
            data[field] = "\n".join(str(x) for x in data[field])

    # Ensure tags is a list of strings
    if "tags" in data and not isinstance(data["tags"], list):
        data["tags"] = []

    # Ensure structured_tags is a list of valid IDs
    from app.characters.structured_tags import _BY_ID
    if isinstance(data.get("structured_tags"), list):
        data["structured_tags"] = [t for t in data["structured_tags"] if t in _BY_ID]
    else:
        data["structured_tags"] = []

    # Normalize response_length
    valid_lengths = {"short", "medium", "long", "very_long"}
    if data.get("response_length") not in valid_lengths:
        data["response_length"] = "long"

    return data


@router.get("")
async def browse_characters(
    limit: int = Query(15, le=50),
    offset: int = Query(0, ge=0),
    search: str | None = None,
    tag: str | None = None,
    gender: str | None = None,
    language: str | None = None,
    user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    user_id = user["id"] if user else None
    is_admin = user.get("role") == "admin" if user else False
    characters = await service.list_public_characters(db, limit, offset, search, tag, gender=gender, user_id=user_id, language=language)
    total = await service.count_public_characters(db, search, tag, gender=gender, user_id=user_id)
    if language:
        from app.characters.translation import ensure_translations
        await ensure_translations(characters, language)
    return {"items": [character_to_dict(c, language=language, is_admin=is_admin) for c in characters], "total": total}


@router.get("/my")
async def my_characters(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    is_admin = user.get("role") == "admin"
    characters = await service.list_my_characters(db, user["id"])
    return [character_to_dict(c, is_admin=is_admin) for c in characters]


@router.get("/structured-tags")
async def list_structured_tags():
    from app.characters.structured_tags import CATEGORIES, get_tags_by_category
    return {"categories": CATEGORIES, "tags": get_tags_by_category()}


@router.post("/import")
async def import_character(
    request: Request,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        card = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    char_data = card_to_character_data(card)

    content_rating_enum = ContentRating(char_data.pop("content_rating", "sfw"))

    character = Character(
        creator_id=user["id"],
        content_rating=content_rating_enum,
        **char_data,
    )
    db.add(character)
    await db.flush()
    from app.characters.slugify import generate_slug
    character.slug = generate_slug(character.name, character.id)
    await db.commit()

    return {"id": character.id, "name": character.name, "slug": character.slug}


@router.get("/by-slug/{slug}")
async def get_character_by_slug(
    slug: str,
    language: str | None = None,
    user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    character = await service.get_character_by_slug(db, slug)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    if not character.is_public:
        user_id = user["id"] if user else None
        user_role = user.get("role") if user else None
        if character.creator_id != user_id and user_role != "admin":
            raise HTTPException(status_code=404, detail="Character not found")
    if language:
        from app.characters.translation import ensure_translations
        await ensure_translations([character], language, include_descriptions=True)
    is_admin = user.get("role") == "admin" if user else False
    return character_to_dict(character, language=language, is_admin=is_admin)


@router.get("/{character_id}/similar")
async def get_similar(
    character_id: str,
    language: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    characters = await service.get_similar_characters(db, character_id)
    if language:
        from app.characters.translation import ensure_translations
        await ensure_translations(characters, language, cached_only=True)
    return [character_to_dict(c, language=language) for c in characters]


@router.get("/{character_id}/export")
async def export_character(
    character_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Character).where(Character.id == character_id, Character.is_public == True))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    card = character_to_card(character)
    # Sanitize filename: remove quotes and non-ASCII, fallback to "character"
    safe_name = re.sub(r'[^\w\s\-.]', '', character.name.replace('"', '')).strip() or "character"
    return JSONResponse(
        content=card,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}.json"',
        },
    )


class VoteRequest(BaseModel):
    value: int = Field(..., ge=-1, le=1)  # +1, -1, or 0 (remove)


@router.post("/{character_id}/vote")
async def vote_character(
    character_id: str,
    body: VoteRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Vote on a character. value: 1 (upvote), -1 (downvote), 0 (remove vote)."""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # Find existing vote
    vote_result = await db.execute(
        select(Vote).where(Vote.user_id == user["id"], Vote.character_id == character_id)
    )
    existing = vote_result.scalar_one_or_none()

    old_value = existing.value if existing else 0
    new_value = body.value

    if new_value == 0:
        # Remove vote
        if existing:
            await db.delete(existing)
    elif existing:
        existing.value = new_value
    else:
        db.add(Vote(user_id=user["id"], character_id=character_id, value=new_value))

    # Update character vote_score by delta
    delta = new_value - old_value
    character.vote_score = (character.vote_score or 0) + delta

    await db.commit()
    return {"vote_score": character.vote_score, "user_vote": new_value}


@router.post("/{character_id}/fork")
async def fork_character(
    character_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fork a public character into a private draft."""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Character).where(Character.id == character_id).options(selectinload(Character.creator))
    )
    original = result.scalar_one_or_none()
    if not original or not original.is_public:
        raise HTTPException(status_code=404, detail="Character not found")

    from app.characters.slugify import generate_slug
    import uuid

    new_id = str(uuid.uuid4())
    fork_name = f"{original.name} (fork)"

    forked = Character(
        id=new_id,
        creator_id=user["id"],
        name=fork_name,
        tagline=original.tagline,
        avatar_url=original.avatar_url,
        personality=original.personality,
        appearance=original.appearance,
        scenario=original.scenario,
        greeting_message=original.greeting_message,
        example_dialogues=original.example_dialogues,
        content_rating=original.content_rating,
        system_prompt_suffix=original.system_prompt_suffix,
        tags=original.tags,
        structured_tags=original.structured_tags,
        preferred_model=original.preferred_model,
        max_tokens=original.max_tokens,
        response_length=original.response_length,
        is_public=False,
        forked_from_id=character_id,
        slug=generate_slug(fork_name, new_id),
    )
    db.add(forked)

    # Increment fork_count on original
    original.fork_count = (original.fork_count or 0) + 1

    await db.commit()
    return {"id": forked.id, "slug": forked.slug, "name": forked.name}


@router.get("/{character_id}/relations")
async def get_character_relations(
    character_id: str,
    language: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get character relationships with related character data."""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(CharacterRelation).where(CharacterRelation.character_id == character_id)
    )
    relations = result.scalars().all()
    if not relations:
        return []

    # Load related characters
    related_ids = [r.related_id for r in relations]
    chars_result = await db.execute(
        select(Character)
        .where(Character.id.in_(related_ids))
        .options(selectinload(Character.creator))
    )
    chars_by_id = {c.id: c for c in chars_result.scalars().all()}

    if language:
        from app.characters.translation import ensure_translations
        await ensure_translations(list(chars_by_id.values()), language, cached_only=True)

    items = []
    for rel in relations:
        char = chars_by_id.get(rel.related_id)
        if not char or not char.is_public:
            continue
        label = getattr(rel, f"label_{language}", None) or rel.label_en or rel.relation_type
        items.append({
            "relation_type": rel.relation_type,
            "label": label,
            "character": character_to_dict(char, language=language),
        })
    return items


@router.get("/{character_id}")
async def get_character(
    character_id: str,
    language: str | None = None,
    user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    character = await service.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    # Private characters only visible to owner and admins
    if not character.is_public:
        user_id = user["id"] if user else None
        user_role = user.get("role") if user else None
        if character.creator_id != user_id and user_role != "admin":
            raise HTTPException(status_code=404, detail="Character not found")
    # Translate card + description fields
    if language:
        from app.characters.translation import ensure_translations
        await ensure_translations([character], language, include_descriptions=True)
    is_admin = user.get("role") == "admin" if user else False
    return character_to_dict(character, language=language, is_admin=is_admin)


@router.get("/check-slug")
async def check_slug(
    slug: str = Query(min_length=1, max_length=50),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.characters.slugify import validate_slug
    try:
        normalized = validate_slug(slug)
    except ValueError as e:
        return {"available": False, "slug": slug, "error": str(e)}
    available = await service.check_slug_available(db, user["id"], normalized)
    return {"available": available, "slug": normalized}


@router.post("", status_code=201)
async def create_character(
    body: CharacterCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    is_admin = user.get("role") == "admin"
    try:
        character = await service.create_character(db, user["id"], body.model_dump())
    except ValueError as e:
        msg = str(e)
        if msg == "slug_taken":
            raise HTTPException(status_code=409, detail="This slug is already taken")
        if msg == "slug_too_short":
            raise HTTPException(status_code=400, detail="Slug must be at least 3 characters")
        raise HTTPException(status_code=400, detail=msg)
    return character_to_dict(character, is_admin=is_admin)


@router.put("/{character_id}")
async def update_character(
    character_id: str,
    body: CharacterUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    is_admin = user.get("role") == "admin"
    try:
        result = await service.update_character(
            db, character_id, user["id"], body.model_dump(), is_admin=is_admin
        )
    except ValueError as e:
        msg = str(e)
        if msg == "slug_taken":
            raise HTTPException(status_code=409, detail="This slug is already taken")
        raise HTTPException(status_code=400, detail=msg)
    if not result:
        raise HTTPException(status_code=404, detail="Character not found or not yours")
    return character_to_dict(result, is_admin=is_admin)


@router.delete("/{character_id}", status_code=204)
async def delete_character(
    character_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    is_admin = user.get("role") == "admin"
    deleted = await service.delete_character(db, character_id, user["id"], is_admin=is_admin)
    if not deleted:
        raise HTTPException(status_code=404, detail="Character not found or not yours")
