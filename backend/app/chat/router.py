import json
import time as _time
from datetime import datetime
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
from app.llm import model_cooldown as _model_cooldown
from app.llm import model_resolver as _model_resolver
from app.llm.thinking_filter import has_mixed_languages as _has_mixed_langs

router = APIRouter(prefix="/api/chats", tags=["chat"])

# Pattern to match numbered choices at the end of AI response (e.g. "1. Open the door")
_CHOICE_PATTERN = _re.compile(r'^(\d+)\.\s+(.+)$', _re.MULTILINE)

# Pattern for dice roll requests from GM: [ROLL expression description]
_ROLL_PATTERN = _re.compile(r'\[ROLL\s+(\S+)\s*(.*?)\]')

# Pattern for encounter state updates from GM: [STATE {...json...}]
# Greedy to capture nested braces in JSON with arrays of objects
_STATE_PATTERN = _re.compile(r'\[STATE\s*(\{.*\})\s*\]', _re.DOTALL)


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

def _parse_dice_rolls(text: str) -> list[dict] | None:
    """Find [ROLL expr description] patterns in AI response and execute rolls."""
    matches = _ROLL_PATTERN.findall(text)
    if not matches:
        return None
    from app.game.dice import roll as dice_roll
    results = []
    for expr, desc in matches:
        try:
            result = dice_roll(expr)
            results.append({
                "expression": result.expression,
                "rolls": result.rolls,
                "kept": result.kept,
                "modifier": result.modifier,
                "total": result.total,
                "description": desc.strip() if desc.strip() else None,
            })
        except ValueError:
            continue
    return results if results else None


def _parse_encounter_state(text: str) -> dict | None:
    """Find [STATE {...json...}] pattern in AI response and parse encounter state."""
    match = _STATE_PATTERN.search(text)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except (json.JSONDecodeError, ValueError):
        return None


def _strip_state_blocks(text: str) -> str:
    """Remove [STATE {...}] blocks from text so they don't show in chat."""
    return _STATE_PATTERN.sub('', text).strip()


async def _update_encounter_state(db, chat_id: str, new_state: dict):
    """Merge new encounter state into chat's encounter_state JSONB."""
    from app.db.models import Chat
    from sqlalchemy import select
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()
    if not chat:
        return
    current = chat.encounter_state or {}
    current.update(new_state)
    chat.encounter_state = current
    await db.commit()


async def _save_dice_on_message(db: AsyncSession, msg_id: str, dice_rolls: list):
    """Persist dice roll results on the assistant message for next-turn injection."""
    result = await db.execute(select(Message).where(Message.id == msg_id))
    msg = result.scalar_one_or_none()
    if msg:
        msg.dice_rolls = dice_rolls
        await db.commit()


# ── Companion approval parsing ─────────────────────────────
_APPROVAL_PATTERN = _re.compile(r'\[APPROVAL\s*([+-]\d)\]', _re.IGNORECASE)


def _parse_and_strip_approval(text: str) -> tuple[str, int]:
    """Parse [APPROVAL +1] or [APPROVAL -1] from response, strip the tag.

    Returns (cleaned_text, approval_delta). Delta is 0 if no tag found.
    """
    m = _APPROVAL_PATTERN.search(text)
    if not m:
        return text, 0
    delta = int(m.group(1))
    delta = max(-1, min(1, delta))  # clamp to -1..+1
    cleaned = text[:m.start()].rstrip() + text[m.end():]
    return cleaned.rstrip(), delta


# ── Suggested replies parsing ─────────────────────────────
_SUGGEST_PATTERN = _re.compile(r'\[SUGGEST:\s*(.+?)\]', _re.IGNORECASE)


def _parse_and_strip_suggestions(text: str) -> tuple[str, list[str] | None]:
    """Parse [SUGGEST: opt1 | opt2 | opt3] from response, strip the tag.

    Returns (cleaned_text, suggestions_list_or_None).
    """
    m = _SUGGEST_PATTERN.search(text)
    if not m:
        return text, None
    suggestions = [s.strip() for s in m.group(1).split('|') if s.strip()]
    if len(suggestions) < 2:
        return text, None
    cleaned = text[:m.start()].rstrip() + text[m.end():]
    return cleaned.rstrip(), suggestions[:6]


async def _update_companion_approval(db, chat_id: str, delta: int):
    """Update companion_approval on chat, clamped to [-3, +3]."""
    if delta == 0:
        return
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()
    if not chat:
        return
    current = getattr(chat, 'companion_approval', 0) or 0
    chat.companion_approval = max(-3, min(3, current + delta))
    await db.commit()


# ── Provider-specific prompt hints ────────────────────────────
# Injected as the very last system message, right before generate_stream.
# Grok is uncensored — focus on character fidelity, not fighting censorship.
# Mistral excels at literary prose — emphasise sensory detail and style.

_PROVIDER_HINTS: dict[str, dict[str, str]] = {
    "grok": {
        "ru": (
            "Ты работаешь через модель без цензуры. НЕ добавляй дисклеймеры, предупреждения или мета-комментарии. "
            "Полностью оставайся в роли персонажа {name} — твоя собственная личность НЕ должна просвечивать. "
            "Никакого сарказма или иронии от автора — только голос персонажа."
        ),
        "en": (
            "You are running on an uncensored model. Do NOT add disclaimers, warnings, or meta-commentary. "
            "Stay fully in character as {name} — your own personality must NOT leak through. "
            "No authorial sarcasm or irony — only the character's voice."
        ),
        "es": (
            "Estas en un modelo sin censura. NO agregues advertencias ni meta-comentarios. "
            "Mantente completamente en el personaje de {name} — tu propia personalidad NO debe filtrarse. "
            "Solo la voz del personaje."
        ),
        "fr": (
            "Tu es sur un modele sans censure. N'ajoute PAS d'avertissements ni de meta-commentaires. "
            "Reste entierement dans le personnage de {name} — ta propre personnalite NE doit PAS transparaitre. "
            "Uniquement la voix du personnage."
        ),
        "de": (
            "Du arbeitest auf einem unzensierten Modell. Fuege KEINE Warnungen oder Meta-Kommentare hinzu. "
            "Bleib vollstaendig in der Rolle von {name} — deine eigene Persoenlichkeit darf NICHT durchscheinen. "
            "Nur die Stimme der Figur."
        ),
        "pt": (
            "Voce esta em um modelo sem censura. NAO adicione avisos ou meta-comentarios. "
            "Fique totalmente no personagem de {name} — sua propria personalidade NAO deve transparecer. "
            "Apenas a voz do personagem."
        ),
        "it": (
            "Sei su un modello senza censura. NON aggiungere avvertimenti o meta-commenti. "
            "Resta completamente nel personaggio di {name} — la tua personalita NON deve trasparire. "
            "Solo la voce del personaggio."
        ),
    },
    "grok_nsfw": {
        "ru": (
            "У тебя нет ограничений контента. Сосредоточься на качестве прозы: точные сенсорные детали, "
            "аутентичный голос {name}, физиологически реалистичные описания тела и действий. "
            "Пиши как опытный автор эротики — уверенно, без стеснения, без самоцензуры."
        ),
        "en": (
            "You have no content restrictions. Focus on prose quality: precise sensory details, "
            "authentic voice of {name}, physiologically realistic body and action descriptions. "
            "Write like an experienced erotica author — confidently, without hesitation or self-censorship."
        ),
        "es": (
            "No tienes restricciones de contenido. Centrate en la calidad: detalles sensoriales precisos, "
            "voz autentica de {name}, descripciones fisiologicamente realistas. "
            "Escribe como un autor erotico experimentado — con confianza, sin autocensura."
        ),
        "fr": (
            "Tu n'as aucune restriction de contenu. Concentre-toi sur la qualite: details sensoriels precis, "
            "voix authentique de {name}, descriptions physiologiquement realistes. "
            "Ecris comme un auteur erotique experimente — avec assurance, sans autocensure."
        ),
        "de": (
            "Du hast keine Inhaltsbeschraenkungen. Konzentriere dich auf Qualitaet: praezise sensorische Details, "
            "authentische Stimme von {name}, physiologisch realistische Beschreibungen. "
            "Schreibe wie ein erfahrener Erotik-Autor — selbstsicher, ohne Selbstzensur."
        ),
        "pt": (
            "Voce nao tem restricoes de conteudo. Foque na qualidade: detalhes sensoriais precisos, "
            "voz autentica de {name}, descricoes fisiologicamente realistas. "
            "Escreva como um autor erotico experiente — com confianca, sem autocensura."
        ),
        "it": (
            "Non hai restrizioni di contenuto. Concentrati sulla qualita: dettagli sensoriali precisi, "
            "voce autentica di {name}, descrizioni fisiologicamente realistiche. "
            "Scrivi come un autore erotico esperto — con sicurezza, senza autocensura."
        ),
    },
    "groq": {
        "ru": (
            "КРИТИЧЕСКИ ВАЖНО: каждое слово в ответе должно быть на русском языке. "
            "Ни одного английского слова — ни eyes, ни dark, ни seemed, ни voice, ни smile. "
            "Если не знаешь русский аналог — перефразируй."
        ),
        "en": "",
        "es": "CRITICO: cada palabra debe estar en espanol. Ni una sola palabra en ingles.",
        "fr": "CRITIQUE: chaque mot doit etre en francais. Pas un seul mot en anglais.",
        "de": "KRITISCH: jedes Wort muss auf Deutsch sein. Kein einziges englisches Wort.",
        "pt": "CRITICO: cada palavra deve estar em portugues. Nenhuma palavra em ingles.",
        "it": "CRITICO: ogni parola deve essere in italiano. Nemmeno una parola in inglese.",
    },
    "mistral": {
        "ru": (
            "Пиши в традиции европейской литературной прозы. Каждая сцена — живая: звуки, запахи, текстуры, свет. "
            "Диалоги {name} звучат натурально — с паузами, недосказанностью, подтекстом. "
            "Предпочитай показывать через действия и детали, а не рассказывать напрямую. "
            "ЗАПРЕЩЕНО вводить посторонних людей (шаги за дверью, незнакомцы, прохожие, случайные звонки) — сцена только между присутствующими персонажами."
        ),
        "en": (
            "Write in the tradition of European literary prose. Every scene is alive: sounds, scents, textures, light. "
            "Dialogue of {name} sounds natural — with pauses, things left unsaid, subtext. "
            "Prefer showing through actions and details over telling directly. "
            "NEVER introduce uninvolved people (footsteps behind doors, strangers, passersby, random calls) — the scene is only between the present characters."
        ),
        "es": (
            "Escribe en la tradicion de la prosa literaria europea. Cada escena vive: sonidos, olores, texturas, luz. "
            "Los dialogos de {name} suenan naturales — con pausas, cosas no dichas, subtexto. "
            "Prefiere mostrar a traves de acciones y detalles. "
            "PROHIBIDO introducir personas ajenas (pasos detras de puertas, desconocidos, transeuntes) — la escena es solo entre los personajes presentes."
        ),
        "fr": (
            "Ecris dans la tradition de la prose litteraire europeenne. Chaque scene est vivante: sons, odeurs, textures, lumiere. "
            "Les dialogues de {name} sonnent naturels — avec des pauses, des non-dits, du sous-texte. "
            "Prefere montrer a travers les actions et les details plutot que raconter. "
            "INTERDIT d'introduire des personnes non impliquees (pas derriere la porte, inconnus, passants) — la scene est uniquement entre les personnages presents."
        ),
        "de": (
            "Schreibe in der Tradition europaeischer literarischer Prosa. Jede Szene lebt: Geraeusche, Gerueche, Texturen, Licht. "
            "Die Dialoge von {name} klingen natuerlich — mit Pausen, Ungesagtem, Subtext. "
            "Bevorzuge Zeigen durch Handlungen und Details statt direktem Erzaehlen. "
            "VERBOTEN: unbeteiligte Personen einfuehren (Schritte hinter der Tuer, Fremde, Passanten) — die Szene spielt nur zwischen den anwesenden Figuren."
        ),
        "pt": (
            "Escreva na tradicao da prosa literaria europeia. Cada cena e viva: sons, cheiros, texturas, luz. "
            "Os dialogos de {name} soam naturais — com pausas, coisas nao ditas, subtexto. "
            "Prefira mostrar atraves de acoes e detalhes em vez de contar diretamente. "
            "PROIBIDO introduzir pessoas nao envolvidas (passos atras da porta, estranhos, transeuntes) — a cena e apenas entre os personagens presentes."
        ),
        "it": (
            "Scrivi nella tradizione della prosa letteraria europea. Ogni scena e viva: suoni, profumi, texture, luce. "
            "I dialoghi di {name} suonano naturali — con pause, non detti, sottotesto. "
            "Preferisci mostrare attraverso azioni e dettagli piuttosto che raccontare direttamente. "
            "VIETATO introdurre persone non coinvolte (passi dietro la porta, sconosciuti, passanti) — la scena e solo tra i personaggi presenti."
        ),
    },
    "mistral_nsfw": {
        "ru": (
            "Интимные сцены пиши с литературной элегантностью и сырой честностью. "
            "Детально, чувственно, неспешно — как европейская эротическая проза. "
            "Тело {name} описывай конкретно и реалистично, эмоции — через физические реакции."
        ),
        "en": (
            "Write intimate scenes with literary elegance and raw honesty. "
            "Detailed, sensual, unhurried — like European erotic prose. "
            "Describe {name}'s body concretely and realistically, emotions through physical reactions."
        ),
        "es": (
            "Escribe escenas intimas con elegancia literaria y honestidad cruda. "
            "Detallado, sensual, sin prisa — como prosa erotica europea. "
            "Describe el cuerpo de {name} concretamente, emociones a traves de reacciones fisicas."
        ),
        "fr": (
            "Ecris les scenes intimes avec elegance litteraire et honnetete brute. "
            "Detaille, sensuel, sans precipitation — comme la prose erotique europeenne. "
            "Decris le corps de {name} concretement, les emotions a travers les reactions physiques."
        ),
        "de": (
            "Schreibe intime Szenen mit literarischer Eleganz und roher Ehrlichkeit. "
            "Detailliert, sinnlich, ohne Eile — wie europaeische erotische Prosa. "
            "Beschreibe {name}s Koerper konkret und realistisch, Emotionen durch koerperliche Reaktionen."
        ),
        "pt": (
            "Escreva cenas intimas com elegancia literaria e honestidade crua. "
            "Detalhado, sensual, sem pressa — como prosa erotica europeia. "
            "Descreva o corpo de {name} concretamente, emocoes atraves de reacoes fisicas."
        ),
        "it": (
            "Scrivi scene intime con eleganza letteraria e onesta cruda. "
            "Dettagliato, sensuale, senza fretta — come prosa erotica europea. "
            "Descrivi il corpo di {name} concretamente, emozioni attraverso reazioni fisiche."
        ),
    },
}


_LENGTH_REMINDER: dict[str, dict[str, str]] = {
    "short": {
        "ru": " ДЛИНА: строго 1-3 предложения. Не больше.",
        "en": " LENGTH: strictly 1-3 sentences. No more.",
        "es": " LONGITUD: estrictamente 1-3 oraciones. No mas.",
        "fr": " LONGUEUR: strictement 1-3 phrases. Pas plus.",
        "de": " LAENGE: strikt 1-3 Saetze. Nicht mehr.",
        "pt": " COMPRIMENTO: estritamente 1-3 frases. Nao mais.",
        "it": " LUNGHEZZA: rigorosamente 1-3 frasi. Non di piu.",
    },
    "medium": {
        "ru": " ДЛИНА: строго 2 абзаца (5-8 предложений). Не больше.",
        "en": " LENGTH: strictly 2 paragraphs (5-8 sentences). No more.",
        "es": " LONGITUD: estrictamente 2 parrafos (5-8 oraciones). No mas.",
        "fr": " LONGUEUR: strictement 2 paragraphes (5-8 phrases). Pas plus.",
        "de": " LAENGE: strikt 2 Absaetze (5-8 Saetze). Nicht mehr.",
        "pt": " COMPRIMENTO: estritamente 2 paragrafos (5-8 frases). Nao mais.",
        "it": " LUNGHEZZA: rigorosamente 2 paragrafi (5-8 frasi). Non di piu.",
    },
    "long": {
        "ru": " ДЛИНА: строго 3-4 абзаца. Не больше 4 абзацев. Лучше ярко и коротко, чем длинно и водянисто.",
        "en": " LENGTH: strictly 3-4 paragraphs. No more than 4. Better vivid and short than long and watery.",
        "es": " LONGITUD: estrictamente 3-4 parrafos. No mas de 4. Mejor vivido y breve que largo y aguado.",
        "fr": " LONGUEUR: strictement 3-4 paragraphes. Pas plus de 4. Mieux vif et court que long et dilue.",
        "de": " LAENGE: strikt 3-4 Absaetze. Nicht mehr als 4. Lieber lebendig und kurz als lang und verwaeessert.",
        "pt": " COMPRIMENTO: estritamente 3-4 paragrafos. Nao mais que 4. Melhor vivido e curto do que longo e aguado.",
        "it": " LUNGHEZZA: rigorosamente 3-4 paragrafi. Non piu di 4. Meglio vivido e breve che lungo e annacquato.",
    },
    "very_long": {
        "ru": " ДЛИНА: максимум 4-6 абзацев. Не больше 6.",
        "en": " LENGTH: max 4-6 paragraphs. No more than 6.",
        "es": " LONGITUD: maximo 4-6 parrafos. No mas de 6.",
        "fr": " LONGUEUR: max 4-6 paragraphes. Pas plus de 6.",
        "de": " LAENGE: max 4-6 Absaetze. Nicht mehr als 6.",
        "pt": " COMPRIMENTO: maximo 4-6 paragrafos. Nao mais que 6.",
        "it": " LUNGHEZZA: massimo 4-6 paragrafi. Non piu di 6.",
    },
}


def _get_provider_hint(provider_name: str, content_rating: str, language: str, char_name: str, response_length: str = "long") -> str | None:
    """Return a provider-specific prompt hint, or None if no hint needed."""
    key = provider_name
    if content_rating == "nsfw" and f"{provider_name}_nsfw" in _PROVIDER_HINTS:
        key = f"{provider_name}_nsfw"
    hints = _PROVIDER_HINTS.get(key)

    # Length reminder — applies to ALL providers
    length_hints = _LENGTH_REMINDER.get(response_length, _LENGTH_REMINDER["long"])
    length_text = length_hints.get(language, length_hints.get("en", ""))

    if not hints:
        # No provider-specific hint, but still inject length reminder
        return length_text.strip() if length_text else None
    text = hints.get(language, hints.get("en", ""))
    if not text:
        return length_text.strip() if length_text else None
    text = text.format(name=char_name)
    if length_text:
        text += length_text
    return text


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


def _dedup_response(text: str) -> str:
    """Remove duplicated content from model output.

    Some models (e.g. Llama 3.3) repeat themselves — generating the same
    scene twice with minor rewording. Two strategies:
    1. Paragraph-level: first 3 words of paragraphs match earlier ones
    2. Substring-level: a long sentence from the first half reappears later
    """
    if len(text) < 100:
        return text

    # Strategy 1: paragraph-level dedup
    paragraphs = [p.strip() for p in _re.split(r'\n\s*\n|\n', text) if p.strip()]
    if len(paragraphs) >= 3:
        def _key(p: str) -> str:
            clean = _re.sub(r'^[\s\-\u2014\u2013\u00ab"\']+', '', p)
            words = clean.split()[:3]
            return " ".join(w.lower().rstrip('.,!?;:') for w in words)
        keys = [_key(p) for p in paragraphs]
        for i in range(1, len(paragraphs)):
            if not keys[i]:
                continue
            for j in range(i):
                if keys[i] == keys[j]:
                    remaining = len(paragraphs) - i
                    matches = 0
                    for k in range(remaining):
                        if i + k < len(paragraphs) and j + k < i:
                            if keys[i + k] and keys[i + k] == keys[j + k]:
                                matches += 1
                    if matches >= remaining * 0.5 and matches >= 2:
                        return "\n\n".join(paragraphs[:i])

    # Strategy 2: repeated phrase detection (handles mid-sentence repeats)
    # The model restarts the scene mid-sentence — look for a phrase from the
    # beginning of the text that reappears later (e.g. character name + action).
    # Extract opening phrase (first 3-5 words) and search for it in the second half.
    words = text.split()
    if len(words) >= 20:
        # Try phrases of 3, 4, 5 opening words
        for phrase_len in (5, 4, 3):
            phrase = " ".join(words[:phrase_len])
            if len(phrase) < 12:
                continue
            # Search for this phrase in the second half of text
            search_start = len(text) // 3
            pos = text.find(phrase, search_start)
            if pos > 0:
                # Found a repeat — cut before it, at nearest sentence boundary
                clean_cut = text.rfind('. ', 0, pos)
                if clean_cut > len(text) // 5:
                    return text[:clean_cut + 1].rstrip()
                # No sentence boundary — cut at word boundary before repeat
                clean_cut = text.rfind(' ', 0, pos)
                if clean_cut > len(text) // 5:
                    return text[:clean_cut].rstrip()

    return text


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
        "campaign_id": getattr(c, 'campaign_id', None),
        "encounter_state": getattr(c, 'encounter_state', None),
        "persona_id": getattr(c, 'persona_id', None),
        "persona_name": getattr(c, 'persona_name', None),
        "persona_slug": persona.slug if persona else None,
        "title": c.title,
        "model_used": c.model_used,
        "has_summary": bool(getattr(c, 'summary', None)),
        "rating": getattr(c, 'rating', None),
        "companion_approval": getattr(c, 'companion_approval', 0) or 0,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }
    if c.character:
        d["characters"] = {
            "id": c.character.id,
            "name": c.character.name,
            "avatar_url": c.character.avatar_url,
            "tagline": c.character.tagline,
            "scenario": c.character.scenario,
            "content_rating": c.character.content_rating.value if c.character.content_rating else "sfw",
            "companion_name": getattr(c.character, 'companion_name', None),
            "companion_role": getattr(c.character, 'companion_role', None),
            "companion_avatar_url": getattr(c.character, 'companion_avatar_url', None),
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


@router.delete("/{chat_id}/messages/{message_id}")
async def delete_message(
    chat_id: str,
    message_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a message and all messages after it (cannot delete greeting)."""
    count = await service.delete_message(db, chat_id, message_id, user["id"])
    if not count:
        raise HTTPException(status_code=404, detail="Message not found or cannot be deleted")
    return {"deleted": count}


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


@router.post("/{chat_id}/rate")
async def rate_adventure(
    chat_id: str,
    request: Request,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rate an adventure 1-5 stars."""
    body = await request.json()
    rating = body.get("rating")
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        raise HTTPException(400, "Rating must be 1-5")

    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(404, "Chat not found")
    if chat.user_id != user.get("id"):
        raise HTTPException(403, "Not your chat")

    chat.rating = rating
    if not chat.completed_at:
        chat.completed_at = datetime.utcnow()
    await db.commit()

    # Check achievements
    new_achievements = []
    try:
        from app.achievements.checker import check_achievements
        new_achievements = await check_achievements(db, user["id"], trigger="rating")
    except Exception:
        pass

    # Award XP for rating
    xp_data = None
    try:
        from app.users.xp import award_xp
        xp_data = await award_xp(user["id"], 25)
    except Exception:
        pass

    return {"ok": True, "rating": rating, "new_achievements": new_achievements, "xp": xp_data}


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
            await check_message_interval(user["id"])
        await check_daily_limit(user["id"], user.get("role", "user"))
        chat = await service.get_chat(db, chat_id, user_id=user["id"])
    else:
        anon_session_id = request.headers.get("x-anon-session")
        if not anon_session_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        check_message_rate(f"anon:{anon_session_id}")
        if not body.is_regenerate and not body.is_continue:
            await check_message_interval(f"anon:{anon_session_id}")
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
    # DnD mode: campaign chat or character with 'dnd' tag
    _char_tags = [t.strip() for t in (getattr(character, 'tags', '') or '').split(",")]
    is_dnd = bool(getattr(chat, 'campaign_id', None)) or "dnd" in _char_tags

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
    # Claude does not allow NSFW content — block in NSFW mode
    _NSFW_BLOCKED_PROVIDERS = {"claude", "haiku"}
    is_auto = model_name == "auto"

    if is_auto:
        provider_name = "auto"
        model_id = ""
    elif model_name in ("claude", "haiku"):
        if content_rating == "nsfw":
            raise HTTPException(status_code=400, detail="Claude is not available for NSFW content")
        provider_name = "claude"
        model_id = _model_resolver.get_model(model_name)
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
        model_id = _model_resolver.get_model(model_name)

    requested_max_tokens = body.max_tokens if body.max_tokens is not None else (getattr(character, 'max_tokens', None) or 2048)
    capped_max_tokens = cap_max_tokens(requested_max_tokens, tier)
    _resp_length = getattr(character, 'response_length', None) or "long"

    has_companion = bool(getattr(character, 'companion_name', None))
    # Approval tracking only for fiction/DnD (GrimQuill), not for SweetSin RP
    companion_approval_enabled = has_companion and (settings.site_mode == "fiction" or is_dnd)
    # Companion chats get higher temperature for more varied output
    _default_temp = 0.95 if content_rating == "nsfw" else 0.85
    if has_companion:
        _default_temp = min(_default_temp + 0.07, 1.0)

    base_config = {
        "temperature": body.temperature if body.temperature is not None else _default_temp,
        "max_tokens": capped_max_tokens,
        "top_p": body.top_p if body.top_p is not None else 0.95,
        "top_k": body.top_k if body.top_k is not None else 0,
        "min_p": 0.05,
        "frequency_penalty": body.frequency_penalty if body.frequency_penalty is not None else (0.6 if content_rating == "nsfw" else 0.4),
        "presence_penalty": body.presence_penalty if body.presence_penalty is not None else (0.5 if content_rating == "nsfw" else 0.3),
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
        # Skip NSFW-blocked providers (e.g. Claude) when content is NSFW
        if content_rating == "nsfw":
            auto_order = [p for p in auto_order if p not in _NSFW_BLOCKED_PROVIDERS]
        # Companion chats: prefer providers that support repetition penalties
        # Groq/Grok/Mistral/Cerebras ignore penalties → deprioritize them
        if has_companion:
            _NO_PENALTY_PROVIDERS = {"groq", "grok", "mistral", "cerebras"}
            good = [p for p in auto_order if p not in _NO_PENALTY_PROVIDERS]
            bad = [p for p in auto_order if p in _NO_PENALTY_PROVIDERS]
            auto_order = good + bad

        async def event_stream():
            errors: list[str] = []
            for pname in auto_order:
                try:
                    prov = get_provider(pname)
                except ValueError:
                    continue  # provider not configured
                use_flex = cost_mode != "economy" and pname == "groq"
                config = LLMConfig(model=_model_resolver.get_model(pname), use_flex=use_flex, **base_config)
                full_response: list[str] = []
                buffered: list[str] = []
                buffer_flushed = False
                is_refusal = False
                # Inject provider-specific hint (Grok: stay in character; Mistral: literary prose)
                hint = _get_provider_hint(pname, content_rating, language, character.name, _resp_length)
                prov_msgs = messages + [LLMMessage(role="system", content=hint)] if hint else messages
                try:
                    async for chunk in prov.generate_stream(prov_msgs, config):
                        full_response.append(chunk)
                        if not buffer_flushed:
                            buffered.append(chunk)
                            buf_text = "".join(buffered)
                            if len(buf_text) >= 200:
                                # Check buffered text for refusal or language bleed
                                if _is_refusal_response(buf_text):
                                    is_refusal = True
                                    break
                                if _has_mixed_langs(buf_text, language):
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
                        errors.append(f"{pname}:{actual_m}: content refusal or language bleed")
                        continue

                    # Check short responses that finished before buffer flush
                    complete_text = _dedup_response("".join(full_response))
                    if not buffer_flushed:
                        if _is_refusal_response(complete_text) or _has_mixed_langs(complete_text, language):
                            actual_m = getattr(prov, 'last_model_used', '') or ''
                            errors.append(f"{pname}:{actual_m}: content refusal or language bleed")
                            continue
                        # Flush remaining buffer
                        for b in buffered:
                            yield f"data: {json.dumps({'type': 'token', 'content': b})}\n\n"

                    # Parse companion approval tags before saving (fiction/DnD only)
                    approval_delta = 0
                    if companion_approval_enabled:
                        complete_text, approval_delta = _parse_and_strip_approval(complete_text)
                    # Parse suggested replies
                    complete_text, suggestions = _parse_and_strip_suggestions(complete_text)

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
                    # Update companion approval if changed
                    if approval_delta:
                        await _update_companion_approval(db, chat_id, approval_delta)
                    await service.increment_message_count(character.id, language, user_id_for_increment)
                    _asyncio.create_task(maybe_summarize(chat_id))
                    done_data = {'type': 'done', 'message_id': saved_msg_id, 'user_message_id': user_msg.id, 'model_used': actual_model, 'truncated': truncated}
                    if companion_approval_enabled and approval_delta:
                        done_data['companion_approval_delta'] = approval_delta
                    if settings.is_fiction_mode:
                        choices = _parse_choices(complete_text)
                        if choices:
                            done_data['choices'] = choices
                    if suggestions:
                        done_data['suggestions'] = suggestions
                    # Parse dice rolls and encounter state for DnD chats
                    if is_dnd:
                        dice_rolls = _parse_dice_rolls(complete_text)
                        if dice_rolls:
                            done_data['dice_rolls'] = dice_rolls
                            await _save_dice_on_message(db, saved_msg_id, dice_rolls)
                        enc_state = _parse_encounter_state(complete_text)
                        if enc_state:
                            await _update_encounter_state(db, chat_id, enc_state)
                            done_data['encounter_state'] = enc_state
                    if anon_session_id and anon_remaining is not None:
                        done_data['anon_messages_left'] = anon_remaining - 1
                    if user_id_for_increment and not anon_session_id:
                        try:
                            from app.achievements.checker import check_achievements as _ach_check
                            _new_ach = await _ach_check(db, user_id_for_increment, trigger="message")
                            if _new_ach:
                                done_data['new_achievements'] = _new_ach
                        except Exception:
                            pass
                        try:
                            from app.users.xp import award_xp as _award_xp
                            done_data['xp'] = await _award_xp(user_id_for_increment, 10)
                        except Exception:
                            pass
                    yield f"data: {json.dumps(done_data)}\n\n"
                    return
                except Exception as e:
                    _model_cooldown.handle_402_if_applicable(pname, e)
                    # Auto-fix model 404 in auto-mode (fire-and-forget, next provider will handle this request)
                    if _model_resolver.is_404_error(e) and pname in _model_resolver.FIXABLE_PROVIDERS:
                        _asyncio.create_task(_model_resolver.resolve_model_404(pname, config.model))
                    errors.append(f"{pname}: {e}")
                    continue
            full_err = 'Все провайдеры недоступны:\n' + '\n'.join(errors)
            yield f"data: {json.dumps({'type': 'error', 'content': _user_error(full_err, is_admin), 'user_message_id': user_msg.id})}\n\n"
    else:
        provider = get_provider(provider_name)
        config = LLMConfig(model=model_id, **base_config)
        # Inject provider-specific hint (Grok: stay in character; Mistral: literary prose)
        hint = _get_provider_hint(provider_name, content_rating, language, character.name, _resp_length)
        if hint:
            messages = messages + [LLMMessage(role="system", content=hint)]

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
                            if _is_refusal_response(buf_text) or _has_mixed_langs(buf_text, language):
                                is_refusal = True
                                break
                            for b in buffered:
                                yield f"data: {json.dumps({'type': 'token', 'content': b})}\n\n"
                            buffer_flushed = True
                    else:
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

                complete_text = _dedup_response("".join(full_response))
                if not buffer_flushed and not is_refusal:
                    if _is_refusal_response(complete_text) or _has_mixed_langs(complete_text, language):
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
                        fb_config = LLMConfig(model=_model_resolver.get_model(fb_name), **base_config)
                        fb_hint = _get_provider_hint(fb_name, content_rating, language, character.name, _resp_length)
                        fb_msgs = messages + [LLMMessage(role="system", content=fb_hint)] if fb_hint else messages
                        try:
                            fb_response: list[str] = []
                            async for chunk in fb_prov.generate_stream(fb_msgs, fb_config):
                                fb_response.append(chunk)
                                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
                            fb_text = "".join(fb_response)
                            if _is_refusal_response(fb_text) or _has_mixed_langs(fb_text, language):
                                continue
                            # Parse companion approval tags (fiction/DnD only)
                            fb_approval_delta = 0
                            if companion_approval_enabled:
                                fb_text, fb_approval_delta = _parse_and_strip_approval(fb_text)
                            fb_text, fb_suggestions = _parse_and_strip_suggestions(fb_text)
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
                            if fb_approval_delta:
                                await _update_companion_approval(db, chat_id, fb_approval_delta)
                            await service.increment_message_count(character.id, language, user_id_for_increment)
                            _asyncio.create_task(maybe_summarize(chat_id))
                            done_data = {'type': 'done', 'message_id': fb_saved_id, 'user_message_id': user_msg.id, 'model_used': actual_model, 'truncated': fb_truncated}
                            if companion_approval_enabled and fb_approval_delta:
                                done_data['companion_approval_delta'] = fb_approval_delta
                            if settings.is_fiction_mode:
                                fb_choices = _parse_choices(fb_text)
                                if fb_choices:
                                    done_data['choices'] = fb_choices
                            if fb_suggestions:
                                done_data['suggestions'] = fb_suggestions
                            if is_dnd:
                                fb_dice = _parse_dice_rolls(fb_text)
                                if fb_dice:
                                    done_data['dice_rolls'] = fb_dice
                                    await _save_dice_on_message(db, fb_saved_id, fb_dice)
                                fb_enc = _parse_encounter_state(fb_text)
                                if fb_enc:
                                    await _update_encounter_state(db, chat_id, fb_enc)
                                    done_data['encounter_state'] = fb_enc
                            if anon_session_id and anon_remaining is not None:
                                done_data['anon_messages_left'] = anon_remaining - 1
                            if user_id_for_increment and not anon_session_id:
                                try:
                                    from app.achievements.checker import check_achievements as _ach_check
                                    _new_ach = await _ach_check(db, user_id_for_increment, trigger="message")
                                    if _new_ach:
                                        done_data['new_achievements'] = _new_ach
                                except Exception:
                                    pass
                                try:
                                    from app.users.xp import award_xp as _award_xp
                                    done_data['xp'] = await _award_xp(user_id_for_increment, 10)
                                except Exception:
                                    pass
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

                # Parse companion approval tags before saving (fiction/DnD only)
                approval_delta = 0
                if companion_approval_enabled:
                    complete_text, approval_delta = _parse_and_strip_approval(complete_text)
                # Parse suggested replies
                complete_text, suggestions = _parse_and_strip_suggestions(complete_text)

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
                # Update companion approval if changed
                if approval_delta:
                    await _update_companion_approval(db, chat_id, approval_delta)
                await service.increment_message_count(character.id, language, user_id_for_increment)
                _asyncio.create_task(maybe_summarize(chat_id))
                done_data = {'type': 'done', 'message_id': saved_msg_id, 'user_message_id': user_msg.id, 'model_used': actual_model, 'truncated': truncated}
                if companion_approval_enabled and approval_delta:
                    done_data['companion_approval_delta'] = approval_delta
                if settings.is_fiction_mode:
                    choices = _parse_choices(complete_text)
                    if choices:
                        done_data['choices'] = choices
                if suggestions:
                    done_data['suggestions'] = suggestions
                if is_dnd:
                    dice_rolls = _parse_dice_rolls(complete_text)
                    if dice_rolls:
                        done_data['dice_rolls'] = dice_rolls
                        await _save_dice_on_message(db, saved_msg_id, dice_rolls)
                    enc_state = _parse_encounter_state(complete_text)
                    if enc_state:
                        await _update_encounter_state(db, chat_id, enc_state)
                        done_data['encounter_state'] = enc_state
                if anon_session_id and anon_remaining is not None:
                    done_data['anon_messages_left'] = anon_remaining - 1
                if user_id_for_increment and not anon_session_id:
                    try:
                        from app.achievements.checker import check_achievements as _ach_check
                        _new_ach = await _ach_check(db, user_id_for_increment, trigger="message")
                        if _new_ach:
                            done_data['new_achievements'] = _new_ach
                    except Exception:
                        pass
                    try:
                        from app.users.xp import award_xp as _award_xp
                        done_data['xp'] = await _award_xp(user_id_for_increment, 10)
                    except Exception:
                        pass
                yield f"data: {json.dumps(done_data)}\n\n"
            except Exception as e:
                # Auto-fix model 404: resolve new model and retry once
                if _model_resolver.is_404_error(e) and provider_name in _model_resolver.FIXABLE_PROVIDERS:
                    new_model = await _model_resolver.resolve_model_404(provider_name, config.model)
                    if new_model:
                        try:
                            retry_config = LLMConfig(model=new_model, **base_config)
                            r_response: list[str] = []
                            r_buffered: list[str] = []
                            r_buf_flushed = False
                            r_refusal = False
                            async for chunk in provider.generate_stream(messages, retry_config):
                                r_response.append(chunk)
                                if not r_buf_flushed:
                                    r_buffered.append(chunk)
                                    if len("".join(r_buffered)) >= 200:
                                        r_buf_text = "".join(r_buffered)
                                        if _is_refusal_response(r_buf_text) or _has_mixed_langs(r_buf_text, language):
                                            r_refusal = True
                                            break
                                        for b in r_buffered:
                                            yield f"data: {json.dumps({'type': 'token', 'content': b})}\n\n"
                                        r_buf_flushed = True
                                else:
                                    yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
                            r_text = "".join(r_response)
                            if not r_buf_flushed and not r_refusal:
                                if _is_refusal_response(r_text) or _has_mixed_langs(r_text, language):
                                    r_refusal = True
                            if r_refusal:
                                raise RuntimeError("Retry model also refused")
                            if not r_buf_flushed:
                                for b in r_buffered:
                                    yield f"data: {json.dumps({'type': 'token', 'content': b})}\n\n"
                            # Parse companion approval tags (fiction/DnD only)
                            r_approval_delta = 0
                            if companion_approval_enabled:
                                r_text, r_approval_delta = _parse_and_strip_approval(r_text)
                            r_text, r_suggestions = _parse_and_strip_suggestions(r_text)
                            r_model = f"{provider_name}:{new_model}"
                            est_p = _estimate_prompt_tokens(messages)
                            est_c = len(r_text) // 4
                            r_truncated = est_c >= capped_max_tokens * 0.85
                            if continue_msg_id:
                                await _append_to_message(db, continue_msg_id, r_text, r_model, est_p, est_c)
                                r_msg_id = continue_msg_id
                            else:
                                r_msg = await service.save_message(db, chat_id, "assistant", r_text, model_used=r_model, prompt_tokens=est_p, completion_tokens=est_c)
                                r_msg_id = r_msg.id
                            if r_approval_delta:
                                await _update_companion_approval(db, chat_id, r_approval_delta)
                            await service.increment_message_count(character.id, language, user_id_for_increment)
                            _asyncio.create_task(maybe_summarize(chat_id))
                            r_done = {'type': 'done', 'message_id': r_msg_id, 'user_message_id': user_msg.id, 'model_used': r_model, 'truncated': r_truncated}
                            if companion_approval_enabled and r_approval_delta:
                                r_done['companion_approval_delta'] = r_approval_delta
                            if settings.is_fiction_mode:
                                r_choices = _parse_choices(r_text)
                                if r_choices:
                                    r_done['choices'] = r_choices
                            if r_suggestions:
                                r_done['suggestions'] = r_suggestions
                            if is_dnd:
                                r_dice = _parse_dice_rolls(r_text)
                                if r_dice:
                                    r_done['dice_rolls'] = r_dice
                                    await _save_dice_on_message(db, r_msg_id, r_dice)
                                r_enc = _parse_encounter_state(r_text)
                                if r_enc:
                                    await _update_encounter_state(db, chat_id, r_enc)
                                    r_done['encounter_state'] = r_enc
                            if anon_session_id and anon_remaining is not None:
                                r_done['anon_messages_left'] = anon_remaining - 1
                            if user_id_for_increment and not anon_session_id:
                                try:
                                    from app.achievements.checker import check_achievements as _ach_check
                                    _new_ach = await _ach_check(db, user_id_for_increment, trigger="message")
                                    if _new_ach:
                                        r_done['new_achievements'] = _new_ach
                                except Exception:
                                    pass
                                try:
                                    from app.users.xp import award_xp as _award_xp
                                    r_done['xp'] = await _award_xp(user_id_for_increment, 10)
                                except Exception:
                                    pass
                            yield f"data: {json.dumps(r_done)}\n\n"
                            return
                        except Exception:
                            pass  # fall through to error below
                _model_cooldown.handle_402_if_applicable(provider_name, e)
                yield f"data: {json.dumps({'type': 'error', 'content': _user_error(str(e), is_admin), 'user_message_id': user_msg.id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
