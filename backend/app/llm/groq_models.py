"""Registry of Groq models — auto-refreshed from API, quality scores static."""

import asyncio
import logging
import time

logger = logging.getLogger(__name__)

# Static quality scores for known models (higher = better for roleplay)
QUALITY_SCORES: dict[str, int] = {
    "openai/gpt-oss-120b": 9,
    "llama-3.3-70b-versatile": 8,
    "openai/gpt-oss-20b": 6,
    "qwen/qwen3-32b": 8,
    "meta-llama/llama-4-scout-17b-16e-instruct": 7,
    "meta-llama/llama-4-maverick-17b-128e-instruct": 7,
    "deepseek-r1-distill-llama-70b": 7,
}

# Models to exclude (not useful for chat)
EXCLUDE_PREFIXES = ("whisper", "meta-llama/llama-guard", "meta-llama/llama-prompt-guard")
EXCLUDE_IDS = {"groq/compound", "groq/compound-mini", "openai/gpt-oss-safeguard-20b"}

# Min quality to include in auto-fallback (skip 8B and similar tiny models)
MIN_QUALITY_FOR_FALLBACK = 6

# Cache
_cached_models: list[dict] = []
_cache_time: float = 0
CACHE_TTL = 3600  # 1 hour

# Fallback if API unavailable
FALLBACK_MODELS = [
    {"id": "openai/gpt-oss-120b", "name": "GPT-OSS 120B", "quality": 9, "note": ""},
    {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B", "quality": 8, "note": ""},
    {"id": "openai/gpt-oss-20b", "name": "GPT-OSS 20B", "quality": 6, "note": ""},
]


def _should_include(model_id: str) -> bool:
    """Filter out non-chat models."""
    for prefix in EXCLUDE_PREFIXES:
        if model_id.startswith(prefix):
            return False
    return model_id not in EXCLUDE_IDS


def _build_model_entry(model_id: str, owned_by: str = "") -> dict:
    quality = QUALITY_SCORES.get(model_id, 5)
    # Pretty name: "openai/gpt-oss-120b" → "GPT-OSS 120B"
    short = model_id.split("/")[-1] if "/" in model_id else model_id
    name = short.replace("-", " ").title()
    return {"id": model_id, "name": name, "quality": quality, "note": owned_by}


async def refresh_models(client) -> list[dict]:
    """Fetch models from Groq API and update cache."""
    global _cached_models, _cache_time
    try:
        response = await client.models.list()
        models = []
        for m in response.data:
            if _should_include(m.id):
                models.append(_build_model_entry(m.id, getattr(m, "owned_by", "")))
        if models:
            models.sort(key=lambda x: x["quality"], reverse=True)
            _cached_models = models
            _cache_time = time.monotonic()
            logger.info(f"Groq models refreshed: {[m['id'] for m in models]}")
    except Exception as e:
        logger.warning(f"Failed to refresh Groq models: {e}")
    return _cached_models


def get_models_sorted() -> list[dict]:
    return _cached_models if _cached_models else FALLBACK_MODELS


def get_fallback_models(limit: int = 3) -> list[str]:
    """Return top-N model IDs for auto-fallback (quality >= MIN_QUALITY_FOR_FALLBACK)."""
    models = get_models_sorted()
    good = [m["id"] for m in models if m["quality"] >= MIN_QUALITY_FOR_FALLBACK]
    return good[:limit] if good else [models[0]["id"]]


def find_model_by_id(model_id: str) -> dict | None:
    for m in get_models_sorted():
        if m["id"] == model_id:
            return m
    return None


def is_cache_stale() -> bool:
    return not _cached_models or (time.monotonic() - _cache_time) > CACHE_TTL
