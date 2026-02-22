from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import User, Message, Character, Chat
from app.config import settings

router = APIRouter(prefix="/api/stats", tags=["stats"])

BASE_USERS = 1200 if settings.is_nsfw_mode else 0
BASE_MESSAGES = 45000 if settings.is_nsfw_mode else 0

# System emails excluded from public stats
_SYSTEM_EMAILS = ("system@sweetsin.cc", "system@fiction.local", "anonymous@system.local")


@router.get("")
async def get_stats(db: AsyncSession = Depends(get_db)):
    # Exclude admins and system users from counts
    users = (await db.execute(
        select(func.count()).select_from(User).where(
            User.role != "admin",
            User.email.notin_(_SYSTEM_EMAILS),
        )
    )).scalar_one()

    # Exclude messages from admin/system user chats
    admin_ids_sq = select(User.id).where(
        (User.role == "admin") | User.email.in_(_SYSTEM_EMAILS)
    ).scalar_subquery()
    messages = (await db.execute(
        select(func.count()).select_from(Message).where(
            ~Message.chat_id.in_(
                select(Chat.id).where(Chat.user_id.in_(admin_ids_sq))
            )
        )
    )).scalar_one()

    characters = (await db.execute(
        select(func.count()).select_from(Character).where(Character.is_public == True)
    )).scalar_one()

    result = {
        "users": users + BASE_USERS,
        "messages": messages + BASE_MESSAGES,
        "characters": characters,
        "online_now": characters,
    }

    if settings.is_fiction_mode:
        result["online_now"] = 0
        result["stories"] = characters

    return result
