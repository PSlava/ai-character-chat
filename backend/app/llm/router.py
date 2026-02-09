from fastapi import APIRouter
from app.llm.openrouter_models import get_models_sorted as get_or_models
from app.llm.groq_models import get_models_sorted as get_groq_models
from app.llm.cerebras_models import get_models_sorted as get_cerebras_models

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/openrouter")
async def list_openrouter_models():
    return get_or_models()


@router.get("/groq")
async def list_groq_models():
    return get_groq_models()


@router.get("/cerebras")
async def list_cerebras_models():
    return get_cerebras_models()
