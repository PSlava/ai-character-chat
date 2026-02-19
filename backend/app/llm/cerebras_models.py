"""Registry of Cerebras models — auto-refreshed from API, quality scores static."""

import logging
import time

logger = logging.getLogger(__name__)

# Static quality scores for known models (higher = better for roleplay)
# Llama/Qwen preferred — GPT-OSS has strict content moderation
# NOTE: Cerebras API does NOT support frequency_penalty / presence_penalty,
# so repetition control is limited. Scores lowered vs Groq equivalents.
QUALITY_SCORES: dict[str, int] = {
    "qwen-3-235b-a22b-instruct-2507": 8,
    "zai-glm-4.7": 6,
    "gpt-oss-120b": 5,
}

# Models that refuse NSFW content (strict content moderation)
NSFW_BLOCKED: set[str] = {"gpt-oss-120b"}

# Models to exclude (too small for roleplay)
EXCLUDE_IDS = {"llama3.1-8b"}

# Min quality to include in auto-fallback
MIN_QUALITY_FOR_FALLBACK = 6

# Cache
_cached_models: list[dict] = []
_cache_time: float = 0
CACHE_TTL = 3600  # 1 hour

# Fallback if API unavailable
FALLBACK_MODELS = [
    {"id": "qwen-3-235b-a22b-instruct-2507", "name": "Qwen 3 235B A22B", "quality": 8, "nsfw": True, "note": "no penalty support"},
    {"id": "zai-glm-4.7", "name": "ZAI GLM 4.7", "quality": 6, "nsfw": True, "note": "no penalty support"},
    {"id": "gpt-oss-120b", "name": "GPT-OSS 120B", "quality": 5, "nsfw": False, "note": "no penalty support"},
]


def _build_model_entry(model_id: str, owned_by: str = "") -> dict:
    quality = QUALITY_SCORES.get(model_id, 5)
    name = model_id.replace("-", " ").title()
    return {"id": model_id, "name": name, "quality": quality, "nsfw": model_id not in NSFW_BLOCKED, "note": owned_by}


async def refresh_models(client) -> list[dict]:
    """Fetch models from Cerebras API and update cache."""
    global _cached_models, _cache_time
    try:
        response = await client.models.list()
        models = []
        for m in response.data:
            if m.id not in EXCLUDE_IDS:
                models.append(_build_model_entry(m.id, getattr(m, "owned_by", "")))
        if models:
            models.sort(key=lambda x: x["quality"], reverse=True)
            _cached_models = models
            _cache_time = time.monotonic()
            logger.info(f"Cerebras models refreshed: {[m['id'] for m in models]}")
    except Exception as e:
        logger.warning(f"Failed to refresh Cerebras models: {e}")
    return _cached_models


def get_models_sorted() -> list[dict]:
    return _cached_models if _cached_models else FALLBACK_MODELS


def get_fallback_models(limit: int = 3, nsfw: bool = False) -> list[str]:
    """Return top-N model IDs for auto-fallback (quality >= MIN_QUALITY_FOR_FALLBACK).

    If nsfw=True, exclude models with strict content moderation.
    """
    models = get_models_sorted()
    good = [m["id"] for m in models if m["quality"] >= MIN_QUALITY_FOR_FALLBACK]
    if nsfw:
        good = [mid for mid in good if mid not in NSFW_BLOCKED]
    return good[:limit] if good else [models[0]["id"]]


def find_model_by_id(model_id: str) -> dict | None:
    for m in get_models_sorted():
        if m["id"] == model_id:
            return m
    return None


def is_cache_stale() -> bool:
    return not _cached_models or (time.monotonic() - _cache_time) > CACHE_TTL
