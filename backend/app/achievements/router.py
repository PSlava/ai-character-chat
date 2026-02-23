from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.auth.middleware import get_current_user
from app.achievements.definitions import get_all_definitions
from app.achievements.checker import get_user_achievements, get_user_progress

router = APIRouter(prefix="/api/achievements", tags=["achievements"])


@router.get("")
async def list_achievements(
    language: str = "en",
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all achievements with user's unlock status and progress."""
    definitions = get_all_definitions(language)
    unlocked = await get_user_achievements(db, user["id"])
    progress = await get_user_progress(db, user["id"])

    result = []
    for d in definitions:
        aid = d["id"]
        achieved_at = unlocked.get(aid)
        entry = {
            **d,
            "unlocked": achieved_at is not None,
            "achieved_at": achieved_at.isoformat() if achieved_at else None,
        }
        if d.get("target"):
            entry["progress"] = min(progress.get(aid, 0), d["target"])
        result.append(entry)
    return result
