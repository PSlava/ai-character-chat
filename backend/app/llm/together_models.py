"""Registry of Together AI models — auto-refreshed from API, quality scores static."""

import logging
import time

logger = logging.getLogger(__name__)

# Static quality scores for known models (higher = better for roleplay)
QUALITY_SCORES: dict[str, int] = {
    "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8": 9,
    "meta-llama/Llama-3.3-70B-Instruct-Turbo": 8,
    "Qwen/Qwen3-32B": 7,
    "meta-llama/Llama-4-Scout-17B-16E-Instruct": 7,
    "deepseek-ai/DeepSeek-R1": 6,
    "deepseek-ai/DeepSeek-V3": 6,
    "mistralai/Mistral-Small-24B-Instruct-2501": 5,
}

# Together AI does not block NSFW at API level
NSFW_BLOCKED: set[str] = set()

# Models to exclude (not useful for chat)
EXCLUDE_PREFIXES = (
    "meta-llama/Llama-Guard",
    "meta-llama/Llama-Prompt-Guard",
    "togethercomputer/",
)
EXCLUDE_IDS: set[str] = set()

# Only include these model types from API (skip embedding, image, etc.)
INCLUDE_TYPES = {"chat", "language"}

# Min quality to include in auto-fallback
MIN_QUALITY_FOR_FALLBACK = 6

# Cache
_cached_models: list[dict] = []
_cache_time: float = 0
CACHE_TTL = 3600  # 1 hour

# Fallback if API unavailable
FALLBACK_MODELS = [
    {"id": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8", "name": "Llama 4 Maverick", "quality": 9, "nsfw": True, "note": ""},
    {"id": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "name": "Llama 3.3 70B Turbo", "quality": 8, "nsfw": True, "note": ""},
    {"id": "Qwen/Qwen3-32B", "name": "Qwen 3 32B", "quality": 7, "nsfw": True, "note": ""},
    {"id": "meta-llama/Llama-4-Scout-17B-16E-Instruct", "name": "Llama 4 Scout", "quality": 7, "nsfw": True, "note": ""},
    {"id": "deepseek-ai/DeepSeek-V3", "name": "DeepSeek V3", "quality": 6, "nsfw": True, "note": ""},
]


def _should_include(model_id: str) -> bool:
    """Filter out non-chat models."""
    for prefix in EXCLUDE_PREFIXES:
        if model_id.startswith(prefix):
            return False
    return model_id not in EXCLUDE_IDS


def _build_model_entry(model_id: str, owned_by: str = "") -> dict:
    quality = QUALITY_SCORES.get(model_id, 5)
    # Pretty name: "meta-llama/Llama-3.3-70B-Instruct-Turbo" → "Llama 3.3 70B Instruct Turbo"
    short = model_id.split("/")[-1] if "/" in model_id else model_id
    name = short.replace("-", " ").title()
    return {"id": model_id, "name": name, "quality": quality, "nsfw": model_id not in NSFW_BLOCKED, "note": owned_by}


async def refresh_models(client) -> list[dict]:
    """Fetch models from Together API and update cache."""
    global _cached_models, _cache_time
    try:
        response = await client.models.list()
        models = []
        for m in response.data:
            model_type = getattr(m, "type", None) or ""
            if model_type and model_type not in INCLUDE_TYPES:
                continue
            if _should_include(m.id):
                models.append(_build_model_entry(m.id, getattr(m, "owned_by", "")))
        if models:
            models.sort(key=lambda x: x["quality"], reverse=True)
            _cached_models = models
            _cache_time = time.monotonic()
            logger.info(f"Together models refreshed: {[m['id'] for m in models[:10]]}...")
    except Exception as e:
        logger.warning(f"Failed to refresh Together models: {e}")
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
