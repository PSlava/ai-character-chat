"""Daily counter growth — bump base_chat_count / base_like_count on public characters.

Growth rates are scaled by language preference affinity: characters popular
in a given language grow faster for that language's counter.
"""

import json
import logging

from sqlalchemy import text

from app.db.session import engine as db_engine

logger = logging.getLogger("autonomous")


async def grow_counters():
    """Increment base counters for all public characters with preference-aware growth."""
    try:
        async with db_engine.begin() as conn:
            result = await conn.execute(
                text("""
                    SELECT id, base_chat_count, base_like_count,
                           content_rating, structured_tags, tags
                    FROM characters
                    WHERE is_public = true
                """)
            )
            rows = result.fetchall()

            if not rows:
                logger.info("No public characters to update")
                return

            from app.characters.language_preferences import get_growth_increments

            updated = 0
            for row in rows:
                char_id = row[0]
                base_chat = row[1] or {}
                base_like = row[2] or {}
                rating = row[3] or ""
                structured_str = row[4] or ""
                free_tags = row[5] or ""

                structured = [t.strip() for t in structured_str.split(",") if t.strip()]

                # Detect setting from structured tags
                setting = ""
                for tag in structured:
                    if tag in ("fantasy", "sci_fi", "post_apocalyptic", "horror", "historical"):
                        setting = "fantasy"
                        break
                    if tag in ("modern", "school"):
                        setting = "modern"
                        break

                chat_inc, like_inc = get_growth_increments(
                    setting=setting,
                    rating=rating,
                    structured_tags=structured,
                    free_tags=free_tags,
                )

                new_chat = {}
                new_like = {}
                for lang in ("ru", "en", "es", "fr", "de", "pt", "it"):
                    new_chat[lang] = (base_chat.get(lang) or 0) + chat_inc[lang]
                    new_like[lang] = (base_like.get(lang) or 0) + like_inc[lang]

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
