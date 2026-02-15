"""Page view collection utilities — IP hashing, device detection, GeoIP, async recording."""

import hashlib
import logging
from datetime import date

import httpx

from app.config import settings
from app.db.session import engine as db_engine
from app.db.models import PageView

logger = logging.getLogger(__name__)

# In-memory IP → country cache (IP never changes country, so no TTL needed)
_country_cache: dict[str, str | None] = {}
_GEOIP_URL = "http://ip-api.com/json/{ip}?fields=countryCode"


def hash_ip(ip: str) -> str:
    """SHA256(ip + daily_salt). Same IP → same hash within a day (for unique visitors).
    Different hash each day (can't track user across days — privacy)."""
    daily_salt = hashlib.sha256(
        (date.today().isoformat() + settings.jwt_secret).encode()
    ).hexdigest()
    return hashlib.sha256((ip + daily_salt).encode()).hexdigest()


def parse_device(user_agent: str | None) -> str:
    """Simple keyword-based device detection. No external libraries."""
    if not user_agent:
        return "desktop"
    ua = user_agent.lower()
    if any(kw in ua for kw in ("ipad", "tablet", "kindle", "silk")):
        return "tablet"
    if any(kw in ua for kw in ("mobile", "android", "iphone", "ipod", "opera mini", "opera mobi")):
        return "mobile"
    return "desktop"


def parse_language(accept_language: str | None) -> str | None:
    """Extract primary language from Accept-Language header."""
    if not accept_language:
        return None
    # "en-US,en;q=0.9,ru;q=0.8" → "en"
    first = accept_language.split(",")[0].strip()
    lang = first.split(";")[0].strip().split("-")[0].lower()
    return lang if lang else None


async def lookup_country(ip: str) -> str | None:
    """Resolve IP → 2-letter country code via ip-api.com. Uses in-memory cache."""
    if ip in _country_cache:
        return _country_cache[ip]

    # Skip private/local IPs
    if ip.startswith(("127.", "10.", "192.168.", "172.16.", "::1", "fe80")):
        _country_cache[ip] = None
        return None

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                _GEOIP_URL.format(ip=ip),
                timeout=3.0,
            )
            if resp.status_code == 200:
                code = resp.json().get("countryCode")
                if code and len(code) == 2:
                    _country_cache[ip] = code
                    return code
    except Exception:
        pass

    _country_cache[ip] = None
    return None


async def record_pageview(
    path: str,
    ip: str,
    user_agent: str | None,
    referrer: str | None,
    accept_language: str | None,
    user_id: str | None,
) -> None:
    """Insert a page view record. Never raises — errors are silently logged."""
    try:
        from sqlalchemy import insert
        ip_hashed = hash_ip(ip)
        device = parse_device(user_agent)
        language = parse_language(accept_language)
        country = await lookup_country(ip)

        # Truncate fields to prevent DB errors
        if referrer and len(referrer) > 1000:
            referrer = referrer[:1000]
        if path and len(path) > 500:
            path = path[:500]

        async with db_engine.begin() as conn:
            await conn.execute(
                insert(PageView).values(
                    path=path,
                    ip_hash=ip_hashed,
                    user_id=user_id,
                    user_agent=user_agent[:500] if user_agent and len(user_agent) > 500 else user_agent,
                    device=device,
                    referrer=referrer,
                    language=language,
                    country=country,
                )
            )
    except Exception as e:
        logger.warning("Failed to record pageview: %s", str(e)[:200])
