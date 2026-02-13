import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from starlette.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.auth.middleware import get_current_user
from app.db.session import get_db
from app.chat.schemas import CreateChatRequest, SendMessageRequest
from app.chat import service
from app.db.models import User, Persona
from app.llm.base import LLMConfig
from app.llm.registry import get_provider
from app.config import settings
from app.auth.rate_limit import check_message_rate

router = APIRouter(prefix="/api/chats", tags=["chat"])

_GENERIC_ERROR_RU = "Ошибка генерации ответа. Попробуйте позже."
_MODERATION_KEYWORDS = ("data_inspection_failed", "content_policy", "content_filter", "moderation", "safety system")


def _is_moderation_error(err: str) -> bool:
    low = err.lower()
    return any(kw in low for kw in _MODERATION_KEYWORDS)


def _user_error(err: str, is_admin: bool) -> str:
    if is_admin or _is_moderation_error(err):
        return err
    return _GENERIC_ERROR_RU


def message_to_dict(m):
    return {
        "id": m.id,
        "chat_id": m.chat_id,
        "role": m.role.value if hasattr(m.role, 'value') else m.role,
        "content": m.content,
        "model_used": m.model_used,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def chat_to_dict(c):
    d = {
        "id": c.id,
        "user_id": c.user_id,
        "character_id": c.character_id,
        "persona_id": getattr(c, 'persona_id', None),
        "title": c.title,
        "model_used": c.model_used,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }
    if c.character:
        d["characters"] = {
            "id": c.character.id,
            "name": c.character.name,
            "avatar_url": c.character.avatar_url,
            "tagline": c.character.tagline,
            "content_rating": c.character.content_rating.value if c.character.content_rating else "sfw",
        }
    return d


@router.post("")
async def create_chat(
    body: CreateChatRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat, character, created = await service.get_or_create_chat(
        db, user["id"], body.character_id, body.model, persona_id=body.persona_id,
        force_new=body.force_new,
    )
    if not chat:
        raise HTTPException(status_code=404, detail="Character not found")

    msgs, has_more = await service.get_chat_messages(db, chat.id, limit=20)
    return JSONResponse(
        content={
            "chat": chat_to_dict(chat),
            "messages": [message_to_dict(m) for m in msgs],
            "has_more": has_more,
        },
        status_code=201 if created else 200,
    )


@router.get("")
async def list_chats(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chats = await service.list_user_chats(db, user["id"])
    return [chat_to_dict(c) for c in chats]


@router.get("/{chat_id}")
async def get_chat(
    chat_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat = await service.get_chat(db, chat_id, user["id"])
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    msgs, has_more = await service.get_chat_messages(db, chat_id, limit=20)
    return {
        "chat": chat_to_dict(chat),
        "messages": [message_to_dict(m) for m in msgs],
        "has_more": has_more,
    }


@router.delete("/{chat_id}", status_code=204)
async def delete_chat(
    chat_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await service.delete_chat(db, chat_id, user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found")


@router.get("/{chat_id}/messages")
async def get_messages(
    chat_id: str,
    before: str | None = None,
    limit: int = 20,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Load older messages for infinite scroll."""
    chat = await service.get_chat(db, chat_id, user["id"])
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    msgs, has_more = await service.get_chat_messages(db, chat_id, limit=limit, before_id=before)
    return {
        "messages": [message_to_dict(m) for m in msgs],
        "has_more": has_more,
    }


@router.delete("/{chat_id}/messages", status_code=204)
async def clear_messages(
    chat_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Clear all messages except the greeting."""
    cleared = await service.clear_chat_messages(db, chat_id, user["id"])
    if not cleared:
        raise HTTPException(status_code=404, detail="Chat not found")


@router.delete("/{chat_id}/messages/{message_id}", status_code=204)
async def delete_message(
    chat_id: str,
    message_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single message (cannot delete greeting)."""
    deleted = await service.delete_message(db, chat_id, message_id, user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Message not found or cannot be deleted")


@router.post("/{chat_id}/message")
async def send_message(
    chat_id: str,
    body: SendMessageRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    check_message_rate(user["id"])

    chat = await service.get_chat(db, chat_id, user["id"])
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    character = chat.character

    # If model override requested, persist it on the chat
    if body.model and body.model != chat.model_used:
        chat.model_used = body.model
        await db.commit()

    model_name = chat.model_used or settings.default_model
    content_rating = character.content_rating.value if character.content_rating else "sfw"

    # Save user message
    user_msg = await service.save_message(db, chat_id, "user", body.content)

    # Get user display name and language for system prompt
    user_result = await db.execute(select(User).where(User.id == user["id"]))
    user_obj = user_result.scalar_one_or_none()
    language = body.language or (user_obj.language if user_obj else None) or "ru"

    # Load persona if attached to chat
    user_name = user_obj.display_name if user_obj else None
    user_description = None
    if chat.persona_id:
        persona_result = await db.execute(select(Persona).where(Persona.id == chat.persona_id))
        persona_obj = persona_result.scalar_one_or_none()
        if persona_obj:
            user_name = persona_obj.name
            user_description = persona_obj.description

    # Build context
    messages = await service.build_conversation_messages(
        db, chat_id, character, user_name=user_name, user_description=user_description,
        language=language, context_limit=body.context_limit,
    )

    # Resolve provider and model ID
    PROVIDER_MODELS = {
        "claude": "claude-sonnet-4-5-20250929",
        "openai": "gpt-4o",
        "gemini": "gemini-2.0-flash",
        "deepseek": "deepseek-chat",
        "qwen": "qwen3-32b",
    }
    is_auto = model_name == "auto"

    if is_auto:
        provider_name = "auto"
        model_id = ""
    elif model_name.startswith("groq:"):
        provider_name = "groq"
        model_id = model_name[5:]
    elif model_name.startswith("cerebras:"):
        provider_name = "cerebras"
        model_id = model_name[9:]
    elif model_name.startswith("together:"):
        provider_name = "together"
        model_id = model_name[9:]
    elif "/" in model_name:
        provider_name = "openrouter"
        model_id = model_name
    elif model_name in ("openrouter",):
        provider_name = "openrouter"
        model_id = ""
    elif model_name in ("groq",):
        provider_name = "groq"
        model_id = ""
    elif model_name in ("cerebras",):
        provider_name = "cerebras"
        model_id = ""
    elif model_name in ("together",):
        provider_name = "together"
        model_id = ""
    else:
        provider_name = model_name
        model_id = PROVIDER_MODELS.get(model_name, "")

    base_config = {
        "temperature": body.temperature if body.temperature is not None else 0.7,
        "max_tokens": body.max_tokens if body.max_tokens is not None else (getattr(character, 'max_tokens', None) or 2048),
        "top_p": body.top_p if body.top_p is not None else 0.95,
        "top_k": body.top_k if body.top_k is not None else 0,
        "frequency_penalty": body.frequency_penalty if body.frequency_penalty is not None else 0.0,
        "presence_penalty": body.presence_penalty if body.presence_penalty is not None else 0.3,
        "content_rating": content_rating,
    }

    is_admin = user.get("role") == "admin"

    if is_auto:
        auto_order = [p.strip() for p in settings.auto_provider_order.split(",") if p.strip()]

        async def event_stream():
            errors: list[str] = []
            for pname in auto_order:
                try:
                    prov = get_provider(pname)
                except ValueError:
                    continue  # provider not configured
                config = LLMConfig(model="", **base_config)
                full_response: list[str] = []
                try:
                    async for chunk in prov.generate_stream(messages, config):
                        full_response.append(chunk)
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
                    complete_text = "".join(full_response)
                    actual_model = f"{pname}:{getattr(prov, 'last_model_used', '') or ''}"
                    saved_msg = await service.save_message(db, chat_id, "assistant", complete_text, model_used=actual_model)
                    if not body.is_regenerate:
                        await service.increment_message_count(character.id, language, user["id"])
                    yield f"data: {json.dumps({'type': 'done', 'message_id': saved_msg.id, 'user_message_id': user_msg.id, 'model_used': actual_model})}\n\n"
                    return
                except Exception as e:
                    errors.append(f"{pname}: {e}")
                    continue
            full_err = 'Все провайдеры недоступны:\n' + '\n'.join(errors)
            yield f"data: {json.dumps({'type': 'error', 'content': _user_error(full_err, is_admin), 'user_message_id': user_msg.id})}\n\n"
    else:
        provider = get_provider(provider_name)
        config = LLMConfig(model=model_id, **base_config)

        async def event_stream():
            full_response = []
            try:
                async for chunk in provider.generate_stream(messages, config):
                    full_response.append(chunk)
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

                complete_text = "".join(full_response)
                actual_model = f"{provider_name}:{getattr(provider, 'last_model_used', model_id) or model_id}"
                saved_msg = await service.save_message(db, chat_id, "assistant", complete_text, model_used=actual_model)
                if not body.is_regenerate:
                    await service.increment_message_count(character.id, language, user["id"])
                yield f"data: {json.dumps({'type': 'done', 'message_id': saved_msg.id, 'user_message_id': user_msg.id, 'model_used': actual_model})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': _user_error(str(e), is_admin), 'user_message_id': user_msg.id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
