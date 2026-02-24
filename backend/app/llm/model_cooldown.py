"""Cooldown mechanism for failed models and provider-level blacklisting.

When a model returns an error, it gets excluded from auto-fallback
for COOLDOWN_SECONDS. This prevents repeatedly hitting broken models.

Models returning 404 (not found) get a much longer ban (24h) since
the model was likely removed by the provider.

Providers returning 402 (no balance) get blacklisted entirely for 6h.
Admin can also manually disable providers via settings.
"""

import time
import logging

logger = logging.getLogger(__name__)

COOLDOWN_SECONDS = 15 * 60  # 15 minutes for transient errors
NOT_FOUND_SECONDS = 24 * 60 * 60  # 24 hours for 404 / model removed
PROVIDER_BLACKLIST_SECONDS = 6 * 60 * 60  # 6 hours for 402 / no balance

_cooldowns: dict[str, float] = {}
_not_found: dict[str, float] = {}

# Provider-level blacklist (402 no balance)
_provider_blacklist: dict[str, float] = {}  # provider -> monotonic timestamp
_provider_alert_sent: dict[str, float] = {}  # dedup: provider -> monotonic timestamp
_admin_disabled: set[str] = set()  # manually disabled by admin (synced from DB)


def mark_failed(provider: str, model_id: str) -> None:
    """Mark a model as failed — exclude from auto for 15 min."""
    _cooldowns[f"{provider}:{model_id}"] = time.monotonic()


def mark_not_found(provider: str, model_id: str) -> None:
    """Mark a model as not found (404) — exclude for 24h."""
    key = f"{provider}:{model_id}"
    _not_found[key] = time.monotonic()
    _cooldowns.pop(key, None)  # no need for short cooldown too
    logger.warning(f"Model {key} marked as not found — banned for 24h")


def is_available(provider: str, model_id: str) -> bool:
    """Check if a model is available (not in cooldown or banned)."""
    key = f"{provider}:{model_id}"
    # Check 404 ban first (longer)
    if key in _not_found:
        elapsed = time.monotonic() - _not_found[key]
        if elapsed >= NOT_FOUND_SECONDS:
            del _not_found[key]
        else:
            return False
    # Check transient cooldown
    if key in _cooldowns:
        elapsed = time.monotonic() - _cooldowns[key]
        if elapsed >= COOLDOWN_SECONDS:
            del _cooldowns[key]
        else:
            return False
    return True


def is_not_found(provider: str, model_id: str) -> bool:
    """Check if a model is banned as not found."""
    key = f"{provider}:{model_id}"
    if key not in _not_found:
        return False
    elapsed = time.monotonic() - _not_found[key]
    if elapsed >= NOT_FOUND_SECONDS:
        del _not_found[key]
        return False
    return True


def filter_available(provider: str, models: list[str]) -> list[str]:
    """Filter out models that are in cooldown or banned."""
    return [m for m in models if is_available(provider, m)]


# ── Provider-level blacklist (402 / no balance) ─────────────────


def mark_provider_no_balance(provider: str) -> None:
    """Blacklist entire provider for 6 hours (no balance / 402)."""
    _provider_blacklist[provider] = time.monotonic()
    logger.warning("Provider %s blacklisted for 6h (402 no balance)", provider)


def is_provider_available(provider: str) -> bool:
    """Check if a provider is available (not blacklisted and not admin-disabled)."""
    if provider in _admin_disabled:
        return False
    if provider in _provider_blacklist:
        elapsed = time.monotonic() - _provider_blacklist[provider]
        if elapsed >= PROVIDER_BLACKLIST_SECONDS:
            del _provider_blacklist[provider]
        else:
            return False
    return True


def clear_provider_blacklist(provider: str) -> None:
    """Remove auto-blacklist for a provider (admin unblock)."""
    _provider_blacklist.pop(provider, None)
    logger.info("Provider %s blacklist cleared by admin", provider)


def should_send_balance_alert(provider: str) -> bool:
    """Check if we should send an email alert (dedup: max 1 per 6h per provider)."""
    now = time.monotonic()
    last = _provider_alert_sent.get(provider, 0)
    if now - last < PROVIDER_BLACKLIST_SECONDS:
        return False
    _provider_alert_sent[provider] = now
    return True


def get_blacklisted_providers() -> dict[str, dict]:
    """Return currently blacklisted providers with remaining seconds (for admin UI)."""
    now = time.monotonic()
    result = {}
    expired = []
    for prov, ts in _provider_blacklist.items():
        elapsed = now - ts
        if elapsed >= PROVIDER_BLACKLIST_SECONDS:
            expired.append(prov)
        else:
            result[prov] = {
                "remaining_seconds": int(PROVIDER_BLACKLIST_SECONDS - elapsed),
                "reason": "402 no balance",
            }
    for prov in expired:
        del _provider_blacklist[prov]
    return result


def get_admin_disabled() -> set[str]:
    """Return set of admin-disabled providers."""
    return set(_admin_disabled)


def set_admin_disabled(disabled: set[str]) -> None:
    """Update the set of admin-disabled providers."""
    _admin_disabled.clear()
    _admin_disabled.update(disabled)


def _is_402_error(e: Exception) -> bool:
    """Detect 402 Payment Required / insufficient balance errors."""
    err = str(e)
    if "402" in err:
        return True
    low = err.lower()
    return any(phrase in low for phrase in (
        "insufficient balance", "insufficient_balance",
        "payment required", "billing", "quota exceeded",
        "exceeded your current quota", "no balance",
        "insufficient_quota", "account_deactivated",
    ))


def handle_402_if_applicable(provider: str, error: Exception) -> None:
    """If the error is a 402, blacklist the provider and schedule an alert email."""
    if not _is_402_error(error):
        return
    mark_provider_no_balance(provider)
    if should_send_balance_alert(provider):
        # Fire-and-forget email alert (imported lazily to avoid circular imports)
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_send_balance_alert_async(provider, error))
        except RuntimeError:
            pass  # no running loop (e.g. in tests)


async def _send_balance_alert_async(provider: str, error: Exception) -> None:
    """Send balance alert email (async, fire-and-forget)."""
    try:
        from app.utils.email import send_balance_alert
        await send_balance_alert(provider, str(error))
    except Exception:
        logger.exception("Failed to send balance alert for %s", provider)
