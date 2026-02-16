"""Daily counter growth — bump base_chat_count / base_like_count on public characters."""

import logging
import random

from sqlalchemy import text

from app.db.session import engine as db_engine

logger = logging.getLogger("autonomous")


async def grow_counters():
    """Increment base counters for all public characters."""
    try:
        async with db_engine.begin() as conn:
            # Get all public characters with their current base counts
            result = await conn.execute(
                text("""
                    SELECT id, base_chat_count, base_like_count
                    FROM characters
                    WHERE is_public = true
                """)
            )
            rows = result.fetchall()

            if not rows:
                logger.info("No public characters to update")
                return

            updated = 0
            for row in rows:
                char_id = row[0]
                base_chat = row[1] or {}
                base_like = row[2] or {}

                # Bump each language
                new_chat = {}
                new_like = {}
                for lang in ("ru", "en", "es"):
                    new_chat[lang] = (base_chat.get(lang) or 0) + random.randint(3, 15)
                    new_like[lang] = (base_like.get(lang) or 0) + random.randint(1, 5)

                import json
                await conn.execute(
                    text("""
                        UPDATE characters
                        SET base_chat_count = CAST(:chat AS jsonb),
                            base_like_count = CAST(:like AS jsonb)
                        WHERE id = :id
                    """),
                    {
                        "id": char_id,
                        "chat": json.dumps(new_chat),
                        "like": json.dumps(new_like),
                    },
                )
                updated += 1

            logger.info("Counter growth: updated %d characters", updated)

    except Exception:
        logger.exception("Counter growth failed")
        raise
