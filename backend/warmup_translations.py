"""One-time script to pre-translate all characters into EN and ES."""
import asyncio
import sys
import os

# Ensure app module is importable
sys.path.insert(0, os.path.dirname(__file__))


async def main():
    from app.db.session import async_session
    from app.db.models import Character
    from app.characters.translation import ensure_translations
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    target_languages = ["en", "es"]

    async with async_session() as db:
        result = await db.execute(
            select(Character).options(selectinload(Character.creator))
        )
        characters = list(result.scalars().all())
        print(f"Found {len(characters)} characters")

        for lang in target_languages:
            # Filter characters that need translation (original != target)
            need = [c for c in characters if (c.original_language or "ru") != lang]
            cached = [c for c in need if (c.translations or {}).get(lang)]
            uncached = [c for c in need if not (c.translations or {}).get(lang)]
            print(f"\n[{lang}] {len(need)} need translation, {len(cached)} cached, {len(uncached)} uncached")

            if not uncached:
                print(f"[{lang}] All cached, skipping")
                continue

            # Translate in batches of 15
            BATCH = 15
            for i in range(0, len(uncached), BATCH):
                batch = uncached[i:i + BATCH]
                print(f"[{lang}] Translating batch {i // BATCH + 1} ({len(batch)} chars)...")
                # Use ensure_translations with cached_only=False to trigger LLM
                await ensure_translations(batch, lang, cached_only=False)
                translated = sum(1 for c in batch if getattr(c, '_active_translations', None))
                print(f"[{lang}] Translated {translated}/{len(batch)}")
                # Small delay between batches to respect rate limits
                if i + BATCH < len(uncached):
                    await asyncio.sleep(2)

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
