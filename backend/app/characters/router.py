import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.middleware import get_current_user
from app.db.session import get_db
from app.characters.schemas import CharacterCreate, CharacterUpdate, GenerateFromStoryRequest
from app.characters import service
from app.characters.serializers import character_to_dict
from app.llm.base import LLMMessage, LLMConfig
from app.llm.registry import get_provider

router = APIRouter(prefix="/api/characters", tags=["characters"])

GENERATE_SYSTEM_PROMPT = """Ты — эксперт по созданию персонажей для ролевых чатов.
Проанализируй предоставленный текст и создай профиль персонажа в формате JSON.

Верни строго JSON-объект со следующими полями:
{
  "name": "Имя персонажа",
  "tagline": "Краткое описание в 5-10 слов",
  "personality": "Детальное описание характера, манеры речи, привычек, особенностей поведения. Пиши от второго лица: 'Ты — ...'",
  "scenario": "Описание мира, ситуации и контекста для начала диалога",
  "greeting_message": "Первое сообщение персонажа в начале чата. Используй *звёздочки* для описания действий. Сообщение должно быть атмосферным и приглашать к диалогу.",
  "example_dialogues": "2-3 примера коротких реплик в формате:\\nUser: ...\\nCharacter: ...",
  "tags": ["тег1", "тег2", "тег3"],
  "content_rating": "sfw"
}

Правила:
- personality должен быть подробным (минимум 3-4 предложения)
- greeting_message должно быть от лица персонажа, атмосферным
- content_rating: "sfw" для обычного контента, "moderate" если есть насилие/мрачные темы, "nsfw" если явный взрослый контент
- Если указано имя конкретного персонажа — создай профиль для него. Иначе — выбери самого яркого/интересного персонажа из текста.
- Верни ТОЛЬКО JSON, без markdown-обёртки, без пояснений."""


@router.post("/generate-from-story")
async def generate_from_story(
    body: GenerateFromStoryRequest,
    user=Depends(get_current_user),
):
    MODEL_MAP = {
        "openrouter": "google/gemini-2.0-flash-exp:free",
        "qwen3": "qwen/qwen3-next-80b-a3b-instruct:free",
    }
    OPENROUTER_ALIASES = {"qwen3"}
    provider_name = "openrouter" if body.preferred_model in OPENROUTER_ALIASES else body.preferred_model

    try:
        provider = get_provider(provider_name)
    except ValueError:
        raise HTTPException(status_code=400, detail="Model not available")

    user_msg = body.story_text
    if body.character_name:
        user_msg += f"\n\nСоздай профиль для персонажа: {body.character_name}"

    messages = [
        LLMMessage(role="system", content=GENERATE_SYSTEM_PROMPT),
        LLMMessage(role="user", content=user_msg),
    ]
    config = LLMConfig(model=MODEL_MAP.get(body.preferred_model, ""), temperature=0.7, max_tokens=2048)

    try:
        raw = await provider.generate(messages, config)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {str(e)}")

    # Strip markdown code fences if present
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Failed to parse LLM response as JSON")

    return data


@router.get("")
async def browse_characters(
    limit: int = Query(20, le=50),
    offset: int = Query(0, ge=0),
    search: str | None = None,
    tag: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    characters = await service.list_public_characters(db, limit, offset, search, tag)
    return [character_to_dict(c) for c in characters]


@router.get("/my")
async def my_characters(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    characters = await service.list_my_characters(db, user["id"])
    return [character_to_dict(c) for c in characters]


@router.get("/{character_id}")
async def get_character(character_id: str, db: AsyncSession = Depends(get_db)):
    character = await service.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character_to_dict(character)


@router.post("", status_code=201)
async def create_character(
    body: CharacterCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    character = await service.create_character(db, user["id"], body.model_dump())
    return character_to_dict(character)


@router.put("/{character_id}")
async def update_character(
    character_id: str,
    body: CharacterUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await service.update_character(
        db, character_id, user["id"], body.model_dump()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Character not found or not yours")
    return character_to_dict(result)


@router.delete("/{character_id}", status_code=204)
async def delete_character(
    character_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await service.delete_character(db, character_id, user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Character not found or not yours")
