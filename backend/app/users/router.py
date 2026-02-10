from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.middleware import get_current_user
from app.db.session import get_db
from app.db.models import User, Favorite, Character

router = APIRouter(prefix="/api/users", tags=["users"])


class ProfileUpdate(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    language: str | None = None


@router.get("/me")
async def get_profile(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user["id"]))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404)
    return {
        "id": u.id,
        "email": u.email,
        "username": u.username,
        "display_name": u.display_name,
        "avatar_url": u.avatar_url,
        "bio": u.bio,
        "language": u.language or "ru",
    }


@router.put("/me")
async def update_profile(
    body: ProfileUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user["id"]))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404)

    for key, value in body.model_dump().items():
        if value is not None:
            setattr(u, key, value)
    await db.commit()
    await db.refresh(u)
    return {
        "id": u.id,
        "email": u.email,
        "username": u.username,
        "display_name": u.display_name,
        "avatar_url": u.avatar_url,
        "bio": u.bio,
        "language": u.language or "ru",
    }


@router.get("/me/favorites")
async def get_favorites(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Favorite, Character)
        .join(Character, Favorite.character_id == Character.id)
        .where(Favorite.user_id == user["id"])
    )
    rows = result.all()
    return [
        {
            "character_id": fav.character_id,
            "character": {
                "id": char.id,
                "name": char.name,
                "tagline": char.tagline,
                "avatar_url": char.avatar_url,
            },
        }
        for fav, char in rows
    ]


@router.post("/me/favorites/{character_id}", status_code=201)
async def add_favorite(
    character_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fav = Favorite(user_id=user["id"], character_id=character_id)
    db.add(fav)

    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if character:
        character.like_count = (character.like_count or 0) + 1

    await db.commit()
    return {"status": "ok"}


@router.delete("/me/favorites/{character_id}", status_code=204)
async def remove_favorite(
    character_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user["id"],
            Favorite.character_id == character_id,
        )
    )
    fav = result.scalar_one_or_none()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")
    await db.delete(fav)
    await db.commit()
