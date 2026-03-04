"""Auto-resolve model 404s: detect renamed models, find replacement, persist override."""

import asyncio
import logging
import re
import time

from sqlalchemy import text

from app.db.session import engine as db_engine
from app.config import settings

logger = logging.getLogger("llm.model_resolver")

# Single source of truth for default models per provider
DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o",
    "gemini": "gemini-3.0-flash",
    "deepseek": "deepseek-chat",
    "qwen": "qwen3-235b-a22b",
    "claude": "claude-sonnet-4-6",
    "haiku": "claude-haiku-4-5-20251001",
    "grok": "grok-4-1-fast-non-reasoning",
    "mistral": "mistral-medium-latest",
}

# Providers where we can auto-fix (have AsyncOpenAI client with models.list())
FIXABLE_PROVIDERS = {"grok", "mistral", "deepseek", "openai"}
# Note: qwen uses DashScope which may not support models.list() reliably

# In-memory overrides: {provider: new_model_id}
_overrides: dict[str, str] = {}

# Dedup: don't re-resolve same provider within 10 minutes
_resolve_timestamps: dict[str, float] = {}
_RESOLVE_COOLDOWN = 600  # seconds

# Per-provider locks to prevent concurrent resolve attempts
_resolve_locks: dict[str, asyncio.Lock] = {}

# Strong references to background tasks (prevent GC before completion)
_background_tasks: set[asyncio.Task] = set()

DB_KEY_PREFIX = "model_override."


def get_model(provider: str) -> str:
    """Get the current model ID for a provider (override or default)."""
    return _overrides.get(provider) or DEFAULT_MODELS.get(provider, "")


def is_404_error(e: Exception) -> bool:
    """Check if an exception indicates a model-not-found (404) error."""
    # All FIXABLE_PROVIDERS use OpenAI SDK — check status_code directly
    status = getattr(e, "status_code", None)
    if status == 404:
        return True
    # Fallback: string check for wrapped exceptions, scoped to model context
    err = str(e).lower()
    if "model" in err and ("not found" in err or "does not exist" in err or "not_found" in err):
        return True
    return False


async def resolve_model_404(provider: str, old_model: str) -> str | None:
    """Attempt to find a replacement model after a 404. Returns new model ID or None."""
    now = time.time()
    last = _resolve_timestamps.get(provider, 0)
    if now - last < _RESOLVE_COOLDOWN:
        logger.debug("Skipping resolve for %s (cooldown)", provider)
        return _overrides.get(provider)

    # Per-provider lock prevents duplicate resolve from concurrent requests
    lock = _resolve_locks.get(provider)
    if not lock:
        lock = asyncio.Lock()
        _resolve_locks[provider] = lock

    async with lock:
        # Re-check cooldown after acquiring lock (another request may have resolved)
        now = time.time()
        last = _resolve_timestamps.get(provider, 0)
        if now - last < _RESOLVE_COOLDOWN:
            return _overrides.get(provider)

        logger.info("Resolving 404 for %s (old model: %s)", provider, old_model)

        available = await _fetch_models(provider)
        if not available:
            logger.warning("Could not fetch model list for %s", provider)
            return None

        new_model = _find_best_match(old_model, available)
        if not new_model:
            logger.warning("No suitable replacement found for %s/%s", provider, old_model)
            return None

        # Set cooldown only on success — transient failures won't block retries
        _resolve_timestamps[provider] = now
        logger.info("Auto-fix: %s model %s -> %s", provider, old_model, new_model)
        _overrides[provider] = new_model
        await _save_to_db(provider, new_model)
        task = asyncio.create_task(_send_alert(provider, old_model, new_model))
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)
        return new_model


def _find_best_match(old_model: str, available: list[str]) -> str | None:
    """Find the best matching model from available list based on token overlap."""
    if not available:
        return None

    old_tokens = set(_tokenize(old_model))
    if not old_tokens:
        return None

    # Negative keywords: reduce score for non-chat models
    _NEGATIVE_TOKENS = {"embedding", "image", "video", "audio", "vision", "tts", "whisper", "moderation"}
    # Positive substrings: boost for chat-oriented models (checked against full name)
    _POSITIVE_SUBSTRINGS = ["chat", "instruct", "non-reasoning"]
    # Penalty substrings: models with "reasoning" but NOT "non-reasoning"
    _PENALTY_SUBSTRINGS = ["reasoning"]

    scored: list[tuple[float, str]] = []
    for candidate in available:
        cand_tokens = set(_tokenize(candidate))
        cand_lower = candidate.lower()

        # Skip clearly wrong models
        if cand_tokens & _NEGATIVE_TOKENS:
            continue

        overlap = len(old_tokens & cand_tokens)
        if overlap == 0:
            continue

        score = overlap / max(len(old_tokens), 1)

        # Boost for positive substrings
        for pos in _POSITIVE_SUBSTRINGS:
            if pos in cand_lower:
                score += 0.3

        # Penalize reasoning models (but not non-reasoning)
        for pen in _PENALTY_SUBSTRINGS:
            if pen in cand_lower and f"non-{pen}" not in cand_lower:
                score -= 0.5

        # Slight penalty for longer names (prefer simpler models)
        score -= len(cand_tokens) * 0.01

        scored.append((score, candidate))

    if not scored:
        return None

    scored.sort(key=lambda x: (-x[0], len(x[1])))
    return scored[0][1]


def _tokenize(model_id: str) -> list[str]:
    """Split model ID into tokens for comparison."""
    return [t.lower() for t in re.split(r"[-_.\s]+", model_id) if t]


async def _fetch_models(provider: str) -> list[str] | None:
    """Fetch model list from provider via OpenAI-compatible API."""
    # Access _providers directly to bypass blacklist/availability checks —
    # we need to fetch model list even if provider is temporarily blocked
    from app.llm.registry import _providers

    prov = _providers.get(provider)
    if not prov:
        return None

    client = getattr(prov, "client", None)
    if not client or not hasattr(client, "models"):
        return None

    try:
        response = await client.models.list()
        return [m.id for m in response.data]
    except Exception as e:
        logger.warning("Failed to fetch models for %s: %s", provider, e)
        return None


async def load_from_db():
    """Load persisted model overrides from DB on startup."""
    try:
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT key, value FROM prompt_templates WHERE key LIKE :prefix"),
                {"prefix": f"{DB_KEY_PREFIX}%"},
            )
            for row in result:
                provider = row[0][len(DB_KEY_PREFIX):]
                _overrides[provider] = row[1]
                logger.info("Loaded model override: %s -> %s", provider, row[1])
    except Exception as e:
        logger.warning("Failed to load model overrides from DB: %s", e)


async def _save_to_db(provider: str, new_model: str):
    """Persist model override to DB."""
    try:
        async with db_engine.begin() as conn:
            await conn.execute(
                text("""
                    INSERT INTO prompt_templates (key, value, updated_at)
                    VALUES (:k, :v, NOW())
                    ON CONFLICT (key) DO UPDATE SET value = :v, updated_at = NOW()
                """),
                {"k": f"{DB_KEY_PREFIX}{provider}", "v": new_model},
            )
    except Exception as e:
        logger.warning("Failed to save model override for %s: %s", provider, e)


async def _send_alert(provider: str, old_model: str, new_model: str):
    """Notify admins about auto-fixed model rename."""
    admin_str = settings.admin_emails
    if not admin_str:
        return

    admin_list = [e.strip() for e in admin_str.split(",") if e.strip()]
    if not admin_list:
        return

    from app.utils.email import _get_provider as _get_email_provider, _send_via_resend, _send_via_smtp

    email_provider = _get_email_provider()
    if email_provider == "console":
        logger.info("MODEL AUTO-FIX: %s: %s -> %s", provider, old_model, new_model)
        return

    site = settings.site_name
    subject = f"{site} -- {provider.upper()} model auto-fixed"
    body = (
        f"Model 404 detected and auto-fixed on {site}.\n\n"
        f"  Provider:  {provider}\n"
        f"  Old model: {old_model}\n"
        f"  New model: {new_model}\n\n"
        f"The override is stored in DB and will persist across restarts.\n"
        f"To revert, delete the prompt_templates row with key '{DB_KEY_PREFIX}{provider}'.\n\n"
        f"Consider updating DEFAULT_MODELS in model_resolver.py to make this permanent.\n\n"
        f"-- {site} Model Resolver\n"
    )

    for email in admin_list:
        try:
            if email_provider == "resend":
                await _send_via_resend(email, subject, body)
            else:
                await _send_via_smtp(email, subject, body)
        except Exception:
            logger.exception("Failed to send model auto-fix alert to %s", email)
