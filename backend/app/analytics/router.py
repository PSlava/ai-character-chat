"""Analytics endpoints: page view tracking (public) + admin dashboard."""

import asyncio
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.collector import record_pageview
from app.analytics.schemas import PageViewRequest
from app.auth.middleware import get_current_user_optional
from app.auth.rate_limit import RateLimiter, get_client_ip
from app.admin.router import require_admin
from app.db.session import get_db

router = APIRouter(prefix="/api", tags=["analytics"])

# Rate limit: 60 pageview pings per minute per IP
_pageview_limiter = RateLimiter(max_requests=60, window_seconds=60)


@router.post("/analytics/pageview", status_code=204)
async def track_pageview(
    body: PageViewRequest,
    request: Request,
    user: dict | None = Depends(get_current_user_optional),
):
    """Record a page view. Public endpoint — works for anonymous and authenticated users."""
    # Don't track admin visits
    if user and user.get("role") == "admin":
        return

    ip = get_client_ip(request)
    if not _pageview_limiter.check(f"pv:{ip}"):
        return  # silently drop if rate limited

    user_agent = request.headers.get("user-agent")
    accept_lang = request.headers.get("accept-language")
    user_id = user["id"] if user else None

    # Fire-and-forget — don't block the response
    asyncio.create_task(record_pageview(
        path=body.path,
        ip=ip,
        user_agent=user_agent,
        referrer=body.referrer,
        accept_language=accept_lang,
        user_id=user_id,
    ))


@router.get("/admin/analytics/overview")
async def analytics_overview(
    days: int = Query(default=7, ge=1, le=365),
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin analytics dashboard — traffic, users, content."""
    since = datetime.utcnow() - timedelta(days=days)

    # Run all queries in parallel
    (
        summary_res,
        daily_pv_res,
        daily_reg_res,
        daily_msg_res,
        daily_chat_res,
        top_pages_res,
        top_referrers_res,
        top_chars_res,
        devices_res,
        models_res,
        countries_res,
        anon_res,
    ) = await asyncio.gather(
        _query_summary(db, since),
        _query_daily_pageviews(db, since),
        _query_daily_registrations(db, since),
        _query_daily_messages(db, since),
        _query_daily_chats(db, since),
        _query_top_pages(db, since),
        _query_top_referrers(db, since),
        _query_top_characters(db, since),
        _query_devices(db, since),
        _query_models(db, since),
        _query_countries(db, since),
        _query_anon_stats(db, since),
    )

    # Merge daily stats into single list
    daily = _merge_daily(daily_pv_res, daily_reg_res, daily_msg_res, daily_chat_res, since, days)

    return {
        "summary": summary_res,
        "daily": daily,
        "top_pages": top_pages_res,
        "top_referrers": top_referrers_res,
        "top_characters": top_chars_res,
        "devices": devices_res,
        "models": models_res,
        "countries": countries_res,
        "anon_stats": anon_res,
    }


# --- Query helpers ---

_EXCLUDE_SYSTEM = "AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = {user_col} AND (u.role = 'admin' OR u.email IN ('system@sweetsin.cc', 'anonymous@system.local')))"
_PV_NO_SYSTEM = "AND (user_id IS NULL OR NOT EXISTS (SELECT 1 FROM users u WHERE u.id = page_views.user_id AND (u.role = 'admin' OR u.email IN ('system@sweetsin.cc', 'anonymous@system.local'))))"


async def _query_summary(db: AsyncSession, since: datetime) -> dict:
    """Summary card numbers (excluding admins and system users)."""
    users_total = (await db.execute(text(
        "SELECT COUNT(*) FROM users WHERE role != 'admin' AND email NOT IN ('system@sweetsin.cc', 'anonymous@system.local')"
    ))).scalar() or 0
    users_new = (await db.execute(text(
        "SELECT COUNT(*) FROM users WHERE created_at >= :since AND role != 'admin' AND email NOT IN ('system@sweetsin.cc', 'anonymous@system.local')"
    ), {"since": since})).scalar() or 0
    pageviews = (await db.execute(text(
        f"SELECT COUNT(*) FROM page_views WHERE created_at >= :since {_PV_NO_SYSTEM}"
    ), {"since": since})).scalar() or 0
    unique_visitors = (await db.execute(text(
        f"SELECT COUNT(DISTINCT ip_hash) FROM page_views WHERE created_at >= :since {_PV_NO_SYSTEM}"
    ), {"since": since})).scalar() or 0
    messages = (await db.execute(text(
        "SELECT COUNT(*) FROM messages m JOIN chats ch ON ch.id = m.chat_id WHERE m.created_at >= :since AND m.role = 'user'"
        f" {_EXCLUDE_SYSTEM.format(user_col='ch.user_id')}"
    ), {"since": since})).scalar() or 0
    new_chats = (await db.execute(text(
        f"SELECT COUNT(*) FROM chats WHERE created_at >= :since {_EXCLUDE_SYSTEM.format(user_col='chats.user_id')}"
    ), {"since": since})).scalar() or 0

    return {
        "users_total": users_total,
        "users_new": users_new,
        "pageviews": pageviews,
        "unique_visitors": unique_visitors,
        "messages": messages,
        "new_chats": new_chats,
    }


async def _query_daily_pageviews(db: AsyncSession, since: datetime) -> dict[str, dict]:
    rows = (await db.execute(text(f"""
        SELECT DATE(created_at) as d, COUNT(*) as pv, COUNT(DISTINCT ip_hash) as uv
        FROM page_views WHERE created_at >= :since {_PV_NO_SYSTEM}
        GROUP BY DATE(created_at) ORDER BY d
    """), {"since": since})).fetchall()
    return {str(r[0]): {"pageviews": r[1], "unique_visitors": r[2]} for r in rows}


async def _query_daily_registrations(db: AsyncSession, since: datetime) -> dict[str, int]:
    rows = (await db.execute(text("""
        SELECT DATE(created_at) as d, COUNT(*) as cnt
        FROM users WHERE created_at >= :since AND role != 'admin'
        AND email NOT IN ('system@sweetsin.cc', 'anonymous@system.local')
        GROUP BY DATE(created_at) ORDER BY d
    """), {"since": since})).fetchall()
    return {str(r[0]): r[1] for r in rows}


async def _query_daily_messages(db: AsyncSession, since: datetime) -> dict[str, int]:
    rows = (await db.execute(text(f"""
        SELECT DATE(m.created_at) as d, COUNT(*) as cnt
        FROM messages m JOIN chats ch ON ch.id = m.chat_id
        WHERE m.created_at >= :since AND m.role = 'user'
        {_EXCLUDE_SYSTEM.format(user_col='ch.user_id')}
        GROUP BY DATE(m.created_at) ORDER BY d
    """), {"since": since})).fetchall()
    return {str(r[0]): r[1] for r in rows}


async def _query_daily_chats(db: AsyncSession, since: datetime) -> dict[str, int]:
    rows = (await db.execute(text(f"""
        SELECT DATE(created_at) as d, COUNT(*) as cnt
        FROM chats WHERE created_at >= :since
        {_EXCLUDE_SYSTEM.format(user_col='chats.user_id')}
        GROUP BY DATE(created_at) ORDER BY d
    """), {"since": since})).fetchall()
    return {str(r[0]): r[1] for r in rows}


async def _query_top_pages(db: AsyncSession, since: datetime) -> list[dict]:
    rows = (await db.execute(text(f"""
        SELECT path, COUNT(*) as views, COUNT(DISTINCT ip_hash) as uniq
        FROM page_views WHERE created_at >= :since {_PV_NO_SYSTEM}
        GROUP BY path ORDER BY views DESC LIMIT 20
    """), {"since": since})).fetchall()
    return [{"path": r[0], "views": r[1], "unique": r[2]} for r in rows]


async def _query_top_referrers(db: AsyncSession, since: datetime) -> list[dict]:
    rows = (await db.execute(text(f"""
        SELECT referrer, COUNT(*) as views, COUNT(DISTINCT ip_hash) as uniq
        FROM page_views WHERE created_at >= :since AND referrer IS NOT NULL AND referrer != ''
        {_PV_NO_SYSTEM}
        GROUP BY referrer ORDER BY views DESC LIMIT 20
    """), {"since": since})).fetchall()
    return [{"referrer": r[0], "views": r[1], "unique": r[2]} for r in rows]


async def _query_top_characters(db: AsyncSession, since: datetime) -> list[dict]:
    rows = (await db.execute(text(f"""
        SELECT c.id, c.name, c.avatar_url, COUNT(m.id) as msg_count
        FROM characters c
        JOIN chats ch ON ch.character_id = c.id
        JOIN messages m ON m.chat_id = ch.id
        WHERE m.created_at >= :since AND m.role = 'user'
        {_EXCLUDE_SYSTEM.format(user_col='ch.user_id')}
        GROUP BY c.id, c.name, c.avatar_url
        ORDER BY msg_count DESC LIMIT 10
    """), {"since": since})).fetchall()
    return [{"id": r[0], "name": r[1], "avatar_url": r[2], "messages": r[3]} for r in rows]


async def _query_devices(db: AsyncSession, since: datetime) -> dict:
    rows = (await db.execute(text(f"""
        SELECT device, COUNT(*) as cnt
        FROM page_views WHERE created_at >= :since AND device IS NOT NULL
        {_PV_NO_SYSTEM}
        GROUP BY device
    """), {"since": since})).fetchall()
    result = {"mobile": 0, "desktop": 0, "tablet": 0}
    for r in rows:
        if r[0] in result:
            result[r[0]] = r[1]
    return result


async def _query_countries(db: AsyncSession, since: datetime) -> list[dict]:
    rows = (await db.execute(text(f"""
        SELECT country, COUNT(*) as views, COUNT(DISTINCT ip_hash) as uniq
        FROM page_views
        WHERE created_at >= :since AND country IS NOT NULL
        {_PV_NO_SYSTEM}
        GROUP BY country ORDER BY uniq DESC LIMIT 20
    """), {"since": since})).fetchall()
    return [{"country": r[0], "views": r[1], "unique": r[2]} for r in rows]


async def _query_models(db: AsyncSession, since: datetime) -> list[dict]:
    rows = (await db.execute(text("""
        SELECT model_used, COUNT(*) as cnt
        FROM messages
        WHERE created_at >= :since AND model_used IS NOT NULL AND role = 'assistant'
        GROUP BY model_used ORDER BY cnt DESC
    """), {"since": since})).fetchall()
    return [{"model": r[0], "count": r[1]} for r in rows]


async def _query_anon_stats(db: AsyncSession, since: datetime) -> dict:
    """Anonymous user statistics — unique sessions, messages, chats."""
    unique_sessions = (await db.execute(text(
        "SELECT COUNT(DISTINCT anon_session_id) FROM chats "
        "WHERE anon_session_id IS NOT NULL AND created_at >= :since"
    ), {"since": since})).scalar() or 0
    total_sessions = (await db.execute(text(
        "SELECT COUNT(DISTINCT anon_session_id) FROM chats "
        "WHERE anon_session_id IS NOT NULL"
    ))).scalar() or 0
    anon_messages = (await db.execute(text(
        "SELECT COUNT(*) FROM messages m JOIN chats c ON c.id = m.chat_id "
        "WHERE c.anon_session_id IS NOT NULL AND m.role = 'user' AND m.created_at >= :since"
    ), {"since": since})).scalar() or 0
    anon_chats = (await db.execute(text(
        "SELECT COUNT(*) FROM chats "
        "WHERE anon_session_id IS NOT NULL AND created_at >= :since"
    ), {"since": since})).scalar() or 0
    total_anon_messages = (await db.execute(text(
        "SELECT COUNT(*) FROM messages m JOIN chats c ON c.id = m.chat_id "
        "WHERE c.anon_session_id IS NOT NULL AND m.role = 'user'"
    ))).scalar() or 0
    return {
        "unique_sessions": unique_sessions,
        "total_sessions": total_sessions,
        "messages": anon_messages,
        "chats": anon_chats,
        "total_messages": total_anon_messages,
    }


def _merge_daily(
    pv: dict[str, dict],
    reg: dict[str, int],
    msg: dict[str, int],
    chats: dict[str, int],
    since: datetime,
    days: int,
) -> list[dict]:
    """Merge separate daily dicts into a single list with all fields for each day."""
    result = []
    for i in range(days):
        d = (since + timedelta(days=i)).strftime("%Y-%m-%d")
        pv_data = pv.get(d, {})
        result.append({
            "date": d,
            "pageviews": pv_data.get("pageviews", 0),
            "unique_visitors": pv_data.get("unique_visitors", 0),
            "registrations": reg.get(d, 0),
            "messages": msg.get(d, 0),
            "chats": chats.get(d, 0),
        })
    return result
