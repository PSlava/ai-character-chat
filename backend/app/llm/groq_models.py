"""Registry of Groq models with quality scores."""

GROQ_MODELS = [
    {
        "id": "llama-3.3-70b-versatile",
        "name": "Llama 3.3 70B",
        "quality": 9,
        "note": "большая, универсальная",
    },
    {
        "id": "qwen-qwq-32b",
        "name": "Qwen QwQ 32B",
        "quality": 8,
        "note": "reasoning-модель",
    },
    {
        "id": "openai/gpt-oss-120b",
        "name": "GPT-OSS 120B",
        "quality": 8,
        "note": "OpenAI open-source, 120B",
    },
    {
        "id": "meta-llama/llama-4-scout-17b-16e-instruct",
        "name": "Llama 4 Scout",
        "quality": 7,
        "note": "MoE, быстрая",
    },
    {
        "id": "deepseek-r1-distill-llama-70b",
        "name": "DeepSeek R1 Distill 70B",
        "quality": 7,
        "note": "reasoning-модель",
    },
    {
        "id": "llama-3.1-8b-instant",
        "name": "Llama 3.1 8B",
        "quality": 5,
        "note": "маленькая, очень быстрая",
    },
]


def get_models_sorted() -> list[dict]:
    return sorted(GROQ_MODELS, key=lambda m: m["quality"], reverse=True)


def get_fallback_models(limit: int = 3) -> list[str]:
    """Return top-N model IDs for auto-fallback."""
    return [m["id"] for m in get_models_sorted()[:limit]]


def find_model_by_id(model_id: str) -> dict | None:
    for m in GROQ_MODELS:
        if m["id"] == model_id:
            return m
    return None
