"""Cooldown mechanism for failed models.

When a model returns an error, it gets excluded from auto-fallback
for COOLDOWN_SECONDS. This prevents repeatedly hitting broken models.
"""

import time

COOLDOWN_SECONDS = 15 * 60  # 15 minutes

_cooldowns: dict[str, float] = {}


def mark_failed(provider: str, model_id: str) -> None:
    """Mark a model as failed — exclude from auto for 15 min."""
    _cooldowns[f"{provider}:{model_id}"] = time.monotonic()


def is_available(provider: str, model_id: str) -> bool:
    """Check if a model is available (not in cooldown)."""
    key = f"{provider}:{model_id}"
    if key not in _cooldowns:
        return True
    elapsed = time.monotonic() - _cooldowns[key]
    if elapsed >= COOLDOWN_SECONDS:
        del _cooldowns[key]
        return True
    return False


def filter_available(provider: str, models: list[str]) -> list[str]:
    """Filter out models that are in cooldown."""
    return [m for m in models if is_available(provider, m)]
