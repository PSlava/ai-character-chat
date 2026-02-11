import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.middleware import get_current_user
from app.db.session import get_db
from app.db.models import User, Favorite, Character
from app.utils.sanitize import strip_html_tags

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")

router = APIRouter(prefix="/api/users", tags=["users"])


_PROFILE_ALLOWED_FIELDS = {"display_name", "username", "bio", "avatar_url", "language"}


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=50)
    username: str | None = Field(default=None, max_length=20)
    bio: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = Field(default=None, max_length=2000)
    language: str | None = Field(default=None, max_length=10)


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
        "role": u.role or "user",
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

    data = body.model_dump()
    # Validate and check username uniqueness
    if data.get("username") is not None:
        username = data["username"]
        if not USERNAME_RE.match(username):
            raise HTTPException(status_code=400, detail="Username must be 3-20 characters: letters, digits, underscore")
        existing = await db.execute(select(User).where(User.username == username, User.id != u.id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already taken")

    for key, value in data.items():
        if value is not None and key in _PROFILE_ALLOWED_FIELDS:
            if key in ("display_name", "bio") and isinstance(value, str):
                value = strip_html_tags(value)
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
        "role": u.role or "user",
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

    # Decrement like_count
    char_result = await db.execute(select(Character).where(Character.id == character_id))
    character = char_result.scalar_one_or_none()
    if character and (character.like_count or 0) > 0:
        character.like_count = character.like_count - 1

    await db.delete(fav)
    await db.commit()
