"""CRUD for character lorebook entries (World Info)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_user
from app.db.session import get_db
from app.db.models import Character, LoreEntry
from app.utils.sanitize import strip_html_tags

router = APIRouter(prefix="/api/characters", tags=["lore"])

MAX_LORE_ENTRIES = 50


class LoreEntryCreate(BaseModel):
    keywords: str = Field(max_length=500)
    content: str = Field(max_length=5000)
    enabled: bool = True
    position: int = 0


class LoreEntryUpdate(BaseModel):
    keywords: str | None = Field(default=None, max_length=500)
    content: str | None = Field(default=None, max_length=5000)
    enabled: bool | None = None
    position: int | None = None


def _serialize(e: LoreEntry) -> dict:
    return {
        "id": e.id,
        "character_id": e.character_id,
        "keywords": e.keywords,
        "content": e.content,
        "enabled": e.enabled,
        "position": e.position,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


async def _check_owner(db: AsyncSession, character_id: str, user: dict) -> Character:
    """Verify character exists and user is owner or admin."""
    result = await db.execute(select(Character).where(Character.id == character_id))
    char = result.scalar_one_or_none()
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    if char.creator_id != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return char


@router.get("/{character_id}/lore")
async def list_lore_entries(
    character_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_owner(db, character_id, user)
    result = await db.execute(
        select(LoreEntry)
        .where(LoreEntry.character_id == character_id)
        .order_by(LoreEntry.position, LoreEntry.created_at)
    )
    return [_serialize(e) for e in result.scalars().all()]


@router.post("/{character_id}/lore", status_code=201)
async def create_lore_entry(
    character_id: str,
    body: LoreEntryCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_owner(db, character_id, user)

    count = await db.execute(
        select(func.count()).select_from(LoreEntry).where(LoreEntry.character_id == character_id)
    )
    if (count.scalar() or 0) >= MAX_LORE_ENTRIES:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_LORE_ENTRIES} lore entries allowed")

    entry = LoreEntry(
        character_id=character_id,
        keywords=strip_html_tags(body.keywords),
        content=strip_html_tags(body.content),
        enabled=body.enabled,
        position=body.position,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return _serialize(entry)


@router.put("/{character_id}/lore/{entry_id}")
async def update_lore_entry(
    character_id: str,
    entry_id: str,
    body: LoreEntryUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_owner(db, character_id, user)

    result = await db.execute(
        select(LoreEntry).where(LoreEntry.id == entry_id, LoreEntry.character_id == character_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Lore entry not found")

    if body.keywords is not None:
        entry.keywords = strip_html_tags(body.keywords)
    if body.content is not None:
        entry.content = strip_html_tags(body.content)
    if body.enabled is not None:
        entry.enabled = body.enabled
    if body.position is not None:
        entry.position = body.position

    await db.commit()
    await db.refresh(entry)
    return _serialize(entry)


@router.delete("/{character_id}/lore/{entry_id}", status_code=204)
async def delete_lore_entry(
    character_id: str,
    entry_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_owner(db, character_id, user)

    result = await db.execute(
        select(LoreEntry).where(LoreEntry.id == entry_id, LoreEntry.character_id == character_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Lore entry not found")

    await db.delete(entry)
    await db.commit()
