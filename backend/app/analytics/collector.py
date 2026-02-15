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
_GEOIP_URLS = [
    ("https://api.country.is/{ip}", "country"),         # HTTPS, free, fast
    ("http://ip-api.com/json/{ip}?fields=countryCode", "countryCode"),  # fallback
]


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


def _is_private_ip(ip: str) -> bool:
    """Check if IP is private/local (including Docker 172.16-31 range)."""
    if ip.startswith(("127.", "10.", "192.168.", "::1", "fe80", "0.")):
        return True
    # 172.16.0.0 - 172.31.255.255 (private + Docker)
    if ip.startswith("172."):
        parts = ip.split(".")
        if len(parts) >= 2 and parts[1].isdigit():
            second = int(parts[1])
            if 16 <= second <= 31:
                return True
    return False


async def lookup_country(ip: str) -> str | None:
    """Resolve IP → 2-letter country code. Tries multiple GeoIP APIs with fallback."""
    if ip in _country_cache:
        return _country_cache[ip]

    if _is_private_ip(ip):
        _country_cache[ip] = None
        return None

    for url_template, json_key in _GEOIP_URLS:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    url_template.format(ip=ip),
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    code = resp.json().get(json_key)
                    if code and isinstance(code, str) and len(code) == 2:
                        _country_cache[ip] = code.upper()
                        return code.upper()
        except Exception as e:
            logger.debug("GeoIP lookup failed for %s via %s: %s", ip, url_template, e)
            continue

    logger.warning("All GeoIP lookups failed for IP %s", ip[:20])
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
