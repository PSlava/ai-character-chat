"""Anonymous (guest) chat support.

Anonymous users can chat without registering, tracked by session ID.
Admin setting `anon_message_limit` controls the limit:
  0 = anonymous chat disabled (must register)
  >0 = max messages before registration prompt (default 50)
"""
import time

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.session import engine as db_engine

# Cached system anonymous user ID
_anon_user_id: str | None = None
ANON_EMAIL = "anonymous@system.local"

# Setting cache: (value, timestamp)
_limit_cache: tuple[int, float] = (20, 0.0)
_CACHE_TTL = 60


async def get_anon_user_id(db: AsyncSession) -> str:
    """Get or create the system anonymous user. Cached after first call."""
    global _anon_user_id
    if _anon_user_id:
        return _anon_user_id

    result = await db.execute(select(User.id).where(User.email == ANON_EMAIL))
    uid = result.scalar_one_or_none()
    if uid:
        _anon_user_id = uid
        return uid

    user = User(
        email=ANON_EMAIL,
        username="anonymous",
        display_name="Guest",
        role="user",
    )
    db.add(user)
    await db.commit()
    _anon_user_id = user.id
    return user.id


async def get_anon_message_limit() -> int:
    """Get admin-configurable anonymous message limit. 0 = disabled, >0 = limit."""
    global _limit_cache
    now = time.monotonic()
    if now - _limit_cache[1] < _CACHE_TTL:
        return _limit_cache[0]
    try:
        async with db_engine.connect() as conn:
            row = await conn.execute(
                sa_text("SELECT value FROM prompt_templates WHERE key = 'setting.anon_message_limit'")
            )
            val = row.scalar_one_or_none()
            result = int(val) if val else 20
    except Exception:
        result = 20
    _limit_cache = (result, now)
    return result


async def count_anon_messages(session_id: str) -> int:
    """Count total user messages sent by this anonymous session."""
    async with db_engine.connect() as conn:
        result = await conn.execute(
            sa_text("""
                SELECT COUNT(*) FROM messages m
                JOIN chats c ON m.chat_id = c.id
                WHERE c.anon_session_id = :sid
                AND m.role = 'user'
            """),
            {"sid": session_id},
        )
        return result.scalar() or 0


async def check_anon_limit(session_id: str) -> int:
    """Check anonymous message limit. Returns remaining messages.

    Raises HTTPException 403 with detail:
      - "anon_chat_disabled" if limit is 0
      - "anon_limit_reached" if messages exhausted
    """
    limit = await get_anon_message_limit()
    if limit <= 0:
        raise HTTPException(status_code=403, detail="anon_chat_disabled")
    used = await count_anon_messages(session_id)
    remaining = limit - used
    if remaining <= 0:
        raise HTTPException(status_code=403, detail="anon_limit_reached")
    return remaining


async def get_anon_remaining(session_id: str) -> int:
    """Return remaining anonymous messages (without raising)."""
    limit = await get_anon_message_limit()
    if limit <= 0:
        return 0
    used = await count_anon_messages(session_id)
    return max(0, limit - used)
