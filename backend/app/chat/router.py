import json
import time as _time
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from starlette.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text as sa_text
from app.auth.middleware import get_current_user, get_current_user_optional
from app.db.session import get_db
from app.chat.schemas import CreateChatRequest, SendMessageRequest
from app.chat import service
from app.chat.anon import get_anon_user_id, check_anon_limit, get_anon_remaining, get_anon_message_limit
from app.db.models import User, Persona, Message, Chat
from app.llm.base import LLMConfig, LLMMessage
from app.llm.registry import get_provider
from app.config import settings
from app.auth.rate_limit import check_message_rate, check_message_interval
from app.chat.daily_limit import check_daily_limit, get_daily_usage, get_cost_mode, get_user_tier, get_tier_limits, cap_max_tokens
from app.chat.summarizer import maybe_summarize
import re as _re
import asyncio as _asyncio

router = APIRouter(prefix="/api/chats", tags=["chat"])

# Pattern to match numbered choices at the end of AI response (e.g. "1. Open the door")
_CHOICE_PATTERN = _re.compile(r'^(\d+)\.\s+(.+)$', _re.MULTILINE)


def _parse_choices(text: str) -> list[dict] | None:
    """Extract numbered choices from the end of the AI response text.

    Returns list of {"number": 1, "text": "Open the door"} or None if no choices found.
    """
    # Look at the last ~500 chars for choices
    tail = text[-500:] if len(text) > 500 else text
    lines = tail.strip().split('\n')

    # Walk backwards to find consecutive numbered lines
    choices = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        m = _CHOICE_PATTERN.match(line)
        if m:
            choices.append({"number": int(m.group(1)), "text": m.group(2).strip()})
        else:
            break  # Stop at first non-choice line

    if len(choices) < 2:
        return None

    choices.reverse()
    return choices

# ── Paid mode cache (60s TTL) ─────────────────────────────────
_paid_mode_cache: tuple[bool, float] = (False, 0.0)
_PAID_CACHE_TTL = 60


async def _is_paid_mode(db: AsyncSession) -> bool:
    global _paid_mode_cache
    now = _time.monotonic()
    if now - _paid_mode_cache[1] < _PAID_CACHE_TTL:
        return _paid_mode_cache[0]
    try:
        row = await db.execute(sa_text("SELECT value FROM prompt_templates WHERE key = 'setting.paid_mode'"))
        val = (row.scalar_one_or_none() or "false").lower() == "true"
    except Exception:
        val = False
    _paid_mode_cache = (val, now)
    return val

_GENERIC_ERROR_RU = "Ошибка генерации ответа. Попробуйте позже."
_MODERATION_KEYWORDS = ("data_inspection_failed", "content_policy", "content_filter", "moderation", "safety system")

# Refusal phrases in model responses (model returns refusal as normal text)
_REFUSAL_PHRASES = (
    "не могу продолжить", "не могу продолжать", "незаконный контент",
    "не могу помочь", "не в состоянии помочь",
    "i cannot continue", "i can't continue", "i can't help",
    "i cannot help", "against my guidelines", "i'm not able to",
    "i must refuse", "i cannot generate", "i can't generate",
    "illegal content", "i cannot assist", "i can't assist",
    "no puedo continuar", "no puedo ayudar", "contenido ilegal",
)


def _is_moderation_error(err: str) -> bool:
    low = err.lower()
    return any(kw in low for kw in _MODERATION_KEYWORDS)


def _is_refusal_response(text: str) -> bool:
    """Check if model response is a content refusal (not a real answer)."""
    low = text.strip().lower()
    if len(low) > 500:
        return False  # Real responses are longer
    return any(phrase in low for phrase in _REFUSAL_PHRASES)


def _estimate_prompt_tokens(messages) -> int:
    """Estimate prompt tokens from LLM messages (rough: chars / 4)."""
    return sum(len(m.content) for m in messages) // 4


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
    persona = getattr(c, 'persona', None)
    d = {
        "id": c.id,
        "user_id": c.user_id,
        "character_id": c.character_id,
        "persona_id": getattr(c, 'persona_id', None),
        "persona_name": getattr(c, 'persona_name', None),
        "persona_slug": persona.slug if persona else None,
        "title": c.title,
        "model_used": c.model_used,
        "has_summary": bool(getattr(c, 'summary', None)),
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
    request: Request,
    user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    anon_session_id = None
    if user:
        chat, character, created = await service.get_or_create_chat(
            db, user["id"], body.character_id, body.model, persona_id=body.persona_id,
            force_new=body.force_new, language=body.language,
        )
    else:
        anon_session_id = request.headers.get("x-anon-session")
        if not anon_session_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        # Check if anonymous chat is enabled
        limit = await get_anon_message_limit()
        if limit <= 0:
            raise HTTPException(status_code=403, detail="anon_chat_disabled")
        anon_uid = await get_anon_user_id(db)
        chat, character, created = await service.get_or_create_chat(
            db, anon_uid, body.character_id, body.model,
            force_new=body.force_new,
            anon_session_id=anon_session_id, language=body.language,
        )

    if not chat:
        raise HTTPException(status_code=404, detail="Character not found")

    msgs, has_more = await service.get_chat_messages(db, chat.id, limit=20)
    resp = {
        "chat": chat_to_dict(chat),
        "messages": [message_to_dict(m) for m in msgs],
        "has_more": has_more,
    }
    if anon_session_id:
        resp["anon_messages_left"] = await get_anon_remaining(anon_session_id)
    return JSONResponse(content=resp, status_code=201 if created else 200)


@router.get("")
async def list_chats(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chats = await service.list_user_chats(db, user["id"])
    return [chat_to_dict(c) for c in chats]


@router.get("/anon-limit")
async def anon_limit(request: Request):
    """Public endpoint: returns anonymous chat limit and remaining messages."""
    limit = await get_anon_message_limit()
    session_id = request.headers.get("x-anon-session")
    remaining = limit
    if session_id and limit > 0:
        remaining = await get_anon_remaining(session_id)
    return {"limit": limit, "remaining": remaining, "enabled": limit > 0}


@router.get("/daily-usage")
async def daily_usage(
    user=Depends(get_current_user),
):
    """Return daily message usage for the current user."""
    return await get_daily_usage(user["id"])


@router.get("/{chat_id}")
async def get_chat(
    chat_id: str,
    request: Request,
    user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    anon_session_id = None
    if user:
        chat = await service.get_chat(db, chat_id, user_id=user["id"])
    else:
        anon_session_id = request.headers.get("x-anon-session")
        if not anon_session_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        chat = await service.get_chat(db, chat_id, anon_session_id=anon_session_id)

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    msgs, has_more = await service.get_chat_messages(db, chat_id, limit=20)
    resp = {
        "chat": chat_to_dict(chat),
        "messages": [message_to_dict(m) for m in msgs],
        "has_more": has_more,
    }
    if anon_session_id:
        resp["anon_messages_left"] = await get_anon_remaining(anon_session_id)
    return resp


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
    request: Request,
    before: str | None = None,
    limit: int = 20,
    user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Load older messages for infinite scroll."""
    if user:
        chat = await service.get_chat(db, chat_id, user_id=user["id"])
    else:
        anon_session_id = request.headers.get("x-anon-session")
        if not anon_session_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        chat = await service.get_chat(db, chat_id, anon_session_id=anon_session_id)

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


@router.post("/{chat_id}/generate-persona-reply")
async def generate_persona_reply(
    chat_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a reply as the user's persona. Returns text for editing, NOT saved."""
    from app.llm.base import LLMMessage

    # Check daily limit (counts toward usage)
    await check_daily_limit(user["id"], user.get("role", "user"))

    chat = await service.get_chat(db, chat_id, user["id"])
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    persona_name = getattr(chat, 'persona_name', None)
    if not persona_name:
        raise HTTPException(status_code=400, detail="No persona attached to this chat")

    persona_desc = getattr(chat, 'persona_description', None) or ""
    character_name = chat.character.name if chat.character else "Character"

    # Get recent messages for context
    msgs_result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    recent_msgs = list(msgs_result.scalars().all())
    recent_msgs.reverse()

    # Detect language from recent messages
    user_obj = await db.execute(select(User).where(User.id == user["id"]))
    user_obj = user_obj.scalar_one_or_none()
    language = user_obj.language if user_obj else "ru"

    lang_instructions = {
        "ru": "Напиши ответ на русском языке.",
        "en": "Write the reply in English.",
        "es": "Escribe la respuesta en español.",
        "fr": "Écris la réponse en français.",
        "de": "Schreibe die Antwort auf Deutsch.",
        "pt": "Escreva a resposta em português.",
        "it": "Scrivi la risposta in italiano.",
    }
    lang_hint = lang_instructions.get(language, lang_instructions["en"])

    # Build prompt
    system_prompt = (
        f"You are ghostwriting a reply as the user named '{persona_name}' in a roleplay chat "
        f"with a character named '{character_name}'.\n\n"
        f"About {persona_name}: {persona_desc}\n\n"
        f"Write a short in-character reply (1-3 sentences) as {persona_name} would say it. "
        f"Match the tone and style of the conversation. Use *asterisks* for actions/descriptions. "
        f"Do NOT write as {character_name} — only as {persona_name}.\n"
        f"{lang_hint}\n"
        f"Output ONLY the reply text, nothing else."
    )

    llm_msgs = [LLMMessage(role="system", content=system_prompt)]
    for msg in recent_msgs:
        role_val = msg.role.value if hasattr(msg.role, 'value') else msg.role
        if role_val == "user":
            llm_msgs.append(LLMMessage(role="user", content=msg.content))
        elif role_val == "assistant":
            llm_msgs.append(LLMMessage(role="assistant", content=msg.content))

    # Add a final instruction as user turn to prompt the generation
    llm_msgs.append(LLMMessage(
        role="user",
        content=f"Now write {persona_name}'s next reply to {character_name}. Reply text only."
    ))

    config = LLMConfig(model="", temperature=0.8, max_tokens=512)

    # Auto-fallback through providers
    auto_order = [p.strip() for p in settings.auto_provider_order.split(",") if p.strip()]
    generated_text = ""

    for pname in auto_order:
        try:
            prov = get_provider(pname)
        except ValueError:
            continue
        try:
            chunks = []
            async for chunk in prov.generate_stream(llm_msgs, config):
                chunks.append(chunk)
            generated_text = "".join(chunks)
            break
        except Exception:
            continue

    if not generated_text:
        raise HTTPException(status_code=500, detail="Generation failed")

    # Increment user message count (counts toward daily limit)
    if user_obj:
        user_obj.message_count = (user_obj.message_count or 0) + 1
        await db.commit()

    return {"content": generated_text.strip()}


async def _append_to_message(db: AsyncSession, message_id: str, appended_text: str, model_used: str, est_prompt: int, est_completion: int):
    """Append text to an existing assistant message (for continue feature)."""
    from datetime import datetime
    result = await db.execute(select(Message).where(Message.id == message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        return
    msg.content = (msg.content or "") + appended_text
    msg.token_count = len(msg.content) // 4
    msg.model_used = model_used
    msg.prompt_tokens = (msg.prompt_tokens or 0) + (est_prompt or 0)
    msg.completion_tokens = (msg.completion_tokens or 0) + (est_completion or 0)
    chat_result = await db.execute(select(Chat).where(Chat.id == msg.chat_id))
    chat_obj = chat_result.scalar_one_or_none()
    if chat_obj:
        chat_obj.updated_at = datetime.utcnow()
    await db.commit()


@router.post("/{chat_id}/message")
async def send_message(
    chat_id: str,
    body: SendMessageRequest,
    request: Request,
    user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    anon_session_id = None
    anon_remaining = None

    if user:
        check_message_rate(user["id"])
        if not body.is_regenerate and not body.is_continue:
            check_message_interval(user["id"])
        await check_daily_limit(user["id"], user.get("role", "user"))
        chat = await service.get_chat(db, chat_id, user_id=user["id"])
    else:
        anon_session_id = request.headers.get("x-anon-session")
        if not anon_session_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        check_message_rate(f"anon:{anon_session_id}")
        if not body.is_regenerate and not body.is_continue:
            check_message_interval(f"anon:{anon_session_id}")
        anon_remaining = await check_anon_limit(anon_session_id)  # raises 403 if exceeded
        chat = await service.get_chat(db, chat_id, anon_session_id=anon_session_id)

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    character = chat.character

    # If model override requested, persist it on the chat
    if body.model and body.model != chat.model_used:
        chat.model_used = body.model
        await db.commit()

    model_name = chat.model_used or settings.default_model
    content_rating = character.content_rating.value if character.content_rating else "sfw"

    # Handle "continue" — append to last assistant message
    continue_msg_id = None
    if body.is_continue:
        last_msgs, _ = await service.get_chat_messages(db, chat_id, limit=1)
        if last_msgs and last_msgs[0].role.value == "assistant":
            continue_msg_id = last_msgs[0].id
        # Create a virtual user message (not saved to DB) for the response
        user_msg = type('FakeMsg', (), {'id': 'continue'})()
    else:
        # Dedup: skip saving if last message is the same user text (e.g. page reload after error)
        last_msgs, _ = await service.get_chat_messages(db, chat_id, limit=1)
        if last_msgs and last_msgs[0].role.value == "user" and last_msgs[0].content == body.content:
            user_msg = last_msgs[0]
        else:
            user_msg = await service.save_message(db, chat_id, "user", body.content)

    is_admin = user.get("role") == "admin" if user else False
    tier = get_user_tier(user)

    # Get user display name and language for system prompt
    if user:
        user_result = await db.execute(select(User).where(User.id == user["id"]))
        user_obj = user_result.scalar_one_or_none()
        language = body.language or (user_obj.language if user_obj else None) or "ru"
        user_name = getattr(chat, 'persona_name', None) or (user_obj.display_name if user_obj else None)
        user_description = getattr(chat, 'persona_description', None)
    else:
        language = body.language or "en"
        user_name = None
        user_description = None

    # Build context (respect tier limits)
    tier_ctx_limit = get_tier_limits(tier)["max_context_messages"]
    messages = await service.build_conversation_messages(
        db, chat_id, character, user_name=user_name, user_description=user_description,
        language=language, context_limit=body.context_limit,
        max_context_messages=tier_ctx_limit,
        site_mode=settings.site_mode,
    )

    # For "continue": add instruction to continue from where the model left off
    if body.is_continue:
        messages.append(LLMMessage(role="user", content="Continue writing exactly from where you stopped. Do not repeat anything already written. Pick up mid-sentence if needed."))

    # Resolve provider and model ID
    PROVIDER_MODELS = {
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

    requested_max_tokens = body.max_tokens if body.max_tokens is not None else (getattr(character, 'max_tokens', None) or 2048)
    capped_max_tokens = cap_max_tokens(requested_max_tokens, tier)

    base_config = {
        "temperature": body.temperature if body.temperature is not None else 0.7,
        "max_tokens": capped_max_tokens,
        "top_p": body.top_p if body.top_p is not None else 0.95,
        "top_k": body.top_k if body.top_k is not None else 0,
        "frequency_penalty": body.frequency_penalty if body.frequency_penalty is not None else (0.5 if content_rating == "nsfw" else 0.3),
        "presence_penalty": body.presence_penalty if body.presence_penalty is not None else 0.3,
        "content_rating": content_rating,
    }

    user_id_for_increment = user["id"] if user else None

    if is_auto:
        cost_mode = await get_cost_mode()
        tier_limits = get_tier_limits(tier)
        # Determine provider order based on cost_mode and tier
        if cost_mode == "economy":
            # Free providers only for everyone
            order_str = settings.auto_provider_order
        elif cost_mode == "balanced":
            # Paid for registered users, free for anon
            if tier_limits["allow_paid"]:
                order_str = settings.auto_provider_order_paid
            else:
                order_str = settings.auto_provider_order
        else:
            # quality mode: use paid_mode setting as before
            paid_mode = await _is_paid_mode(db)
            order_str = settings.auto_provider_order_paid if paid_mode else settings.auto_provider_order
        auto_order = [p.strip() for p in order_str.split(",") if p.strip()]

        async def event_stream():
            errors: list[str] = []
            for pname in auto_order:
                try:
                    prov = get_provider(pname)
                except ValueError:
                    continue  # provider not configured
                use_flex = cost_mode != "economy" and pname == "groq"
                config = LLMConfig(model="", use_flex=use_flex, **base_config)
                full_response: list[str] = []
                buffered: list[str] = []
                buffer_flushed = False
                is_refusal = False
                try:
                    async for chunk in prov.generate_stream(messages, config):
                        full_response.append(chunk)
                        if not buffer_flushed:
                            buffered.append(chunk)
                            buf_text = "".join(buffered)
                            if len(buf_text) >= 200:
                                # Check buffered text for refusal
                                if _is_refusal_response(buf_text):
                                    is_refusal = True
                                    break
                                # Flush buffer
                                for b in buffered:
                                    yield f"data: {json.dumps({'type': 'token', 'content': b})}\n\n"
                                buffer_flushed = True
                        else:
                            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

                    if is_refusal:
                        actual_m = getattr(prov, 'last_model_used', '') or ''
                        errors.append(f"{pname}:{actual_m}: content refusal")
                        continue

                    # Check short responses that finished before buffer flush
                    complete_text = "".join(full_response)
                    if not buffer_flushed:
                        if _is_refusal_response(complete_text):
                            actual_m = getattr(prov, 'last_model_used', '') or ''
                            errors.append(f"{pname}:{actual_m}: content refusal")
                            continue
                        # Flush remaining buffer
                        for b in buffered:
                            yield f"data: {json.dumps({'type': 'token', 'content': b})}\n\n"

                    actual_model = f"{pname}:{getattr(prov, 'last_model_used', '') or ''}"
                    est_prompt = _estimate_prompt_tokens(messages)
                    est_completion = len(complete_text) // 4
                    truncated = est_completion >= capped_max_tokens * 0.85

                    if continue_msg_id:
                        # Append to existing assistant message
                        await _append_to_message(db, continue_msg_id, complete_text, actual_model, est_prompt, est_completion)
                        saved_msg_id = continue_msg_id
                    else:
                        saved_msg = await service.save_message(
                            db, chat_id, "assistant", complete_text, model_used=actual_model,
                            prompt_tokens=est_prompt, completion_tokens=est_completion,
                        )
                        saved_msg_id = saved_msg.id
                    await service.increment_message_count(character.id, language, user_id_for_increment)
                    _asyncio.create_task(maybe_summarize(chat_id))
                    done_data = {'type': 'done', 'message_id': saved_msg_id, 'user_message_id': user_msg.id, 'model_used': actual_model, 'truncated': truncated}
                    if settings.is_fiction_mode:
                        choices = _parse_choices(complete_text)
                        if choices:
                            done_data['choices'] = choices
                    if anon_session_id and anon_remaining is not None:
                        done_data['anon_messages_left'] = anon_remaining - 1
                    yield f"data: {json.dumps(done_data)}\n\n"
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
            buffered: list[str] = []
            buffer_flushed = False
            is_refusal = False
            try:
                async for chunk in provider.generate_stream(messages, config):
                    full_response.append(chunk)
                    if not buffer_flushed:
                        buffered.append(chunk)
                        buf_text = "".join(buffered)
                        if len(buf_text) >= 200:
                            if _is_refusal_response(buf_text):
                                is_refusal = True
                                break
                            for b in buffered:
                                yield f"data: {json.dumps({'type': 'token', 'content': b})}\n\n"
                            buffer_flushed = True
                    else:
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

                complete_text = "".join(full_response)
                if not buffer_flushed and not is_refusal:
                    if _is_refusal_response(complete_text):
                        is_refusal = True

                if is_refusal:
                    # Try auto-fallback on refusal (use paid order if paid mode)
                    paid = await _is_paid_mode(db)
                    fb_str = settings.auto_provider_order_paid if paid else settings.auto_provider_order
                    fallback_order = [p.strip() for p in fb_str.split(",") if p.strip() and p.strip() != provider_name]
                    for fb_name in fallback_order:
                        try:
                            fb_prov = get_provider(fb_name)
                        except ValueError:
                            continue
                        fb_config = LLMConfig(model="", **base_config)
                        try:
                            fb_response: list[str] = []
                            async for chunk in fb_prov.generate_stream(messages, fb_config):
                                fb_response.append(chunk)
                                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
                            fb_text = "".join(fb_response)
                            if _is_refusal_response(fb_text):
                                continue
                            actual_model = f"{fb_name}:{getattr(fb_prov, 'last_model_used', '') or ''}"
                            est_prompt = _estimate_prompt_tokens(messages)
                            est_completion = len(fb_text) // 4
                            fb_truncated = est_completion >= capped_max_tokens * 0.85
                            if continue_msg_id:
                                await _append_to_message(db, continue_msg_id, fb_text, actual_model, est_prompt, est_completion)
                                fb_saved_id = continue_msg_id
                            else:
                                saved_msg = await service.save_message(
                                    db, chat_id, "assistant", fb_text, model_used=actual_model,
                                    prompt_tokens=est_prompt, completion_tokens=est_completion,
                                )
                                fb_saved_id = saved_msg.id
                            await service.increment_message_count(character.id, language, user_id_for_increment)
                            _asyncio.create_task(maybe_summarize(chat_id))
                            done_data = {'type': 'done', 'message_id': fb_saved_id, 'user_message_id': user_msg.id, 'model_used': actual_model, 'truncated': fb_truncated}
                            if settings.is_fiction_mode:
                                fb_choices = _parse_choices(fb_text)
                                if fb_choices:
                                    done_data['choices'] = fb_choices
                            if anon_session_id and anon_remaining is not None:
                                done_data['anon_messages_left'] = anon_remaining - 1
                            yield f"data: {json.dumps(done_data)}\n\n"
                            return
                        except Exception:
                            continue
                    # All fallbacks failed or refused too
                    yield f"data: {json.dumps({'type': 'error', 'content': 'Модель отказала в генерации. Попробуйте другую модель.', 'user_message_id': user_msg.id})}\n\n"
                    return

                if not buffer_flushed:
                    for b in buffered:
                        yield f"data: {json.dumps({'type': 'token', 'content': b})}\n\n"

                actual_model = f"{provider_name}:{getattr(provider, 'last_model_used', model_id) or model_id}"
                est_prompt = _estimate_prompt_tokens(messages)
                est_completion = len(complete_text) // 4
                truncated = est_completion >= capped_max_tokens * 0.85
                if continue_msg_id:
                    await _append_to_message(db, continue_msg_id, complete_text, actual_model, est_prompt, est_completion)
                    saved_msg_id = continue_msg_id
                else:
                    saved_msg = await service.save_message(
                        db, chat_id, "assistant", complete_text, model_used=actual_model,
                        prompt_tokens=est_prompt, completion_tokens=est_completion,
                    )
                    saved_msg_id = saved_msg.id
                await service.increment_message_count(character.id, language, user_id_for_increment)
                _asyncio.create_task(maybe_summarize(chat_id))
                done_data = {'type': 'done', 'message_id': saved_msg_id, 'user_message_id': user_msg.id, 'model_used': actual_model, 'truncated': truncated}
                if settings.is_fiction_mode:
                    choices = _parse_choices(complete_text)
                    if choices:
                        done_data['choices'] = choices
                if anon_session_id and anon_remaining is not None:
                    done_data['anon_messages_left'] = anon_remaining - 1
                yield f"data: {json.dumps(done_data)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': _user_error(str(e), is_admin), 'user_message_id': user_msg.id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
