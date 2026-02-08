from fastapi import APIRouter
from app.llm.openrouter_models import get_models_sorted

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/openrouter")
async def list_openrouter_models():
    return get_models_sorted()
