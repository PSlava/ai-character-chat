from datetime import datetime
from sqlalchemy import select, func, text, case
from app.utils.sanitize import strip_html_tags

_TEXT_FIELDS_TO_SANITIZE = {"name", "tagline", "personality", "appearance", "speech_pattern",
                            "scenario", "greeting_message", "example_dialogues", "system_prompt_suffix"}

_CHARACTER_ALLOWED_FIELDS = {
    "name", "tagline", "avatar_url", "personality", "appearance",
    "speech_pattern", "scenario", "greeting_message", "example_dialogues",
    "content_rating", "system_prompt_suffix", "is_public", "preferred_model",
    "max_tokens", "response_length",
}
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models import Character, User, ContentRating
from app.config import settings


async def list_public_characters(
    db: AsyncSession,
    limit: int = 20,
    offset: int = 0,
    search: str | None = None,
    tag: str | None = None,
    gender: str | None = None,
    user_id: str | None = None,
    language: str | None = None,
):
    from sqlalchemy import or_

    # Show public characters + user's own private ones
    if user_id:
        visibility = or_(Character.is_public == True, Character.creator_id == user_id)
    else:
        visibility = Character.is_public == True

    if language and language.isalpha() and len(language) <= 10:
        # Sort by displayed chat count (real + base) for consistency with UI
        order = text(
            f"(COALESCE(characters.chat_count, 0) + COALESCE((characters.base_chat_count->>'{language}')::int, 0)) DESC"
        ), Character.created_at.desc()
    else:
        order = (Character.created_at.desc(),)

    query = (
        select(Character)
        .options(selectinload(Character.creator))
        .where(visibility)
        .order_by(*order)
        .offset(offset)
        .limit(limit)
    )
    if search:
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.where(
            or_(
                Character.name.ilike(f"%{escaped}%"),
                Character.tagline.ilike(f"%{escaped}%"),
                Character.tags.ilike(f"%{escaped}%"),
            )
        )
    if tag:
        query = query.where(Character.tags.contains(tag))
    if gender and gender in ("male", "female"):
        # Exact tag match within comma-separated list (avoid "male" matching "female")
        query = query.where(text(f"(',' || structured_tags || ',') LIKE '%,{gender},%'"))
    if not settings.is_nsfw_mode:
        query = query.where(Character.content_rating == ContentRating.sfw)

    result = await db.execute(query)
    characters = result.scalars().all()

    # Apply cached translations only — never block on LLM calls during browse.
    # Uncached characters get a background translation task.
    if language:
        from app.characters.translation import ensure_translations
        await ensure_translations(characters, language, cached_only=True)

    return characters


async def count_public_characters(
    db: AsyncSession,
    search: str | None = None,
    tag: str | None = None,
    gender: str | None = None,
    user_id: str | None = None,
) -> int:
    from sqlalchemy import or_

    if user_id:
        visibility = or_(Character.is_public == True, Character.creator_id == user_id)
    else:
        visibility = Character.is_public == True

    query = select(func.count()).select_from(Character).where(visibility)
    if search:
        from sqlalchemy import or_
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.where(
            or_(
                Character.name.ilike(f"%{escaped}%"),
                Character.tagline.ilike(f"%{escaped}%"),
                Character.tags.ilike(f"%{escaped}%"),
            )
        )
    if tag:
        query = query.where(Character.tags.contains(tag))
    if gender and gender in ("male", "female"):
        # Exact tag match within comma-separated list (avoid "male" matching "female")
        query = query.where(text(f"(',' || structured_tags || ',') LIKE '%,{gender},%'"))
    if not settings.is_nsfw_mode:
        query = query.where(Character.content_rating == ContentRating.sfw)

    result = await db.execute(query)
    return result.scalar_one()


async def suggest_characters(
    db: AsyncSession,
    query_str: str,
    language: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Lightweight character suggestions for autocomplete. Returns minimal fields."""
    from sqlalchemy import or_

    escaped = query_str.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    q = (
        select(Character.id, Character.name, Character.slug, Character.avatar_url, Character.tagline, Character.translations)
        .where(
            Character.is_public == True,
            or_(
                Character.name.ilike(f"%{escaped}%"),
                Character.tagline.ilike(f"%{escaped}%"),
                Character.tags.ilike(f"%{escaped}%"),
            ),
        )
        .order_by(Character.chat_count.desc())
        .limit(limit)
    )
    result = await db.execute(q)
    rows = result.all()

    suggestions = []
    for row in rows:
        name = row.name
        tagline = row.tagline or ""
        # Use cached translations if available
        if language and row.translations:
            tr = row.translations.get(language, {})
            if "name" in tr:
                name = tr["name"]
            if "tagline" in tr:
                tagline = tr["tagline"]
        suggestions.append({
            "id": row.id,
            "name": name,
            "slug": row.slug,
            "avatar_url": row.avatar_url,
            "tagline": tagline,
        })
    return suggestions


async def get_character(db: AsyncSession, character_id: str):
    result = await db.execute(
        select(Character)
        .options(selectinload(Character.creator))
        .where(Character.id == character_id)
    )
    return result.scalar_one_or_none()


async def get_character_by_slug(db: AsyncSession, slug: str):
    result = await db.execute(
        select(Character)
        .options(selectinload(Character.creator))
        .where(Character.slug == slug)
        .order_by(Character.chat_count.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_character(db: AsyncSession, creator_id: str, data: dict):
    from app.characters.slugify import generate_slug
    data.pop("slug", None)  # ignore any slug from input
    # Sanitize text fields
    for field in _TEXT_FIELDS_TO_SANITIZE:
        if field in data and isinstance(data[field], str):
            data[field] = strip_html_tags(data[field])
    # Convert tags list to comma-separated string
    tags = data.pop("tags", [])
    structured_tags = data.pop("structured_tags", [])
    character = Character(
        **data,
        creator_id=creator_id,
        tags=",".join(tags) if isinstance(tags, list) else tags,
        structured_tags=",".join(structured_tags) if isinstance(structured_tags, list) else structured_tags,
    )
    db.add(character)
    await db.flush()  # get character.id
    character.slug = generate_slug(data.get("name", "character"), character.id)
    await db.commit()
    # Re-fetch with creator loaded
    return await get_character(db, character.id)


async def update_character(db: AsyncSession, character_id: str, creator_id: str, data: dict, is_admin: bool = False):
    if is_admin:
        result = await db.execute(select(Character).where(Character.id == character_id))
    else:
        result = await db.execute(
            select(Character).where(
                Character.id == character_id, Character.creator_id == creator_id
            )
        )
    character = result.scalar_one_or_none()
    if not character:
        return None

    # Delete old avatar file if being replaced
    new_avatar = data.get("avatar_url")
    if new_avatar and character.avatar_url and new_avatar != character.avatar_url:
        if character.avatar_url.startswith("/api/uploads/avatars/"):
            from pathlib import Path
            from app.config import settings
            old_file = Path(settings.upload_dir) / "avatars" / character.avatar_url.split("/")[-1]
            if old_file.exists():
                old_file.unlink(missing_ok=True)

    data.pop("slug", None)  # ignore any slug from input

    # Sanitize text fields
    for field in _TEXT_FIELDS_TO_SANITIZE:
        if field in data and isinstance(data[field], str):
            data[field] = strip_html_tags(data[field])
    tags = data.pop("tags", None)
    structured_tags = data.pop("structured_tags", None)
    for key, value in data.items():
        if value is not None and key in _CHARACTER_ALLOWED_FIELDS:
            setattr(character, key, value)
    if tags is not None:
        character.tags = ",".join(tags) if isinstance(tags, list) else tags
    if structured_tags is not None:
        character.structured_tags = ",".join(structured_tags) if isinstance(structured_tags, list) else structured_tags

    # Regenerate slug when name changes
    if "name" in data and data["name"] is not None and data["name"] != character.name:
        from app.characters.slugify import generate_slug
        character.slug = generate_slug(data["name"], character.id)

    # Clear translation cache if translatable fields changed
    _translatable = ("name", "tagline", "personality", "scenario", "appearance", "greeting_message")
    if any(key in data and data[key] is not None for key in _translatable) or tags is not None:
        character.translations = {}

    character.updated_at = datetime.utcnow()

    await db.commit()
    return await get_character(db, character.id)


async def delete_character(db: AsyncSession, character_id: str, creator_id: str, is_admin: bool = False):
    if is_admin:
        result = await db.execute(select(Character).where(Character.id == character_id))
    else:
        result = await db.execute(
            select(Character).where(
                Character.id == character_id, Character.creator_id == creator_id
            )
        )
    character = result.scalar_one_or_none()
    if not character:
        return False

    # Delete avatar file from disk
    if character.avatar_url and character.avatar_url.startswith("/api/uploads/avatars/"):
        from pathlib import Path
        from app.config import settings
        filename = character.avatar_url.split("/")[-1]
        avatar_path = Path(settings.upload_dir) / "avatars" / filename
        if avatar_path.exists():
            avatar_path.unlink(missing_ok=True)

    await db.delete(character)
    await db.commit()
    return True


async def get_similar_characters(db: AsyncSession, character_id: str, limit: int = 8) -> list:
    """Find similar characters by matching tags, structured_tags, and content_rating."""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        return []

    tags = [t.strip() for t in (character.tags or "").split(",") if t.strip()]
    struct_tags = [t.strip() for t in (character.structured_tags or "").split(",") if t.strip()]
    src_rating = getattr(character.content_rating, 'value', character.content_rating) or "sfw"

    if not tags and not struct_tags:
        return []

    # Weighted score: free-form tags +2, structured tags +3, same content_rating +2, same creator -5
    score_parts = []
    for tag in tags:
        score_parts.append(case((Character.tags.contains(tag), 2), else_=0))
    for stag in struct_tags:
        score_parts.append(
            case(
                (text(f"(',' || COALESCE(structured_tags, '') || ',') LIKE '%,{stag},%'"), 3),
                else_=0,
            )
        )
    # Bonus for same content rating
    score_parts.append(
        case(
            (text(f"COALESCE(content_rating, 'sfw') = '{src_rating}'"), 2),
            else_=0,
        )
    )
    # Penalty for same creator (avoid flooding with same-author chars)
    score_parts.append(
        case((Character.creator_id == character.creator_id, -5), else_=0)
    )

    score = sum(score_parts)

    query = (
        select(Character)
        .options(selectinload(Character.creator))
        .where(
            Character.is_public == True,
            Character.id != character_id,
            score > 0,
        )
        .order_by(score.desc(), Character.chat_count.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    return result.scalars().all()


async def list_my_characters(db: AsyncSession, creator_id: str):
    result = await db.execute(
        select(Character)
        .options(selectinload(Character.creator))
        .where(Character.creator_id == creator_id)
        .order_by(Character.created_at.desc())
    )
    return result.scalars().all()
