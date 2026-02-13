import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import User, Message, Character

router = APIRouter(prefix="/api/stats", tags=["stats"])

BASE_USERS = 1200
BASE_MESSAGES = 45000


@router.get("")
async def get_stats(db: AsyncSession = Depends(get_db)):
    users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    messages = (await db.execute(select(func.count()).select_from(Message))).scalar_one()
    characters = (await db.execute(
        select(func.count()).select_from(Character).where(Character.is_public == True)
    )).scalar_one()

    # Pseudo-random "online now" stable per 5-minute window
    now = datetime.now(timezone.utc)
    window = f"{now.year}-{now.month}-{now.day}-{now.hour}-{now.minute // 5}"
    seed = int(hashlib.md5(window.encode()).hexdigest()[:8], 16)
    online_now = 15 + (seed % 31)  # 15-45

    return {
        "users": users + BASE_USERS,
        "messages": messages + BASE_MESSAGES,
        "characters": characters,
        "online_now": online_now,
    }
