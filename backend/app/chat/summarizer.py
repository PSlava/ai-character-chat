"""Auto-summarize older chat messages when context grows large.

Runs as fire-and-forget after each assistant response.
Uses cheap/fast LLM providers (groq → cerebras → openrouter).
"""
import asyncio
import logging

from sqlalchemy import select, func, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chat, Message
from app.db.session import async_session, engine as db_engine
from app.llm.base import LLMMessage, LLMConfig
from app.llm.registry import get_provider

logger = logging.getLogger("summarizer")

# Summarize when total messages exceed this threshold
SUMMARIZE_THRESHOLD = 40
# Keep the most recent N messages unsummarized (always in context)
KEEP_RECENT = 20
# Providers to try (fast + cheap)
_SUMMARY_PROVIDERS = ("groq", "cerebras", "openrouter")
_TIMEOUT = 30.0

_SUMMARY_PROMPT = """Summarize the following roleplay conversation concisely. Preserve:
- Key plot points and events
- Character relationships and dynamics
- Important decisions and agreements
- Emotional states and character development

Write in the same language as the conversation. Be concise (200-400 words max).
Do NOT add commentary — just the summary.

Conversation:
{conversation}"""


async def _generate_summary(messages_text: str) -> str | None:
    """Generate a summary via LLM."""
    prompt = _SUMMARY_PROMPT.format(conversation=messages_text)
    llm_messages = [
        LLMMessage(role="system", content="You are a concise summarizer of roleplay conversations."),
        LLMMessage(role="user", content=prompt),
    ]
    config = LLMConfig(model="", temperature=0.3, max_tokens=1024)

    for provider_name in _SUMMARY_PROVIDERS:
        try:
            provider = get_provider(provider_name)
        except ValueError:
            continue
        try:
            result = await asyncio.wait_for(
                provider.generate(llm_messages, config),
                timeout=_TIMEOUT,
            )
            result = result.strip()
            if result and len(result) > 20:
                return result
        except Exception as e:
            logger.warning("Summary via %s failed: %s", provider_name, str(e)[:100])
            continue
    return None


async def maybe_summarize(chat_id: str):
    """Check if chat needs summarization, and if so, summarize older messages.

    Must run in its own session since this is fire-and-forget.
    """
    try:
        async with async_session() as db:
            # Count messages
            count_result = await db.execute(
                select(func.count()).select_from(Message).where(Message.chat_id == chat_id)
            )
            total = count_result.scalar() or 0

            if total < SUMMARIZE_THRESHOLD:
                return

            # Get the chat
            chat_result = await db.execute(select(Chat).where(Chat.id == chat_id))
            chat = chat_result.scalar_one_or_none()
            if not chat:
                return

            # Get all messages ordered by time
            msgs_result = await db.execute(
                select(Message)
                .where(Message.chat_id == chat_id)
                .order_by(Message.created_at.asc())
            )
            all_msgs = list(msgs_result.scalars().all())

            if len(all_msgs) < SUMMARIZE_THRESHOLD:
                return

            # Messages to summarize: everything except the last KEEP_RECENT
            to_summarize = all_msgs[:-KEEP_RECENT]

            # If we already have a summary, only summarize new messages since then
            if chat.summary_up_to_id:
                start_idx = 0
                for i, m in enumerate(to_summarize):
                    if m.id == chat.summary_up_to_id:
                        start_idx = i + 1
                        break
                new_messages = to_summarize[start_idx:]
                if len(new_messages) < 10:
                    return  # Not enough new messages to re-summarize
            else:
                new_messages = to_summarize

            if not new_messages:
                return

            # Build text to summarize
            existing_summary = chat.summary or ""
            conversation_parts = []
            if existing_summary:
                conversation_parts.append(f"[Previous summary]\n{existing_summary}\n\n[New messages]")
            for m in new_messages:
                role_label = "User" if (m.role.value if hasattr(m.role, 'value') else m.role) == "user" else "Character"
                conversation_parts.append(f"{role_label}: {m.content[:500]}")  # truncate long messages

            conversation_text = "\n".join(conversation_parts)

            # Generate summary
            summary = await _generate_summary(conversation_text)
            if not summary:
                return

            # Update chat with new summary
            last_summarized_id = to_summarize[-1].id
            async with db_engine.begin() as conn:
                await conn.execute(
                    sa_text("UPDATE chats SET summary = :summary, summary_up_to_id = :up_to WHERE id = :cid"),
                    {"summary": summary, "up_to": last_summarized_id, "cid": chat_id},
                )
            logger.info("Summarized chat %s: %d messages → %d chars", chat_id[:8], len(new_messages), len(summary))

    except Exception as e:
        logger.warning("Summarization failed for chat %s: %s", chat_id[:8], str(e)[:200])
