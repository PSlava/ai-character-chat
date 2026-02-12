from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_user
from app.db.session import get_db
from app.db.models import Character, PromptTemplate, User
from app.chat.prompt_builder import get_all_keys, load_overrides, invalidate_cache
from app.db.session import engine
from app.admin.seed_data import SEED_CHARACTERS, SWEETSIN_EMAIL, SWEETSIN_USERNAME

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def require_admin(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Verify admin role from DB, not just JWT claims."""
    result = await db.execute(select(User).where(User.id == user["id"]))
    db_user = result.scalar_one_or_none()
    if not db_user or (db_user.role or "user") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


class PromptUpdateBody(BaseModel):
    value: str


@router.get("/prompts")
async def list_prompts(
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Return all prompt keys with defaults and overrides."""
    await load_overrides(engine)
    keys = get_all_keys()
    # Enrich with updated_at from DB
    result = await db.execute(select(PromptTemplate))
    db_rows = {row.key: row for row in result.scalars().all()}
    for item in keys:
        db_row = db_rows.get(item["key"])
        item["updated_at"] = db_row.updated_at.isoformat() if db_row else None
    return keys


@router.put("/prompts/{key:path}")
async def update_prompt(
    key: str,
    body: PromptUpdateBody,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create or update a prompt override."""
    existing = await db.execute(select(PromptTemplate).where(PromptTemplate.key == key))
    row = existing.scalar_one_or_none()
    if row:
        row.value = body.value
        row.updated_at = datetime.utcnow()
    else:
        row = PromptTemplate(key=key, value=body.value)
        db.add(row)
    await db.commit()
    invalidate_cache()
    return {"key": key, "status": "saved"}


@router.delete("/prompts/{key:path}")
async def reset_prompt(
    key: str,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete override, resetting to default."""
    await db.execute(delete(PromptTemplate).where(PromptTemplate.key == key))
    await db.commit()
    invalidate_cache()
    return {"key": key, "status": "reset"}


# ── Seed characters ──────────────────────────────────────────────


async def _get_or_create_sweetsin(db: AsyncSession) -> User:
    """Get or create the internal @sweetsin user."""
    result = await db.execute(select(User).where(User.email == SWEETSIN_EMAIL))
    user = result.scalar_one_or_none()
    if user:
        return user

    import secrets
    import bcrypt as _bcrypt

    random_password = secrets.token_hex(32).encode()
    user = User(
        email=SWEETSIN_EMAIL,
        username=SWEETSIN_USERNAME,
        display_name="SweetSin",
        password_hash=_bcrypt.hashpw(random_password, _bcrypt.gensalt()).decode(),
        role="user",
    )
    db.add(user)
    await db.flush()
    return user


@router.post("/seed-characters")
async def import_seed_characters(
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Import 40 seed characters under @sweetsin user."""
    sweetsin = await _get_or_create_sweetsin(db)

    # Delete existing seed characters to avoid duplicates
    await db.execute(
        delete(Character).where(Character.creator_id == sweetsin.id)
    )

    # Copy seed avatars to uploads dir if available
    import shutil
    import uuid as uuid_mod
    from pathlib import Path
    from app.config import settings

    seed_avatars_dir = Path(__file__).parent / "seed_avatars"
    avatars_dest = Path(settings.upload_dir) / "avatars"
    avatars_dest.mkdir(parents=True, exist_ok=True)

    for i, char_data in enumerate(SEED_CHARACTERS):
        avatar_url = None

        # Check for pre-generated avatar
        src = seed_avatars_dir / f"{i:02d}.webp"
        if src.exists():
            filename = f"{uuid_mod.uuid4().hex}.webp"
            dest = avatars_dest / filename
            shutil.copy2(src, dest)
            avatar_url = f"/api/uploads/avatars/{filename}"

        char = Character(
            creator_id=sweetsin.id,
            name=char_data["name"],
            tagline=char_data.get("tagline"),
            personality=char_data["personality"],
            appearance=char_data.get("appearance"),
            scenario=char_data.get("scenario"),
            greeting_message=char_data["greeting_message"],
            example_dialogues=char_data.get("example_dialogues"),
            tags=",".join(char_data.get("tags", [])),
            structured_tags=",".join(char_data.get("structured_tags", [])),
            content_rating=char_data.get("content_rating", "moderate"),
            response_length=char_data.get("response_length", "long"),
            avatar_url=avatar_url,
            is_public=True,
            preferred_model="auto",
        )
        db.add(char)

    await db.commit()
    return {"imported": len(SEED_CHARACTERS)}


@router.delete("/seed-characters")
async def delete_seed_characters(
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete all seed characters (created by @sweetsin)."""
    result = await db.execute(select(User).where(User.email == SWEETSIN_EMAIL))
    sweetsin = result.scalar_one_or_none()
    if not sweetsin:
        return {"deleted": 0}

    count_result = await db.execute(
        select(func.count()).select_from(Character).where(
            Character.creator_id == sweetsin.id
        )
    )
    count = count_result.scalar() or 0

    await db.execute(
        delete(Character).where(Character.creator_id == sweetsin.id)
    )
    await db.commit()
    return {"deleted": count}


# ── Orphan cleanup ──────────────────────────────────────────────


@router.post("/cleanup-avatars")
async def cleanup_orphan_avatars(
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete avatar files not referenced by any character or user."""
    from pathlib import Path
    from app.config import settings

    avatars_dir = Path(settings.upload_dir) / "avatars"
    if not avatars_dir.exists():
        return {"deleted": 0, "kept": 0}

    # Collect all referenced avatar URLs from DB
    char_result = await db.execute(
        select(Character.avatar_url).where(Character.avatar_url.isnot(None))
    )
    user_result = await db.execute(
        select(User.avatar_url).where(User.avatar_url.isnot(None))
    )
    referenced = set()
    for (url,) in char_result.all():
        # "/api/uploads/avatars/abc.webp" → "abc.webp"
        referenced.add(url.split("/")[-1])
    for (url,) in user_result.all():
        referenced.add(url.split("/")[-1])

    deleted = 0
    kept = 0
    for f in avatars_dir.iterdir():
        if f.is_file() and f.name not in referenced:
            f.unlink()
            deleted += 1
        else:
            kept += 1

    return {"deleted": deleted, "kept": kept}
