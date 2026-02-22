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
from app.config import settings

if settings.is_fiction_mode:
    from app.admin.seed_data_fiction import SEED_STORIES as SEED_CHARACTERS
    from app.admin.seed_data_fiction import FICTION_SYSTEM_EMAIL as SWEETSIN_EMAIL
    from app.admin.seed_data_fiction import FICTION_SYSTEM_USERNAME as SWEETSIN_USERNAME
else:
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


# ── Admin settings (stored in prompt_templates as setting.*) ──────────

_SETTING_DEFAULTS: dict[str, str] = {
    "setting.notify_registration": "true",
    "setting.notify_errors": "true",
    "setting.paid_mode": "false",
    "setting.cost_mode": "quality",  # quality | balanced | economy
    "setting.daily_message_limit": "1000",
    "setting.max_personas": "5",
    "setting.anon_message_limit": "20",
}


@router.get("/settings")
async def get_admin_settings(
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Return admin settings (key-value)."""
    result = await db.execute(
        select(PromptTemplate).where(PromptTemplate.key.like("setting.%"))
    )
    overrides = {row.key: row.value for row in result.scalars().all()}
    settings_out = {}
    for key, default_val in _SETTING_DEFAULTS.items():
        short_key = key.removeprefix("setting.")
        settings_out[short_key] = overrides.get(key, default_val)
    return settings_out


@router.put("/settings/{key}")
async def update_admin_setting(
    key: str,
    body: PromptUpdateBody,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update an admin setting."""
    full_key = f"setting.{key}"
    if full_key not in _SETTING_DEFAULTS:
        raise HTTPException(status_code=404, detail="Unknown setting")
    existing = await db.execute(select(PromptTemplate).where(PromptTemplate.key == full_key))
    row = existing.scalar_one_or_none()
    if row:
        row.value = body.value
        row.updated_at = datetime.utcnow()
    else:
        row = PromptTemplate(key=full_key, value=body.value)
        db.add(row)
    await db.commit()
    return {"key": key, "value": body.value}


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
    """Get or create the internal system user for seed content."""
    result = await db.execute(select(User).where(User.email == SWEETSIN_EMAIL))
    user = result.scalar_one_or_none()
    if user:
        return user

    import secrets
    import bcrypt as _bcrypt

    display = "Interactive Fiction" if settings.is_fiction_mode else "SweetSin"
    random_password = secrets.token_hex(32).encode()
    user = User(
        email=SWEETSIN_EMAIL,
        username=SWEETSIN_USERNAME,
        display_name=display,
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

    # Copy seed avatars to uploads dir if available (with thumbnails)
    import uuid as uuid_mod
    from pathlib import Path
    from PIL import Image
    from app.config import settings
    from app.uploads.router import _save_with_thumb

    seed_avatars_dir = Path(__file__).parent / "seed_avatars"
    avatars_dest = Path(settings.upload_dir) / "avatars"
    avatars_dest.mkdir(parents=True, exist_ok=True)

    import random

    for i, char_data in enumerate(SEED_CHARACTERS):
        avatar_url = None

        # Check for pre-generated avatar
        src = seed_avatars_dir / f"{i:02d}.webp"
        if src.exists():
            filename = f"{uuid_mod.uuid4().hex}.webp"
            img = Image.open(src)
            _save_with_thumb(img, avatars_dest, filename)
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
            base_chat_count={} if settings.is_fiction_mode else {"ru": random.randint(300, 3000), "en": random.randint(200, 2500)},
            base_like_count={} if settings.is_fiction_mode else {"ru": random.randint(100, 800), "en": random.randint(80, 600)},
            original_language=char_data.get("original_language", "ru"),
        )
        db.add(char)

    await db.flush()

    # Generate slugs for all imported characters
    from app.characters.slugify import generate_slug
    result2 = await db.execute(
        select(Character).where(Character.creator_id == sweetsin.id, Character.slug.is_(None))
    )
    for c in result2.scalars().all():
        c.slug = generate_slug(c.name, c.id)

    await db.commit()
    return {"imported": len(SEED_CHARACTERS)}


@router.post("/generate-slugs")
async def generate_character_slugs(
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate slugs for all characters that don't have one."""
    from app.characters.slugify import generate_slug

    result = await db.execute(
        select(Character).where(Character.slug.is_(None))
    )
    characters = result.scalars().all()
    for c in characters:
        c.slug = generate_slug(c.name, c.id)
    await db.commit()
    return {"updated": len(characters)}


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
        name = url.split("/")[-1]
        referenced.add(name)
        # Also keep thumbnail variant
        referenced.add(name.replace(".webp", "_thumb.webp"))
    for (url,) in user_result.all():
        name = url.split("/")[-1]
        referenced.add(name)
        referenced.add(name.replace(".webp", "_thumb.webp"))

    deleted = 0
    kept = 0
    for f in avatars_dir.iterdir():
        if f.is_file() and f.name not in referenced:
            f.unlink()
            deleted += 1
        else:
            kept += 1

    return {"deleted": deleted, "kept": kept}


# ── User management ────────────────────────────────────────────


@router.get("/users")
async def list_users(
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users with stats."""
    from sqlalchemy.orm import aliased

    char_count_sq = (
        select(func.count(Character.id))
        .where(Character.creator_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )

    result = await db.execute(
        select(User, char_count_sq.label("character_count"))
        .order_by(User.created_at.desc())
    )

    users = []
    for row in result.all():
        u = row[0]
        users.append({
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "display_name": u.display_name,
            "avatar_url": u.avatar_url,
            "role": u.role or "user",
            "is_banned": getattr(u, "is_banned", False) or False,
            "message_count": u.message_count or 0,
            "chat_count": u.chat_count or 0,
            "character_count": row[1] or 0,
            "language": u.language or "en",
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })
    return users


@router.put("/users/{user_id}/ban")
async def ban_user(
    user_id: str,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot ban yourself")
    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.is_banned = True
    await db.commit()
    return {"status": "banned"}


@router.put("/users/{user_id}/unban")
async def unban_user(
    user_id: str,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.is_banned = False
    await db.commit()
    return {"status": "unbanned"}


@router.delete("/users/{user_id}", status_code=204)
async def admin_delete_user(
    user_id: str,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    from pathlib import Path
    from sqlalchemy.orm import selectinload
    from app.config import settings

    result = await db.execute(
        select(User)
        .options(selectinload(User.characters))
        .where(User.id == user_id)
    )
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete avatar files
    avatars_dir = Path(settings.upload_dir) / "avatars"
    for char in u.characters:
        if char.avatar_url and char.avatar_url.startswith("/api/uploads/avatars/"):
            f = avatars_dir / char.avatar_url.split("/")[-1]
            if f.exists():
                f.unlink(missing_ok=True)
    if u.avatar_url and u.avatar_url.startswith("/api/uploads/avatars/"):
        f = avatars_dir / u.avatar_url.split("/")[-1]
        if f.exists():
            f.unlink(missing_ok=True)

    await db.delete(u)
    await db.commit()
