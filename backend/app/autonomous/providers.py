"""Shared provider order for all autonomous tasks."""

from app.config import settings


def get_autonomous_provider_order() -> tuple[str, ...]:
    """Return provider order from AUTONOMOUS_PROVIDER_ORDER env var.

    Default: openai,gemini,deepseek,together,groq,cerebras,openrouter
    Providers that aren't configured will be skipped at call time.
    """
    return tuple(
        p.strip() for p in settings.autonomous_provider_order.split(",") if p.strip()
    )
