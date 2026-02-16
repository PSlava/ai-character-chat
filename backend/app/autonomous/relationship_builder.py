"""Build relationships between characters based on shared tags — weekly task."""

import json
import logging
import uuid

from sqlalchemy import text

from app.db.session import engine as db_engine
from app.llm.base import LLMMessage, LLMConfig
from app.llm.registry import get_provider

logger = logging.getLogger("autonomous")

_PROVIDER_ORDER = ("groq", "cerebras", "openrouter")
_MAX_PAIRS = 20  # pairs per run
_MAX_RELATIONS_PER_CHAR = 3

# Predefined labels for relation types
_LABELS = {
    "rival": {"ru": "Соперник", "en": "Rival", "es": "Rival"},
    "ex": {"ru": "Бывший", "en": "Ex", "es": "Ex"},
    "friend": {"ru": "Друг", "en": "Friend", "es": "Amigo"},
    "sibling": {"ru": "Родственник", "en": "Sibling", "es": "Hermano"},
    "enemy": {"ru": "Враг", "en": "Enemy", "es": "Enemigo"},
    "lover": {"ru": "Возлюбленный", "en": "Lover", "es": "Amante"},
    "ally": {"ru": "Союзник", "en": "Ally", "es": "Aliado"},
}

_VALID_TYPES = set(_LABELS.keys())

_PROMPT = """Given these two AI roleplay characters, choose the most fitting relationship type between them.

Character A: {name_a}
- Tags: {tags_a}
- Personality (excerpt): {personality_a}

Character B: {name_b}
- Tags: {tags_b}
- Personality (excerpt): {personality_b}

Choose ONE relationship type from: rival, ex, friend, sibling, enemy, lover, ally

Reply with ONLY the relationship type (one word), nothing else."""


async def build_relationships() -> int:
    """Find character pairs with shared tags and create relationships. Returns count."""
    # Get existing relation counts per character
    async with db_engine.connect() as conn:
        existing = await conn.execute(text("""
            SELECT character_id, COUNT(*) as cnt
            FROM character_relations
            GROUP BY character_id
        """))
        relation_counts = {row[0]: row[1] for row in existing.fetchall()}

        # Get existing pairs to avoid duplicates
        existing_pairs = await conn.execute(text("""
            SELECT character_id, related_id FROM character_relations
        """))
        existing_set = {(row[0], row[1]) for row in existing_pairs.fetchall()}

        # Get public characters with tags
        chars_result = await conn.execute(text("""
            SELECT id, name, tags, structured_tags, personality
            FROM characters
            WHERE is_public = true AND tags != '' AND tags IS NOT NULL
            ORDER BY chat_count DESC
            LIMIT 100
        """))
        characters = chars_result.fetchall()

    if len(characters) < 2:
        logger.info("Not enough characters for relationships")
        return 0

    # Find pairs with shared tags (at least 2)
    candidates = []
    for i, a in enumerate(characters):
        if relation_counts.get(a.id, 0) >= _MAX_RELATIONS_PER_CHAR:
            continue
        tags_a = set(t.strip() for t in (a.tags or "").split(",") if t.strip())
        stags_a = set(t.strip() for t in (a.structured_tags or "").split(",") if t.strip())
        all_tags_a = tags_a | stags_a

        for b in characters[i + 1:]:
            if relation_counts.get(b.id, 0) >= _MAX_RELATIONS_PER_CHAR:
                continue
            if (a.id, b.id) in existing_set or (b.id, a.id) in existing_set:
                continue

            tags_b = set(t.strip() for t in (b.tags or "").split(",") if t.strip())
            stags_b = set(t.strip() for t in (b.structured_tags or "").split(",") if t.strip())
            all_tags_b = tags_b | stags_b

            shared = len(all_tags_a & all_tags_b)
            if shared >= 2:
                candidates.append((a, b, shared))

    # Sort by most shared tags first, take top N
    candidates.sort(key=lambda x: x[2], reverse=True)
    candidates = candidates[:_MAX_PAIRS]

    if not candidates:
        logger.info("No eligible character pairs found")
        return 0

    count = 0
    for a, b, shared in candidates:
        try:
            rel_type = await _determine_relationship(a, b)
            if rel_type and rel_type in _VALID_TYPES:
                labels = _LABELS[rel_type]
                # Create bidirectional relations
                async with db_engine.begin() as conn:
                    await conn.execute(text("""
                        INSERT INTO character_relations (id, character_id, related_id, relation_type, label_ru, label_en, label_es)
                        VALUES (:id1, :a, :b, :type, :ru, :en, :es),
                               (:id2, :b, :a, :type, :ru, :en, :es)
                    """), {
                        "id1": str(uuid.uuid4()), "id2": str(uuid.uuid4()),
                        "a": a.id, "b": b.id, "type": rel_type,
                        "ru": labels["ru"], "en": labels["en"], "es": labels["es"],
                    })
                count += 1
                logger.info("Created %s relation: %s <-> %s", rel_type, a.name, b.name)
        except Exception:
            logger.exception("Failed to create relation for %s <-> %s", a.name, b.name)

    return count


async def _determine_relationship(a, b) -> str | None:
    """Use LLM to determine relationship type between two characters."""
    prompt = _PROMPT.format(
        name_a=a.name, tags_a=a.tags or "",
        personality_a=(a.personality or "")[:150],
        name_b=b.name, tags_b=b.tags or "",
        personality_b=(b.personality or "")[:150],
    )
    messages = [LLMMessage(role="user", content=prompt)]
    config = LLMConfig(model="", temperature=0.3, max_tokens=20)

    for provider_name in _PROVIDER_ORDER:
        try:
            provider = get_provider(provider_name)
            raw = await provider.generate(messages, config)
            result = raw.strip().lower().split()[0] if raw.strip() else None
            if result in _VALID_TYPES:
                return result
        except Exception as e:
            logger.warning("Relationship LLM failed with %s: %s", provider_name, str(e)[:100])
            continue

    return None
