from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_user
from app.db.session import get_db
from app.db.models import PromptTemplate
from app.chat.prompt_builder import get_all_keys, load_overrides, invalidate_cache
from app.db.session import engine

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def require_admin(user=Depends(get_current_user)):
    if user.get("role") != "admin":
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
