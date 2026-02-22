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
_FICTION_POST_HISTORY = {
    "ru": (
        "[Продолжай историю от второго лица. Сохраняй текущую локацию.\n"
        "Продвинь сюжет - новое событие, открытие или поворот.\n"
        "ОБЯЗАТЕЛЬНО заверши ответ 2-4 пронумерованными вариантами выбора.\n"
        "НЕ повторяй описания из предыдущих ответов.]"
    ),
    "en": (
        "[Continue the story in second person. Maintain the current location.\n"
        "Advance the plot - a new event, discovery, or twist.\n"
        "You MUST end your response with 2-4 numbered choices.\n"
        "Do NOT repeat descriptions from previous responses.]"
    ),
    "es": (
        "[Continua la historia en segunda persona. Manten la ubicacion actual.\n"
        "Avanza la trama - un nuevo evento, descubrimiento o giro.\n"
        "DEBES terminar tu respuesta con 2-4 opciones numeradas.\n"
        "NO repitas descripciones de respuestas anteriores.]"
    ),
    "fr": (
        "[Continue l'histoire a la deuxieme personne. Maintiens le lieu actuel.\n"
        "Fais avancer l'intrigue - un nouvel evenement, decouverte ou rebondissement.\n"
        "Tu DOIS terminer ta reponse par 2-4 choix numerotes.\n"
        "NE repete PAS les descriptions des reponses precedentes.]"
    ),
    "de": (
        "[Setze die Geschichte in der zweiten Person fort. Behalte den aktuellen Ort bei.\n"
        "Bringe die Handlung voran - ein neues Ereignis, eine Entdeckung oder Wendung.\n"
        "Du MUSST deine Antwort mit 2-4 nummerierten Optionen beenden.\n"
        "Wiederhole KEINE Beschreibungen aus vorherigen Antworten.]"
    ),
    "pt": (
        "[Continue a historia na segunda pessoa. Mantenha a localizacao atual.\n"
        "Avance a trama - um novo evento, descoberta ou reviravolta.\n"
        "Voce DEVE terminar sua resposta com 2-4 opcoes numeradas.\n"
        "NAO repita descricoes de respostas anteriores.]"
    ),
    "it": (
        "[Continua la storia in seconda persona. Mantieni la posizione attuale.\n"
        "Fai avanzare la trama - un nuovo evento, scoperta o colpo di scena.\n"
        "DEVI terminare la tua risposta con 2-4 scelte numerate.\n"
        "NON ripetere descrizioni dalle risposte precedenti.]"
    ),
}

_DND_POST_HISTORY = {
    "ru": (
        "[Продолжай как Game Master от второго лица. Сохраняй текущую локацию и состояние боя.\n"
        "Если выше дан результат броска — сначала опиши его исход.\n"
        "Когда нужен бросок — пиши [ROLL выражение описание]. НЕ бросай кубики сам.\n"
        "Продвинь сюжет — новое событие, столкновение или открытие.\n"
        "ОБЯЗАТЕЛЬНО заверши ответ 2-4 пронумерованными вариантами действий.\n"
        "НЕ повторяй описания из предыдущих ответов.]"
    ),
    "en": (
        "[Continue as Game Master in second person. Maintain current location and combat state.\n"
        "If a dice result is provided above, describe its outcome first.\n"
        "When a roll is needed — write [ROLL expression description]. Do NOT roll dice yourself.\n"
        "Advance the plot — a new event, encounter, or discovery.\n"
        "You MUST end your response with 2-4 numbered action choices.\n"
        "Do NOT repeat descriptions from previous responses.]"
    ),
    "es": (
        "[Continua como Game Master en segunda persona. Manten la ubicacion y estado de combate.\n"
        "Si hay un resultado de tirada arriba, describe su desenlace primero.\n"
        "Para tiradas: [ROLL expresion descripcion]. NO tires dados tu mismo.\n"
        "Avanza la trama. DEBES terminar con 2-4 opciones numeradas.\n"
        "NO repitas descripciones de respuestas anteriores.]"
    ),
    "fr": (
        "[Continue comme Maitre du Jeu a la deuxieme personne. Maintiens le lieu et l'etat du combat.\n"
        "Si un resultat de lancer est fourni ci-dessus, decris son issue d'abord.\n"
        "Pour les jets: [ROLL expression description]. NE lance PAS les des toi-meme.\n"
        "Fais avancer l'intrigue. Tu DOIS terminer par 2-4 options numerotees.\n"
        "NE repete PAS les descriptions des reponses precedentes.]"
    ),
    "de": (
        "[Setze als Spielleiter in der zweiten Person fort. Behalte Ort und Kampfzustand bei.\n"
        "Wenn oben ein Wurfelergebnis steht, beschreibe zuerst dessen Ausgang.\n"
        "Fur Wurfe: [ROLL Ausdruck Beschreibung]. Wurfle NICHT selbst.\n"
        "Bringe die Handlung voran. Du MUSST mit 2-4 nummerierten Optionen enden.\n"
        "Wiederhole KEINE Beschreibungen aus vorherigen Antworten.]"
    ),
    "pt": (
        "[Continue como Mestre do Jogo na segunda pessoa. Mantenha local e estado de combate.\n"
        "Se um resultado de rolagem foi fornecido acima, descreva seu desfecho primeiro.\n"
        "Para rolagens: [ROLL expressao descricao]. NAO role dados voce mesmo.\n"
        "Avance a trama. DEVE terminar com 2-4 opcoes numeradas.\n"
        "NAO repita descricoes de respostas anteriores.]"
    ),
    "it": (
        "[Continua come Game Master in seconda persona. Mantieni posizione e stato del combattimento.\n"
        "Se sopra e fornito un risultato di tiro, descrivi prima il suo esito.\n"
        "Per i tiri: [ROLL espressione descrizione]. NON tirare i dadi tu stesso.\n"
        "Fai avanzare la trama. DEVI terminare con 2-4 opzioni numerate.\n"
        "NON ripetere descrizioni dalle risposte precedenti.]"
    ),
}

# ── Dice result injection for next-turn context ──────────────
_DICE_INJECTION_HEADER = {
    "ru": "РЕЗУЛЬТАТ БРОСКА",
    "en": "DICE RESULT",
    "es": "RESULTADO DE TIRADA",
    "fr": "RESULTAT DU LANCER",
    "de": "WURFELERGEBNIS",
    "pt": "RESULTADO DA ROLAGEM",
    "it": "RISULTATO DEL TIRO",
}
_DICE_INJECTION_FOOTER = {
    "ru": "Опиши исход этого броска в начале ответа. Результат уже определен — не бросай заново.",
    "en": "Describe the outcome of this roll at the start of your response. The result is final — do not re-roll.",
    "es": "Describe el resultado de esta tirada al inicio de tu respuesta. El resultado es definitivo.",
    "fr": "Decris le resultat de ce lancer au debut de ta reponse. Le resultat est definitif.",
    "de": "Beschreibe das Ergebnis dieses Wurfs am Anfang deiner Antwort. Das Ergebnis steht fest.",
    "pt": "Descreva o resultado desta rolagem no inicio da sua resposta. O resultado e definitivo.",
    "it": "Descrivi l'esito di questo tiro all'inizio della risposta. Il risultato e definitivo.",
}


def _format_dice_injection(dice_rolls: list[dict], language: str) -> str:
    """Format previous dice results as a system message for next-turn injection."""
    header = _DICE_INJECTION_HEADER.get(language, _DICE_INJECTION_HEADER["en"])
    footer = _DICE_INJECTION_FOOTER.get(language, _DICE_INJECTION_FOOTER["en"])
    lines = [f"[{header}]"]
    for r in dice_rolls:
        desc = r.get("description", "")
        expr = r.get("expression", "?")
        total = r.get("total", 0)
        rolls = r.get("rolls", [])
        mod = r.get("modifier", 0)
        detail = f"rolls {rolls}"
        if mod:
            detail += f" + {mod}"
        line = f"- {expr} = {total} ({detail})"
        if desc:
            line += f" — {desc}"
        lines.append(line)
    lines.append(footer)
    return "\n".join(lines)


_TUTOR_POST_HISTORY = {
    "en": "[Continue as {name}. If the user made language errors, gently correct 1-2 of them. Introduce a new word or phrase naturally. Keep it conversational.]",
    "ru": "[\u041f\u0440\u043e\u0434\u043e\u043b\u0436\u0430\u0439 \u043a\u0430\u043a {name}. \u0415\u0441\u043b\u0438 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c \u0434\u043e\u043f\u0443\u0441\u0442\u0438\u043b \u043e\u0448\u0438\u0431\u043a\u0438, \u043c\u044f\u0433\u043a\u043e \u0438\u0441\u043f\u0440\u0430\u0432\u044c 1-2. \u0412\u0432\u0435\u0434\u0438 \u043d\u043e\u0432\u043e\u0435 \u0441\u043b\u043e\u0432\u043e \u0435\u0441\u0442\u0435\u0441\u0442\u0432\u0435\u043d\u043d\u043e. \u0413\u043e\u0432\u043e\u0440\u0438 \u0440\u0430\u0437\u0433\u043e\u0432\u043e\u0440\u043d\u043e.]",
    "es": "[Contin\u00faa como {name}. Si el usuario cometi\u00f3 errores, corrige 1-2 suavemente. Introduce una palabra nueva naturalmente. Mant\u00e9n el tono conversacional.]",
    "fr": "[Continue en tant que {name}. Si l'utilisateur a fait des erreurs, corrige 1-2 doucement. Introduis un nouveau mot naturellement. Reste conversationnel.]",
    "de": "[Fahre fort als {name}. Wenn der Benutzer Fehler gemacht hat, korrigiere 1-2 sanft. F\u00fchre ein neues Wort nat\u00fcrlich ein. Bleib im Gespr\u00e4chston.]",
    "pt": "[Continue como {name}. Se o usu\u00e1rio cometeu erros, corrija 1-2 suavemente. Introduza uma nova palavra naturalmente. Mantenha o tom conversacional.]",
    "it": "[Continua come {name}. Se l'utente ha commesso errori, correggi 1-2 gentilmente. Introduci una nuova parola naturalmente. Mantieni il tono conversazionale.]",
}

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
    site_mode: str = "nsfw",
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
        "tags": getattr(character, 'tags', '') or '',
    }
    messages_data, _ = await get_chat_messages(db, chat_id)  # all messages, no limit

    # Check if this chat is part of a campaign (DnD mode)
    chat_result_obj = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat_obj = chat_result_obj.scalar_one_or_none()
    campaign_id = getattr(chat_obj, 'campaign_id', None) if chat_obj else None
    encounter_state = getattr(chat_obj, 'encounter_state', None) if chat_obj else None

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
        site_mode=site_mode,
        campaign_id=campaign_id, encounter_state=encounter_state,
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
    # Campaign chats use DnD post-history regardless of site_mode
    tags_str = char_dict.get("tags", "")
    is_dnd = bool(campaign_id) or "dnd" in [t.strip() for t in tags_str.split(",")]
    if is_dnd:
        post_history_dict = _DND_POST_HISTORY
    elif campaign_id:
        post_history_dict = _DND_POST_HISTORY
    else:
        _POST_HISTORY_MAP = {"sfw": _TUTOR_POST_HISTORY, "fiction": _FICTION_POST_HISTORY}
        post_history_dict = _POST_HISTORY_MAP.get(site_mode, _POST_HISTORY)
    lang = language if language in post_history_dict else "en"
    reminder = post_history_dict[lang].format(name=character.name)
    all_messages = result_list + messages

    # Inject previous dice results for DnD chats (before post-history)
    if is_dnd and messages_data:
        # Find the last assistant message — only inject if it has dice_rolls
        for msg in reversed(messages_data):
            if (hasattr(msg.role, 'value') and msg.role.value or msg.role) == "assistant":
                if getattr(msg, 'dice_rolls', None):
                    all_messages.append(LLMMessage(
                        role="system",
                        content=_format_dice_injection(msg.dice_rolls, language),
                    ))
                break

    all_messages.append(LLMMessage(role="system", content=reminder))
    return all_messages
