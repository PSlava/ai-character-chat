from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models import Chat, Message, Character, User, Persona, MessageRole
from app.chat.prompt_builder import build_system_prompt
from app.db.session import engine as db_engine
from app.llm.base import LLMMessage

MAX_CONTEXT_MESSAGES = 50
DEFAULT_CONTEXT_TOKENS = 24000  # ~6k real tokens; Russian text needs ~4 chars/token


async def get_or_create_chat(
    db: AsyncSession, user_id: str, character_id: str,
    model: str | None = None, persona_id: str | None = None,
):
    """Return existing chat with this character, or create a new one."""
    # Check for existing chat
    existing = await db.execute(
        select(Chat)
        .options(selectinload(Chat.character))
        .where(Chat.user_id == user_id, Chat.character_id == character_id)
    )
    chat = existing.scalar_one_or_none()
    if chat:
        return chat, chat.character, False  # False = not newly created

    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        return None, None, False

    model_used = model or character.preferred_model or "claude"

    chat = Chat(
        user_id=user_id,
        character_id=character_id,
        persona_id=persona_id,
        title=character.name,
        model_used=model_used,
    )
    db.add(chat)
    await db.flush()

    # Apply {{char}}/{{user}} template variables in greeting
    greeting_text = character.greeting_message
    if "{{char}}" in greeting_text or "{{user}}" in greeting_text:
        # Prefer persona name over display_name for {{user}}
        u_name = None
        if persona_id:
            persona_result = await db.execute(select(Persona).where(Persona.id == persona_id))
            persona_obj = persona_result.scalar_one_or_none()
            if persona_obj:
                u_name = persona_obj.name
        if not u_name:
            user_result = await db.execute(select(User).where(User.id == user_id))
            user_obj = user_result.scalar_one_or_none()
            u_name = user_obj.display_name if user_obj and user_obj.display_name else "User"
        greeting_text = greeting_text.replace("{{char}}", character.name).replace("{{user}}", u_name)

    greeting = Message(
        chat_id=chat.id,
        role=MessageRole.assistant,
        content=greeting_text,
        token_count=len(greeting_text) // 4,
    )
    db.add(greeting)

    character.chat_count = (character.chat_count or 0) + 1
    await db.commit()

    # Re-fetch with relationships loaded
    result = await db.execute(
        select(Chat)
        .options(selectinload(Chat.character))
        .where(Chat.id == chat.id)
    )
    chat = result.scalar_one()
    return chat, chat.character, True  # True = newly created


async def get_chat(db: AsyncSession, chat_id: str, user_id: str):
    result = await db.execute(
        select(Chat)
        .options(selectinload(Chat.character).selectinload(Character.creator))
        .where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_chat_messages(db: AsyncSession, chat_id: str, limit: int = 0, before_id: str | None = None):
    """Get messages for a chat. If limit > 0, return paginated (last N messages).

    Returns (messages, has_more) when limit > 0, or (messages, False) when limit == 0 (all).
    """
    q = select(Message).where(Message.chat_id == chat_id)

    if before_id:
        anchor = await db.execute(select(Message.created_at).where(Message.id == before_id))
        anchor_time = anchor.scalar_one_or_none()
        if anchor_time:
            q = q.where(Message.created_at < anchor_time)

    if limit > 0:
        q = q.order_by(Message.created_at.desc()).limit(limit + 1)
        result = await db.execute(q)
        msgs = list(result.scalars().all())
        has_more = len(msgs) > limit
        if has_more:
            msgs = msgs[:limit]
        msgs.reverse()
        return msgs, has_more

    # No limit — return all (used by build_conversation_messages)
    q = q.order_by(Message.created_at.asc())
    result = await db.execute(q)
    return result.scalars().all(), False


async def list_user_chats(db: AsyncSession, user_id: str):
    result = await db.execute(
        select(Chat)
        .options(selectinload(Chat.character))
        .where(Chat.user_id == user_id)
        .order_by(Chat.updated_at.desc())
    )
    return result.scalars().all()


async def delete_chat(db: AsyncSession, chat_id: str, user_id: str):
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        return False
    await db.delete(chat)
    await db.commit()
    return True


async def save_message(db: AsyncSession, chat_id: str, role: str, content: str, model_used: str | None = None):
    msg = Message(
        chat_id=chat_id,
        role=MessageRole(role),
        content=content,
        token_count=len(content) // 4,
        model_used=model_used,
    )
    db.add(msg)

    # Update chat timestamp
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()
    if chat:
        chat.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(msg)
    return msg


async def clear_chat_messages(db: AsyncSession, chat_id: str, user_id: str):
    """Delete all messages except the first one (greeting)."""
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        return False

    # Get first message (greeting) to keep it
    msgs = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
    )
    all_msgs = msgs.scalars().all()
    if len(all_msgs) <= 1:
        return True  # nothing to clear

    for msg in all_msgs[1:]:
        await db.delete(msg)

    chat.updated_at = datetime.utcnow()
    await db.commit()
    return True


async def delete_message(db: AsyncSession, chat_id: str, message_id: str, user_id: str):
    """Delete a single message. Cannot delete the first (greeting) message."""
    # Verify chat ownership
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        return False

    # Get the first message to protect it
    first_msg = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .limit(1)
    )
    first = first_msg.scalar_one_or_none()
    if first and first.id == message_id:
        return False  # can't delete greeting

    # Delete the message
    msg_result = await db.execute(
        select(Message).where(Message.id == message_id, Message.chat_id == chat_id)
    )
    msg = msg_result.scalar_one_or_none()
    if not msg:
        return False

    await db.delete(msg)
    await db.commit()
    return True


async def increment_message_count(character_id: str, language: str):
    """Atomically increment message_counts->{language} for a character."""
    lang = language[:10]  # safety limit
    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                UPDATE characters SET message_counts = jsonb_set(
                    COALESCE(message_counts, '{}'),
                    ARRAY[:lang],
                    to_jsonb(COALESCE((message_counts->>:lang)::int, 0) + 1)
                ) WHERE id = :cid
            """),
            {"lang": lang, "cid": character_id},
        )


async def build_conversation_messages(
    db: AsyncSession,
    chat_id: str,
    character: Character,
    user_name: str | None = None,
    user_description: str | None = None,
    language: str = "ru",
    context_limit: int | None = None,
) -> list[LLMMessage]:
    char_dict = {
        "name": character.name,
        "personality": character.personality,
        "scenario": character.scenario,
        "greeting_message": character.greeting_message,
        "example_dialogues": character.example_dialogues,
        "content_rating": character.content_rating.value if character.content_rating else "sfw",
        "system_prompt_suffix": character.system_prompt_suffix,
        "response_length": getattr(character, 'response_length', None) or "long",
        "appearance": getattr(character, 'appearance', None),
        "structured_tags": [t for t in (getattr(character, 'structured_tags', '') or '').split(",") if t],
    }
    system_prompt = await build_system_prompt(
        char_dict, user_name=user_name, user_description=user_description,
        language=language, engine=db_engine,
    )
    messages_data, _ = await get_chat_messages(db, chat_id)  # all messages, no limit

    # context_limit is in "real" tokens; multiply by ~4 for char-based estimation
    max_tokens = (context_limit * 4) if context_limit else DEFAULT_CONTEXT_TOKENS

    # Sliding window
    messages: list[LLMMessage] = []
    total_tokens = 0
    for msg in reversed(messages_data):
        est_tokens = msg.token_count or len(msg.content) // 4
        if total_tokens + est_tokens > max_tokens:
            break
        messages.insert(0, LLMMessage(role=msg.role.value if hasattr(msg.role, 'value') else msg.role, content=msg.content))
        total_tokens += est_tokens

    messages = messages[-MAX_CONTEXT_MESSAGES:]
    return [LLMMessage(role="system", content=system_prompt)] + messages
