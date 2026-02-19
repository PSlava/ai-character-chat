"""Cooldown mechanism for failed models.

When a model returns an error, it gets excluded from auto-fallback
for COOLDOWN_SECONDS. This prevents repeatedly hitting broken models.

Models returning 404 (not found) get a much longer ban (24h) since
the model was likely removed by the provider.
"""

import time
import logging

logger = logging.getLogger(__name__)

COOLDOWN_SECONDS = 15 * 60  # 15 minutes for transient errors
NOT_FOUND_SECONDS = 24 * 60 * 60  # 24 hours for 404 / model removed

_cooldowns: dict[str, float] = {}
_not_found: dict[str, float] = {}


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
