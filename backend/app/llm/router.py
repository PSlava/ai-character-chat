from fastapi import APIRouter
from app.llm.openrouter_models import get_models_sorted as get_or_models
from app.llm.groq_models import get_models_sorted as get_groq_models, is_cache_stale as groq_stale
from app.llm.cerebras_models import get_models_sorted as get_cerebras_models, is_cache_stale as cerebras_stale
from app.llm.together_models import get_models_sorted as get_together_models, is_cache_stale as together_stale

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/openrouter")
async def list_openrouter_models():
    return get_or_models()


@router.get("/groq")
async def list_groq_models():
    if groq_stale():
        try:
            from app.llm.registry import get_provider
            provider = get_provider("groq")
            await provider.ensure_models_loaded()
        except (ValueError, Exception):
            pass
    return get_groq_models()


@router.get("/cerebras")
async def list_cerebras_models():
    if cerebras_stale():
        try:
            from app.llm.registry import get_provider
            provider = get_provider("cerebras")
            await provider.ensure_models_loaded()
        except (ValueError, Exception):
            pass
    return get_cerebras_models()


@router.get("/together")
async def list_together_models():
    if together_stale():
        try:
            from app.llm.registry import get_provider
            provider = get_provider("together")
            await provider.ensure_models_loaded()
        except (ValueError, Exception):
            pass
    return get_together_models()
