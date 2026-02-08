from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models import Chat, Message, Character, MessageRole
from app.chat.prompt_builder import build_system_prompt
from app.llm.base import LLMMessage

MAX_CONTEXT_MESSAGES = 50
MAX_CONTEXT_TOKENS = 12000


async def create_chat(db: AsyncSession, user_id: str, character_id: str, model: str | None = None):
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        return None, None

    model_used = model or character.preferred_model or "claude"

    chat = Chat(
        user_id=user_id,
        character_id=character_id,
        title=character.name,
        model_used=model_used,
    )
    db.add(chat)
    await db.flush()

    greeting = Message(
        chat_id=chat.id,
        role=MessageRole.assistant,
        content=character.greeting_message,
        token_count=len(character.greeting_message) // 4,
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
    return chat, chat.character


async def get_chat(db: AsyncSession, chat_id: str, user_id: str):
    result = await db.execute(
        select(Chat)
        .options(selectinload(Chat.character).selectinload(Character.creator))
        .where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_chat_messages(db: AsyncSession, chat_id: str):
    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
    )
    return result.scalars().all()


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


async def save_message(db: AsyncSession, chat_id: str, role: str, content: str):
    msg = Message(
        chat_id=chat_id,
        role=MessageRole(role),
        content=content,
        token_count=len(content) // 4,
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


async def build_conversation_messages(db: AsyncSession, chat_id: str, character: Character, user_name: str | None = None) -> list[LLMMessage]:
    char_dict = {
        "name": character.name,
        "personality": character.personality,
        "scenario": character.scenario,
        "greeting_message": character.greeting_message,
        "example_dialogues": character.example_dialogues,
        "content_rating": character.content_rating.value if character.content_rating else "sfw",
        "system_prompt_suffix": character.system_prompt_suffix,
    }
    system_prompt = build_system_prompt(char_dict, user_name=user_name)
    messages_data = await get_chat_messages(db, chat_id)

    # Sliding window
    messages: list[LLMMessage] = []
    total_tokens = 0
    for msg in reversed(messages_data):
        est_tokens = msg.token_count or len(msg.content) // 4
        if total_tokens + est_tokens > MAX_CONTEXT_TOKENS:
            break
        messages.insert(0, LLMMessage(role=msg.role.value if hasattr(msg.role, 'value') else msg.role, content=msg.content))
        total_tokens += est_tokens

    messages = messages[-MAX_CONTEXT_MESSAGES:]
    return [LLMMessage(role="system", content=system_prompt)] + messages
