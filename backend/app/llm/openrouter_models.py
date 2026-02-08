"""Registry of free OpenRouter models with quality scores.

Quality reflects both capability AND reliability.
Models with unstable providers get lower scores.
"""

OPENROUTER_FREE_MODELS = [
    {
        "id": "google/gemma-3-27b-it:free",
        "name": "Gemma 3 27B",
        "quality": 9,
        "note": "стабильная, Google AI Studio",
    },
    {
        "id": "google/gemma-3-12b-it:free",
        "name": "Gemma 3 12B",
        "quality": 8,
        "note": "стабильная, быстрая",
    },
    {
        "id": "nvidia/nemotron-nano-9b-v2:free",
        "name": "Nemotron 9B",
        "quality": 7,
        "note": "быстрая, thinking-модель",
    },
    {
        "id": "deepseek/deepseek-r1-0528:free",
        "name": "DeepSeek R1",
        "quality": 7,
        "note": "умная, но медленная (>30с)",
    },
    {
        "id": "nousresearch/hermes-3-llama-3.1-405b:free",
        "name": "Hermes 3 405B",
        "quality": 6,
        "note": "Venice провайдер нестабилен",
    },
    {
        "id": "meta-llama/llama-3.3-70b-instruct:free",
        "name": "Llama 3.3 70B",
        "quality": 6,
        "note": "Venice провайдер нестабилен",
    },
    {
        "id": "qwen/qwen3-4b:free",
        "name": "Qwen3 4B",
        "quality": 5,
        "note": "маленькая, Venice нестабилен",
    },
    {
        "id": "meta-llama/llama-3.2-3b-instruct:free",
        "name": "Llama 3.2 3B",
        "quality": 4,
        "note": "маленькая, Venice нестабилен",
    },
]


def get_models_sorted() -> list[dict]:
    """Return models sorted by quality descending."""
    return sorted(OPENROUTER_FREE_MODELS, key=lambda m: m["quality"], reverse=True)


def get_fallback_models(limit: int = 3) -> list[str]:
    """Return top-N model IDs sorted by quality for fallback chain."""
    return [m["id"] for m in get_models_sorted()[:limit]]


def find_model_by_id(model_id: str) -> dict | None:
    """Find model info by ID."""
    for m in OPENROUTER_FREE_MODELS:
        if m["id"] == model_id:
            return m
    return None
