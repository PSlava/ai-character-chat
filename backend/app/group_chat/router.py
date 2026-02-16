"""Group chat router: 1 user + 2-5 AI characters."""
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.middleware import get_current_user
from app.db.session import get_db, engine as db_engine
from app.db.models import GroupChat, GroupChatMember, GroupMessage, Character, MessageRole
from app.llm.base import LLMMessage, LLMConfig
from app.llm.registry import get_provider
from app.config import settings
from app.chat.prompt_builder import build_system_prompt
from app.chat.daily_limit import check_daily_limit

router = APIRouter(prefix="/api/group-chats", tags=["group-chat"])

MAX_MEMBERS = 5
MIN_MEMBERS = 2
MAX_CONTEXT_MESSAGES = 30


class CreateGroupChatRequest(BaseModel):
    character_ids: list[str] = Field(min_length=MIN_MEMBERS, max_length=MAX_MEMBERS)
    title: str | None = None


class SendGroupMessageRequest(BaseModel):
    content: str = Field(max_length=20000)
    language: str | None = Field(default=None, max_length=10)


def _member_to_dict(m: GroupChatMember) -> dict:
    return {
        "id": m.id,
        "character_id": m.character_id,
        "position": m.position,
        "character": {
            "id": m.character.id,
            "name": m.character.name,
            "avatar_url": m.character.avatar_url,
            "tagline": m.character.tagline,
        } if m.character else None,
    }


def _message_to_dict(m: GroupMessage) -> dict:
    return {
        "id": m.id,
        "group_chat_id": m.group_chat_id,
        "character_id": m.character_id,
        "role": m.role.value if hasattr(m.role, 'value') else m.role,
        "content": m.content,
        "model_used": m.model_used,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def _chat_to_dict(gc: GroupChat) -> dict:
    return {
        "id": gc.id,
        "user_id": gc.user_id,
        "title": gc.title,
        "members": [_member_to_dict(m) for m in sorted(gc.members, key=lambda x: x.position)],
        "created_at": gc.created_at.isoformat() if gc.created_at else None,
        "updated_at": gc.updated_at.isoformat() if gc.updated_at else None,
    }


@router.post("", status_code=201)
async def create_group_chat(
    body: CreateGroupChatRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify all characters exist
    result = await db.execute(
        select(Character).where(Character.id.in_(body.character_ids))
    )
    characters = {c.id: c for c in result.scalars().all()}
    if len(characters) < len(body.character_ids):
        raise HTTPException(status_code=404, detail="One or more characters not found")

    title = body.title or " & ".join(characters[cid].name for cid in body.character_ids[:3])
    if len(body.character_ids) > 3:
        title += f" +{len(body.character_ids) - 3}"

    gc = GroupChat(user_id=user["id"], title=title)
    db.add(gc)
    await db.flush()

    for i, cid in enumerate(body.character_ids):
        member = GroupChatMember(group_chat_id=gc.id, character_id=cid, position=i)
        db.add(member)

    await db.commit()

    # Re-fetch with relationships
    result = await db.execute(
        select(GroupChat)
        .options(selectinload(GroupChat.members).selectinload(GroupChatMember.character))
        .where(GroupChat.id == gc.id)
    )
    gc = result.scalar_one()
    return _chat_to_dict(gc)


@router.get("")
async def list_group_chats(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GroupChat)
        .options(selectinload(GroupChat.members).selectinload(GroupChatMember.character))
        .where(GroupChat.user_id == user["id"])
        .order_by(GroupChat.updated_at.desc())
    )
    return [_chat_to_dict(gc) for gc in result.scalars().all()]


@router.get("/{chat_id}")
async def get_group_chat(
    chat_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GroupChat)
        .options(selectinload(GroupChat.members).selectinload(GroupChatMember.character))
        .where(GroupChat.id == chat_id, GroupChat.user_id == user["id"])
    )
    gc = result.scalar_one_or_none()
    if not gc:
        raise HTTPException(status_code=404, detail="Group chat not found")

    # Get last 30 messages
    msgs_result = await db.execute(
        select(GroupMessage)
        .where(GroupMessage.group_chat_id == chat_id)
        .order_by(GroupMessage.created_at.desc())
        .limit(30)
    )
    msgs = list(msgs_result.scalars().all())
    msgs.reverse()

    return {
        "chat": _chat_to_dict(gc),
        "messages": [_message_to_dict(m) for m in msgs],
    }


@router.delete("/{chat_id}", status_code=204)
async def delete_group_chat(
    chat_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GroupChat).where(GroupChat.id == chat_id, GroupChat.user_id == user["id"])
    )
    gc = result.scalar_one_or_none()
    if not gc:
        raise HTTPException(status_code=404, detail="Group chat not found")
    await db.delete(gc)
    await db.commit()


@router.post("/{chat_id}/message")
async def send_group_message(
    chat_id: str,
    body: SendGroupMessageRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """User sends a message, then each character responds in sequence via SSE."""
    await check_daily_limit(user["id"], user.get("role", "user"))

    result = await db.execute(
        select(GroupChat)
        .options(selectinload(GroupChat.members).selectinload(GroupChatMember.character))
        .where(GroupChat.id == chat_id, GroupChat.user_id == user["id"])
    )
    gc = result.scalar_one_or_none()
    if not gc:
        raise HTTPException(status_code=404, detail="Group chat not found")

    language = body.language or "ru"

    # Save user message
    user_msg = GroupMessage(
        group_chat_id=chat_id,
        character_id=None,
        role=MessageRole.user,
        content=body.content,
    )
    db.add(user_msg)
    gc.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user_msg)

    # Sort members by position
    members = sorted(gc.members, key=lambda m: m.position)

    # Get recent context messages
    ctx_result = await db.execute(
        select(GroupMessage)
        .where(GroupMessage.group_chat_id == chat_id)
        .order_by(GroupMessage.created_at.desc())
        .limit(MAX_CONTEXT_MESSAGES)
    )
    context_msgs = list(ctx_result.scalars().all())
    context_msgs.reverse()

    # Auto fallback provider order
    auto_order = [p.strip() for p in settings.auto_provider_order.split(",") if p.strip()]

    async def event_stream():
        # First, send user message confirmation
        yield f"data: {json.dumps({'type': 'user_saved', 'message_id': user_msg.id})}\n\n"

        for member in members:
            character = member.character
            if not character:
                continue

            # Build system prompt for this character
            char_dict = {
                "name": character.name,
                "personality": character.personality,
                "scenario": character.scenario,
                "greeting_message": character.greeting_message,
                "example_dialogues": character.example_dialogues,
                "content_rating": character.content_rating.value if character.content_rating else "sfw",
                "system_prompt_suffix": character.system_prompt_suffix,
                "response_length": getattr(character, 'response_length', None) or "medium",
                "appearance": getattr(character, 'appearance', None),
                "structured_tags": [t for t in (getattr(character, 'structured_tags', '') or '').split(",") if t],
            }

            # Build group-aware system prompt addition
            other_names = [m.character.name for m in members if m.character and m.character.id != character.id]
            group_context = f"\nThis is a GROUP CHAT with multiple characters. Other characters present: {', '.join(other_names)}. Keep responses shorter (1-2 paragraphs). React to what others said. Don't repeat what other characters already said."

            system_prompt = await build_system_prompt(
                char_dict, language=language, engine=db_engine,
            )
            system_prompt += group_context

            # Build conversation messages for this character
            llm_msgs = [LLMMessage(role="system", content=system_prompt)]
            for msg in context_msgs:
                role_val = msg.role.value if hasattr(msg.role, 'value') else msg.role
                if role_val == "user":
                    llm_msgs.append(LLMMessage(role="user", content=msg.content))
                else:
                    # Other characters' messages appear as assistant (with name prefix)
                    llm_msgs.append(LLMMessage(role="assistant", content=msg.content))

            config = LLMConfig(model="", temperature=0.8, max_tokens=1024)

            # Signal which character is about to respond
            yield f"data: {json.dumps({'type': 'character_start', 'character_id': character.id, 'character_name': character.name})}\n\n"

            # Try providers
            success = False
            full_response: list[str] = []
            actual_model = ""

            for pname in auto_order:
                try:
                    prov = get_provider(pname)
                except ValueError:
                    continue
                try:
                    async for chunk in prov.generate_stream(llm_msgs, config):
                        full_response.append(chunk)
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk, 'character_id': character.id})}\n\n"

                    complete_text = "".join(full_response)
                    actual_model = f"{pname}:{getattr(prov, 'last_model_used', '') or ''}"

                    # Save assistant message
                    async with db_engine.begin() as conn:
                        from sqlalchemy import text as sa_text
                        import uuid
                        msg_id = str(uuid.uuid4())
                        await conn.execute(sa_text(
                            "INSERT INTO group_messages (id, group_chat_id, character_id, role, content, model_used, created_at) "
                            "VALUES (:id, :gcid, :cid, 'assistant', :content, :model, NOW())"
                        ), {"id": msg_id, "gcid": chat_id, "cid": character.id, "content": complete_text, "model": actual_model})

                    yield f"data: {json.dumps({'type': 'character_done', 'character_id': character.id, 'message_id': msg_id, 'model_used': actual_model})}\n\n"
                    success = True

                    # Add to context for next character
                    context_msgs.append(type('Msg', (), {
                        'role': MessageRole.assistant, 'content': complete_text,
                        'character_id': character.id, 'id': msg_id,
                    })())
                    break
                except Exception:
                    full_response.clear()
                    continue

            if not success:
                yield f"data: {json.dumps({'type': 'character_error', 'character_id': character.id, 'content': 'Generation failed'})}\n\n"

        yield f"data: {json.dumps({'type': 'all_done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
