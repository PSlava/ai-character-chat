"""Shared provider order for all autonomous tasks.

PAID ONLY — quality matters for character generation, highlights, relationships.
Together (Llama, no NSFW moderation) preferred for NSFW content.
Free providers excluded — if all paid fail, admin is notified.
"""

from app.config import settings


def get_autonomous_provider_order() -> tuple[str, ...]:
    """Return provider order from AUTONOMOUS_PROVIDER_ORDER env var.

    Default: together,openai,claude,deepseek (paid only, NSFW-friendly first).
    """
    return tuple(
        p.strip() for p in settings.autonomous_provider_order.split(",") if p.strip()
    )
