"""Registry of Cerebras models with quality scores."""

CEREBRAS_MODELS = [
    {
        "id": "qwen-3-235b-a22b-instruct-2507",
        "name": "Qwen 3 235B",
        "quality": 9,
        "note": "самая большая, ~1400 t/s",
    },
    {
        "id": "gpt-oss-120b",
        "name": "GPT-OSS 120B",
        "quality": 8,
        "note": "OpenAI open-source, ~3000 t/s",
    },
    {
        "id": "llama3.1-8b",
        "name": "Llama 3.1 8B",
        "quality": 5,
        "note": "маленькая, ~2200 t/s",
    },
]


def get_models_sorted() -> list[dict]:
    return sorted(CEREBRAS_MODELS, key=lambda m: m["quality"], reverse=True)


def get_fallback_models(limit: int = 3) -> list[str]:
    """Return top-N model IDs for auto-fallback."""
    return [m["id"] for m in get_models_sorted()[:limit]]


def find_model_by_id(model_id: str) -> dict | None:
    for m in CEREBRAS_MODELS:
        if m["id"] == model_id:
            return m
    return None
