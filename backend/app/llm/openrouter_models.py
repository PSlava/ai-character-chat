"""Registry of free OpenRouter models with quality scores.

Quality reflects both capability AND reliability.
Models with unstable providers get lower scores.
"""

OPENROUTER_FREE_MODELS = [
    {
        "id": "google/gemma-3-27b-it:free",
        "name": "Gemma 3 27B",
        "quality": 9,
        "nsfw": False,  # Google safety filters block NSFW
        "note": "стабильная, Google AI Studio",
    },
    {
        "id": "google/gemma-3-12b-it:free",
        "name": "Gemma 3 12B",
        "quality": 8,
        "nsfw": False,  # Google safety filters block NSFW
        "note": "стабильная, быстрая",
    },
    {
        "id": "nvidia/nemotron-nano-9b-v2:free",
        "name": "Nemotron 9B",
        "quality": 7,
        "nsfw": True,
        "note": "быстрая, thinking-модель",
    },
    {
        "id": "deepseek/deepseek-r1-0528:free",
        "name": "DeepSeek R1",
        "quality": 7,
        "nsfw": False,  # DeepSeek has content moderation
        "note": "умная, но медленная (>30с)",
    },
    {
        "id": "nousresearch/hermes-3-llama-3.1-405b:free",
        "name": "Hermes 3 405B",
        "quality": 6,
        "nsfw": True,
        "note": "Venice провайдер нестабилен",
    },
    {
        "id": "meta-llama/llama-3.3-70b-instruct:free",
        "name": "Llama 3.3 70B",
        "quality": 6,
        "nsfw": True,
        "note": "Venice провайдер нестабилен",
    },
    {
        "id": "qwen/qwen3-4b:free",
        "name": "Qwen3 4B",
        "quality": 5,
        "nsfw": True,
        "note": "маленькая, Venice нестабилен",
    },
    {
        "id": "meta-llama/llama-3.2-3b-instruct:free",
        "name": "Llama 3.2 3B",
        "quality": 4,
        "nsfw": True,
        "note": "маленькая, Venice нестабилен",
    },
]


def get_models_sorted() -> list[dict]:
    """Return models sorted by quality descending."""
    return sorted(OPENROUTER_FREE_MODELS, key=lambda m: m["quality"], reverse=True)


def get_fallback_models(limit: int = 3, nsfw: bool = False) -> list[str]:
    """Return top-N model IDs, diversified by provider to avoid shared rate limits.

    Google AI Studio models share a rate limit, so we pick one Google model
    then fill remaining slots from other providers before adding more Google models.

    If nsfw=True, exclude models that can't handle NSFW content.
    """
    sorted_models = get_models_sorted()
    if nsfw:
        sorted_models = [m for m in sorted_models if m.get("nsfw", True)]
    result: list[str] = []
    seen_providers: set[str] = set()

    # First pass: best model from each provider
    for m in sorted_models:
        provider = m["id"].split("/")[0]  # google, nvidia, deepseek, etc.
        if provider not in seen_providers:
            result.append(m["id"])
            seen_providers.add(provider)
            if len(result) >= limit:
                return result

    # Second pass: fill remaining with best available
    for m in sorted_models:
        if m["id"] not in result:
            result.append(m["id"])
            if len(result) >= limit:
                return result

    return result


def find_model_by_id(model_id: str) -> dict | None:
    """Find model info by ID."""
    for m in OPENROUTER_FREE_MODELS:
        if m["id"] == model_id:
            return m
    return None
