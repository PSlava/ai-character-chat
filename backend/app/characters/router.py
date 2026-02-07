from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.middleware import get_current_user
from app.db.session import get_db
from app.characters.schemas import CharacterCreate, CharacterUpdate
from app.characters import service
from app.characters.serializers import character_to_dict

router = APIRouter(prefix="/api/characters", tags=["characters"])


@router.get("")
async def browse_characters(
    limit: int = Query(20, le=50),
    offset: int = Query(0, ge=0),
    search: str | None = None,
    tag: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    characters = await service.list_public_characters(db, limit, offset, search, tag)
    return [character_to_dict(c) for c in characters]


@router.get("/my")
async def my_characters(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    characters = await service.list_my_characters(db, user["id"])
    return [character_to_dict(c) for c in characters]


@router.get("/{character_id}")
async def get_character(character_id: str, db: AsyncSession = Depends(get_db)):
    character = await service.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character_to_dict(character)


@router.post("", status_code=201)
async def create_character(
    body: CharacterCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    character = await service.create_character(db, user["id"], body.model_dump())
    return character_to_dict(character)


@router.put("/{character_id}")
async def update_character(
    character_id: str,
    body: CharacterUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await service.update_character(
        db, character_id, user["id"], body.model_dump()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Character not found or not yours")
    return character_to_dict(result)


@router.delete("/{character_id}", status_code=204)
async def delete_character(
    character_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await service.delete_character(db, character_id, user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Character not found or not yours")
