"""Daily message limit per user. Admins are exempt."""
import time
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, func, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Message, Chat
from app.db.session import engine as db_engine

# Generic setting cache: key -> (value, timestamp)
_setting_cache: dict[str, tuple[int, float]] = {}
_CACHE_TTL = 60  # seconds


async def _get_setting_int(key: str, default: int) -> int:
    """Read an integer admin setting with 60s cache."""
    now = time.monotonic()
    cached = _setting_cache.get(key)
    if cached and now - cached[1] < _CACHE_TTL:
        return cached[0]
    try:
        async with db_engine.connect() as conn:
            row = await conn.execute(
                sa_text("SELECT value FROM prompt_templates WHERE key = :key"),
                {"key": f"setting.{key}"},
            )
            val = row.scalar_one_or_none()
            result = int(val) if val else default
    except Exception:
        result = default
    _setting_cache[key] = (result, now)
    return result


async def _get_daily_limit() -> int:
    return await _get_setting_int("daily_message_limit", 1000)


async def get_max_personas() -> int:
    return await _get_setting_int("max_personas", 5)


async def _count_user_messages_today(user_id: str) -> int:
    """Count user messages sent today (UTC) across all chats."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    async with db_engine.connect() as conn:
        result = await conn.execute(
            sa_text("""
                SELECT COUNT(*) FROM messages m
                JOIN chats c ON m.chat_id = c.id
                WHERE c.user_id = :uid
                AND m.role = 'user'
                AND m.created_at >= :today
            """),
            {"uid": user_id, "today": today_start},
        )
        return result.scalar() or 0


async def check_daily_limit(user_id: str, user_role: str):
    """Raise 429 if user exceeded daily message limit. Admins are exempt."""
    if user_role == "admin":
        return
    limit = await _get_daily_limit()
    if limit <= 0:
        return  # 0 = unlimited
    count = await _count_user_messages_today(user_id)
    if count >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Daily message limit reached ({count}/{limit})",
        )


async def get_daily_usage(user_id: str) -> dict:
    """Return {used, limit} for the current user today."""
    limit = await _get_daily_limit()
    used = await _count_user_messages_today(user_id)
    return {"used": used, "limit": limit}
