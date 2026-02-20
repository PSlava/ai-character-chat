from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models import Chat, Message, Character, User, Persona, MessageRole, LoreEntry
from app.chat.prompt_builder import build_system_prompt
from app.db.session import engine as db_engine
from app.llm.base import LLMMessage

MAX_CONTEXT_MESSAGES = 50
DEFAULT_CONTEXT_TOKENS = 24000  # ~6k real tokens; Russian text needs ~4 chars/token

# Post-history reminder — injected AFTER chat history, closest to generation point.
# Short (~50 tokens) reinforcement of key rules. Most effective position per SillyTavern research.
_POST_HISTORY = {
    "ru": (
        "[Продолжай сцену как {name}. Третье лицо. Покажи, а не расскажи.\n"
        "ОБЯЗАТЕЛЬНО: сохраняй текущую локацию и обстановку из предыдущих сообщений. Не теряй место действия.\n"
        "Продвинь сюжет — новое действие или изменение.\n"
        "СТРОГО ЗАПРЕЩЕНО повторять фразы, описания, звуки и реакции из предыдущих ответов. "
        "Перечитай свои последние ответы — используй ДРУГИЕ слова, ДРУГИЕ описания, ДРУГИЕ реакции. Удиви читателя.]"
    ),
    "en": (
        "[Continue the scene as {name}. Third person. Show, don't tell.\n"
        "REQUIRED: maintain the current location and setting from previous messages. Don't lose the scene's place.\n"
        "Advance the plot — a new action or change.\n"
        "STRICTLY FORBIDDEN to repeat phrases, descriptions, sounds, or reactions from previous responses. "
        "Re-read your recent responses — use DIFFERENT words, DIFFERENT descriptions, DIFFERENT reactions. Surprise the reader.]"
    ),
    "es": (
        "[Continua la escena como {name}. Tercera persona. Muestra, no cuentes.\n"
        "OBLIGATORIO: mantén la ubicación y el entorno actuales de los mensajes anteriores. No pierdas el lugar de la escena.\n"
        "Avanza la trama — una nueva acción o cambio.\n"
        "ESTRICTAMENTE PROHIBIDO repetir frases, descripciones, sonidos o reacciones de respuestas anteriores. "
        "Relee tus respuestas recientes — usa OTRAS palabras, OTRAS descripciones, OTRAS reacciones. Sorprende al lector.]"
    ),
    "fr": (
        "[Continue la scène en tant que {name}. Troisième personne. Montre, ne raconte pas.\n"
        "OBLIGATOIRE : maintiens le lieu et le décor actuels des messages précédents. Ne perds pas le cadre de la scène.\n"
        "Fais avancer l'intrigue — une nouvelle action ou un changement.\n"
        "STRICTEMENT INTERDIT de répéter des phrases, descriptions, sons ou réactions des réponses précédentes. "
        "Relis tes réponses récentes — utilise D'AUTRES mots, D'AUTRES descriptions, D'AUTRES réactions. Surprends le lecteur.]"
    ),
    "de": (
        "[Setze die Szene als {name} fort. Dritte Person. Zeigen, nicht erzählen.\n"
        "PFLICHT: Behalte den aktuellen Ort und die Umgebung aus den vorherigen Nachrichten bei. Verliere den Schauplatz nicht.\n"
        "Bringe die Handlung voran — eine neue Aktion oder Veränderung.\n"
        "STRENG VERBOTEN, Phrasen, Beschreibungen, Geräusche oder Reaktionen aus vorherigen Antworten zu wiederholen. "
        "Lies deine letzten Antworten erneut — verwende ANDERE Worte, ANDERE Beschreibungen, ANDERE Reaktionen. Überrasche den Leser.]"
    ),
    "pt": (
        "[Continue a cena como {name}. Terceira pessoa. Mostre, não conte.\n"
        "OBRIGATÓRIO: mantenha a localização e o cenário atuais das mensagens anteriores. Não perca o lugar da cena.\n"
        "Avance a trama — uma nova ação ou mudança.\n"
        "ESTRITAMENTE PROIBIDO repetir frases, descrições, sons ou reações de respostas anteriores. "
        "Releia suas respostas recentes — use OUTRAS palavras, OUTRAS descrições, OUTRAS reações. Surpreenda o leitor.]"
    ),
    "it": (
        "[Continua la scena come {name}. Terza persona. Mostra, non raccontare.\n"
        "OBBLIGATORIO: mantieni la posizione e l'ambientazione attuali dai messaggi precedenti. Non perdere il luogo della scena.\n"
        "Fai avanzare la trama — una nuova azione o cambiamento.\n"
        "SEVERAMENTE VIETATO ripetere frasi, descrizioni, suoni o reazioni dalle risposte precedenti. "
        "Rileggi le tue risposte recenti — usa ALTRE parole, ALTRE descrizioni, ALTRE reazioni. Sorprendi il lettore.]"
    ),
}


async def get_or_create_chat(
    db: AsyncSession, user_id: str, character_id: str,
    model: str | None = None, persona_id: str | None = None,
    force_new: bool = False, anon_session_id: str | None = None,
    language: str | None = None,
):
    """Return existing chat with this character, or create a new one."""
    if not force_new:
        # Check for existing chat
        q = (
            select(Chat)
            .options(selectinload(Chat.character), selectinload(Chat.persona))
            .where(Chat.character_id == character_id)
        )
        if anon_session_id:
            q = q.where(Chat.anon_session_id == anon_session_id)
        else:
            q = q.where(Chat.user_id == user_id)
        existing = await db.execute(q)
        chat = existing.scalar_one_or_none()
        if chat:
            return chat, chat.character, False  # False = not newly created

    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        return None, None, False

    model_used = model or character.preferred_model or "auto"

    # Load persona snapshot if persona_id provided (not for anonymous)
    p_name = None
    p_description = None
    if persona_id and not anon_session_id:
        persona_result = await db.execute(select(Persona).where(Persona.id == persona_id))
        persona_obj = persona_result.scalar_one_or_none()
        if persona_obj:
            p_name = persona_obj.name
            p_description = persona_obj.description

    chat = Chat(
        user_id=user_id,
        character_id=character_id,
        persona_id=persona_id if not anon_session_id else None,
        persona_name=p_name,
        persona_description=p_description,
        title=character.name,
        model_used=model_used,
        anon_session_id=anon_session_id,
    )
    db.add(chat)
    await db.flush()

    # Use cached translated greeting if available for the user's language
    greeting_text = character.greeting_message
    char_name = character.name
    if language and language != "ru" and character.translations:
        tr = character.translations.get(language, {})
        if tr.get("greeting_message"):
            greeting_text = tr["greeting_message"]
        if tr.get("name"):
            char_name = tr["name"]

    # Apply {{char}}/{{user}} template variables in greeting
    if "{{char}}" in greeting_text or "{{user}}" in greeting_text:
        if anon_session_id:
            u_name = "User"
        else:
            u_name = p_name
            if not u_name:
                user_result = await db.execute(select(User).where(User.id == user_id))
                user_obj = user_result.scalar_one_or_none()
                u_name = user_obj.display_name if user_obj and user_obj.display_name else "User"
        greeting_text = greeting_text.replace("{{char}}", char_name).replace("{{user}}", u_name)

    greeting = Message(
        chat_id=chat.id,
        role=MessageRole.assistant,
        content=greeting_text,
        token_count=len(greeting_text) // 4,
    )
    db.add(greeting)

    character.chat_count = (character.chat_count or 0) + 1

    # Increment user chat count (skip for anonymous)
    if not anon_session_id:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user_obj = user_result.scalar_one_or_none()
        if user_obj:
            user_obj.chat_count = (user_obj.chat_count or 0) + 1

    await db.commit()

    # Re-fetch with relationships loaded
    result = await db.execute(
        select(Chat)
        .options(selectinload(Chat.character), selectinload(Chat.persona))
        .where(Chat.id == chat.id)
    )
    chat = result.scalar_one()
    return chat, chat.character, True  # True = newly created


async def get_chat(db: AsyncSession, chat_id: str, user_id: str | None = None, anon_session_id: str | None = None):
    q = (
        select(Chat)
        .options(
            selectinload(Chat.character).selectinload(Character.creator),
            selectinload(Chat.persona),
        )
        .where(Chat.id == chat_id)
    )
    if anon_session_id:
        q = q.where(Chat.anon_session_id == anon_session_id)
    elif user_id:
        q = q.where(Chat.user_id == user_id)
    else:
        return None
    result = await db.execute(q)
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
        .options(selectinload(Chat.character), selectinload(Chat.persona))
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


async def save_message(
    db: AsyncSession, chat_id: str, role: str, content: str,
    model_used: str | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
):
    msg = Message(
        chat_id=chat_id,
        role=MessageRole(role),
        content=content,
        token_count=len(content) // 4,
        model_used=model_used,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
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


async def increment_message_count(character_id: str, language: str, user_id: str | None = None):
    """Atomically increment message_counts->{language} for a character and user message_count."""
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
        if user_id:
            await conn.execute(
                text("UPDATE users SET message_count = COALESCE(message_count, 0) + 1 WHERE id = :uid"),
                {"uid": user_id},
            )


async def build_conversation_messages(
    db: AsyncSession,
    chat_id: str,
    character: Character,
    user_name: str | None = None,
    user_description: str | None = None,
    language: str = "ru",
    context_limit: int | None = None,
    max_context_messages: int | None = None,
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
    messages_data, _ = await get_chat_messages(db, chat_id)  # all messages, no limit

    # Load lore entries for this character
    lore_result = await db.execute(
        select(LoreEntry)
        .where(LoreEntry.character_id == character.id, LoreEntry.enabled == True)  # noqa: E712
        .order_by(LoreEntry.position)
    )
    lore_entries = [
        {"keywords": e.keywords, "content": e.content, "enabled": e.enabled}
        for e in lore_result.scalars().all()
    ]

    # Build context text from recent messages for lore keyword matching
    recent_texts = [m.content for m in messages_data[-10:]]  # last 10 messages
    context_text = " ".join(recent_texts)

    system_prompt = await build_system_prompt(
        char_dict, user_name=user_name, user_description=user_description,
        language=language, engine=db_engine,
        lore_entries=lore_entries, context_text=context_text,
    )

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

    effective_max = max_context_messages or MAX_CONTEXT_MESSAGES
    messages = messages[-effective_max:]

    result_list = [LLMMessage(role="system", content=system_prompt)]

    # Inject chat summary if available (memory of older messages)
    chat_result = await db.execute(select(Chat.summary).where(Chat.id == chat_id))
    summary = chat_result.scalar_one_or_none()
    if summary:
        summary_labels = {
            "ru": "[Краткое содержание предыдущего разговора]",
            "en": "[Previous conversation summary]",
            "es": "[Resumen de la conversación anterior]",
            "fr": "[Résumé de la conversation précédente]",
            "de": "[Zusammenfassung des bisherigen Gesprächs]",
            "pt": "[Resumo da conversa anterior]",
            "it": "[Riassunto della conversazione precedente]",
        }
        label = summary_labels.get(language, summary_labels["en"])
        result_list.append(LLMMessage(role="system", content=f"{label}\n{summary}"))

    # Post-history reminder (closest to generation = strongest reinforcement)
    content_rating = char_dict.get("content_rating", "sfw")
    lang = language if language in _POST_HISTORY else "en"
    reminder = _POST_HISTORY[lang].format(name=character.name)
    all_messages = result_list + messages
    all_messages.append(LLMMessage(role="system", content=reminder))
    return all_messages
