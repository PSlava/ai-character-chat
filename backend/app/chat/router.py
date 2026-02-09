import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.auth.middleware import get_current_user
from app.db.session import get_db
from app.chat.schemas import CreateChatRequest, SendMessageRequest
from app.chat import service
from app.db.models import User
from app.llm.base import LLMConfig
from app.llm.registry import get_provider
from app.config import settings

router = APIRouter(prefix="/api/chats", tags=["chat"])


def message_to_dict(m):
    return {
        "id": m.id,
        "chat_id": m.chat_id,
        "role": m.role.value if hasattr(m.role, 'value') else m.role,
        "content": m.content,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def chat_to_dict(c):
    d = {
        "id": c.id,
        "user_id": c.user_id,
        "character_id": c.character_id,
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
        }
    return d


@router.post("", status_code=201)
async def create_chat(
    body: CreateChatRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat, character = await service.create_chat(db, user["id"], body.character_id, body.model)
    if not chat:
        raise HTTPException(status_code=404, detail="Character not found")

    messages = await service.get_chat_messages(db, chat.id)
    return {
        "chat": chat_to_dict(chat),
        "messages": [message_to_dict(m) for m in messages],
    }


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
    messages = await service.get_chat_messages(db, chat_id)
    return {
        "chat": chat_to_dict(chat),
        "messages": [message_to_dict(m) for m in messages],
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
    chat = await service.get_chat(db, chat_id, user["id"])
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    character = chat.character

    # If model override requested, persist it on the chat
    if body.model and body.model != chat.model_used:
        chat.model_used = body.model
        await db.commit()

    model_name = chat.model_used or settings.default_model

    # Save user message
    await service.save_message(db, chat_id, "user", body.content)

    # Get user display name for system prompt
    user_result = await db.execute(select(User).where(User.id == user["id"]))
    user_obj = user_result.scalar_one_or_none()
    user_name = user_obj.display_name if user_obj else None

    # Build context
    messages = await service.build_conversation_messages(db, chat_id, character, user_name=user_name)

    # Resolve provider and model ID
    PROVIDER_MODELS = {
        "claude": "claude-sonnet-4-5-20250929",
        "openai": "gpt-4o",
        "gemini": "gemini-2.0-flash",
        "deepseek": "deepseek-chat",
        "qwen": "qwen3-32b",
    }
    if "/" in model_name:
        provider_name = "openrouter"
        model_id = model_name
    elif model_name in ("openrouter", "qwen3"):
        provider_name = "openrouter"
        model_id = ""
    else:
        provider_name = model_name
        model_id = PROVIDER_MODELS.get(model_name, "")

    provider = get_provider(provider_name)
    config = LLMConfig(
        model=model_id,
        temperature=body.temperature if body.temperature is not None else 0.8,
        max_tokens=body.max_tokens if body.max_tokens is not None else 2048,
        top_p=body.top_p if body.top_p is not None else 0.95,
        top_k=body.top_k if body.top_k is not None else 0,
        frequency_penalty=body.frequency_penalty if body.frequency_penalty is not None else 0.0,
    )

    async def event_stream():
        full_response = []
        try:
            async for chunk in provider.generate_stream(messages, config):
                full_response.append(chunk)
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

            complete_text = "".join(full_response)
            saved_msg = await service.save_message(db, chat_id, "assistant", complete_text)
            yield f"data: {json.dumps({'type': 'done', 'message_id': saved_msg.id})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
