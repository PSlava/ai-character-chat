"""Page view collection utilities — IP hashing, device detection, GeoIP, async recording."""

import gzip
import hashlib
import logging
import os
import time
import urllib.request
from datetime import date

import maxminddb

from app.config import settings
from app.db.session import engine as db_engine
from app.db.models import PageView

logger = logging.getLogger(__name__)

# In-memory IP → country cache (IP never changes country, so no TTL needed)
_country_cache: dict[str, str | None] = {}

# Local GeoIP database (DB-IP Lite Country MMDB)
_GEOIP_DB_PATH = os.environ.get("GEOIP_DB_PATH", "/app/geoip.mmdb")
_geoip_reader: maxminddb.Reader | None = None
_geoip_tried = False


_GEOIP_MAX_AGE_DAYS = 30
_GEOIP_URL = "https://download.db-ip.com/free/dbip-country-lite-{month}.mmdb.gz"


def refresh_geoip_db() -> None:
    """Download fresh GeoIP DB if missing or older than 30 days."""
    try:
        if os.path.exists(_GEOIP_DB_PATH):
            age_days = (time.time() - os.path.getmtime(_GEOIP_DB_PATH)) / 86400
            if age_days < _GEOIP_MAX_AGE_DAYS:
                logger.info("GeoIP DB is fresh (%.0f days old)", age_days)
                return

        month = date.today().strftime("%Y-%m")
        url = _GEOIP_URL.format(month=month)
        logger.info("Downloading GeoIP DB: %s", url)

        tmp_path = _GEOIP_DB_PATH + ".tmp.gz"
        urllib.request.urlretrieve(url, tmp_path)
        with gzip.open(tmp_path, "rb") as f:
            data = f.read()
        with open(_GEOIP_DB_PATH, "wb") as f:
            f.write(data)
        os.remove(tmp_path)

        # Reset reader so it reloads on next lookup
        global _geoip_reader, _geoip_tried
        if _geoip_reader:
            _geoip_reader.close()
        _geoip_reader = None
        _geoip_tried = False

        logger.info("GeoIP DB updated: %d KB", len(data) // 1024)
    except Exception as e:
        logger.warning("Failed to update GeoIP DB: %s", e)


def _get_geoip_reader() -> maxminddb.Reader | None:
    global _geoip_reader, _geoip_tried
    if _geoip_reader is not None:
        return _geoip_reader
    if _geoip_tried:
        return None
    _geoip_tried = True
    try:
        _geoip_reader = maxminddb.open_database(_GEOIP_DB_PATH)
        logger.info("GeoIP database loaded: %s", _GEOIP_DB_PATH)
    except Exception as e:
        logger.warning("GeoIP database not available: %s", e)
    return _geoip_reader


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
    if ip.startswith("172."):
        parts = ip.split(".")
        if len(parts) >= 2 and parts[1].isdigit():
            second = int(parts[1])
            if 16 <= second <= 31:
                return True
    return False


def lookup_country(ip: str) -> str | None:
    """Resolve IP → 2-letter country code via local MMDB database. Instant, no network."""
    if ip in _country_cache:
        return _country_cache[ip]

    if _is_private_ip(ip):
        _country_cache[ip] = None
        return None

    reader = _get_geoip_reader()
    if reader:
        try:
            data = reader.get(ip)
            if data and isinstance(data, dict):
                country = data.get("country")
                if isinstance(country, dict):
                    code = country.get("iso_code")
                    if code and isinstance(code, str) and len(code) == 2:
                        _country_cache[ip] = code.upper()
                        return code.upper()
        except Exception as e:
            logger.debug("GeoIP lookup failed for %s: %s", ip, e)

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
        country = lookup_country(ip)

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
