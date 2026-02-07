from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models import Character, User


async def list_public_characters(
    db: AsyncSession,
    limit: int = 20,
    offset: int = 0,
    search: str | None = None,
    tag: str | None = None,
):
    query = (
        select(Character)
        .options(selectinload(Character.creator))
        .where(Character.is_public == True)
        .order_by(Character.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if search:
        query = query.where(Character.name.ilike(f"%{search}%"))
    if tag:
        query = query.where(Character.tags.contains(tag))

    result = await db.execute(query)
    return result.scalars().all()


async def get_character(db: AsyncSession, character_id: str):
    result = await db.execute(
        select(Character)
        .options(selectinload(Character.creator))
        .where(Character.id == character_id)
    )
    return result.scalar_one_or_none()


async def create_character(db: AsyncSession, creator_id: str, data: dict):
    # Convert tags list to comma-separated string
    tags = data.pop("tags", [])
    character = Character(
        **data,
        creator_id=creator_id,
        tags=",".join(tags) if isinstance(tags, list) else tags,
    )
    db.add(character)
    await db.commit()
    # Re-fetch with creator loaded
    return await get_character(db, character.id)


async def update_character(db: AsyncSession, character_id: str, creator_id: str, data: dict):
    result = await db.execute(
        select(Character).where(
            Character.id == character_id, Character.creator_id == creator_id
        )
    )
    character = result.scalar_one_or_none()
    if not character:
        return None

    tags = data.pop("tags", None)
    for key, value in data.items():
        if value is not None:
            setattr(character, key, value)
    if tags is not None:
        character.tags = ",".join(tags) if isinstance(tags, list) else tags
    character.updated_at = datetime.utcnow()

    await db.commit()
    return await get_character(db, character.id)


async def delete_character(db: AsyncSession, character_id: str, creator_id: str):
    result = await db.execute(
        select(Character).where(
            Character.id == character_id, Character.creator_id == creator_id
        )
    )
    character = result.scalar_one_or_none()
    if not character:
        return False
    await db.delete(character)
    await db.commit()
    return True


async def list_my_characters(db: AsyncSession, creator_id: str):
    result = await db.execute(
        select(Character)
        .where(Character.creator_id == creator_id)
        .order_by(Character.created_at.desc())
    )
    return result.scalars().all()
