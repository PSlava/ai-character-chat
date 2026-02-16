"""One-time script to pre-translate all characters into EN and ES.

Translates both card fields (name, tagline, tags) and description fields
(personality, scenario, appearance, greeting_message).
"""
import asyncio
import logging
import sys
import os

logging.basicConfig(level=logging.WARNING)

# Ensure app module is importable
sys.path.insert(0, os.path.dirname(__file__))


async def main():
    from app.config import settings
    from app.llm.registry import init_providers
    from app.db.session import async_session
    from app.db.models import Character
    from app.characters.translation import ensure_translations
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    # Initialize LLM providers (normally done by FastAPI lifespan)
    init_providers(
        anthropic_key=settings.anthropic_api_key,
        openai_key=settings.openai_api_key,
        gemini_key=settings.gemini_api_key,
        openrouter_key=settings.openrouter_api_key,
        deepseek_key=settings.deepseek_api_key,
        qwen_key=settings.qwen_api_key,
        groq_key=settings.groq_api_key,
        cerebras_key=settings.cerebras_api_key,
        together_key=settings.together_api_key,
        proxy_url=settings.proxy_url,
    )
    from app.llm.registry import get_available_providers
    print(f"Providers: {get_available_providers()}")

    target_languages = ["en", "es", "fr", "de"]

    async with async_session() as db:
        result = await db.execute(
            select(Character).options(selectinload(Character.creator))
        )
        characters = list(result.scalars().all())
        print(f"Found {len(characters)} characters")

        # Pass 1: Translate card fields (name, tagline, tags) — batched, fast
        for lang in target_languages:
            need = [c for c in characters if (c.original_language or "ru") != lang]
            uncached = [c for c in need if not (c.translations or {}).get(lang)]
            print(f"\n[{lang}] CARDS: {len(uncached)} uncached of {len(need)}")

            if not uncached:
                print(f"[{lang}] All cards cached, skipping")
                continue

            BATCH = 15
            for i in range(0, len(uncached), BATCH):
                batch = uncached[i:i + BATCH]
                print(f"[{lang}] Cards batch {i // BATCH + 1} ({len(batch)} chars)...")
                await ensure_translations(batch, lang, include_descriptions=False, cached_only=False)
                translated = sum(1 for c in batch if getattr(c, '_active_translations', None))
                print(f"[{lang}] Translated {translated}/{len(batch)}")
                if i + BATCH < len(uncached):
                    await asyncio.sleep(2)

        # Pass 2: Translate descriptions (personality, scenario, appearance, greeting)
        # One character at a time with delays to stay within rate limits
        for lang in target_languages:
            need = [c for c in characters if (c.original_language or "ru") != lang]
            # Re-read from DB to get fresh translations column
            result2 = await db.execute(
                select(Character).options(selectinload(Character.creator))
            )
            fresh_chars = {c.id: c for c in result2.scalars().all()}

            need_desc = []
            for c in need:
                fresh = fresh_chars.get(c.id, c)
                cached_tr = (fresh.translations or {}).get(lang, {})
                if not cached_tr.get("personality") and getattr(fresh, "personality", None):
                    need_desc.append(fresh)

            print(f"\n[{lang}] DESCRIPTIONS: {len(need_desc)} need translation")

            for i, c in enumerate(need_desc):
                print(f"[{lang}] {i + 1}/{len(need_desc)}: {c.name}...", end=" ", flush=True)
                await ensure_translations([c], lang, include_descriptions=True, cached_only=False)
                has_tr = bool(getattr(c, '_active_translations', {}).get("personality"))
                print("OK" if has_tr else "FAILED")
                # 3s delay between characters (4 API calls each → ~13/min, well within 60/min)
                if i + 1 < len(need_desc):
                    await asyncio.sleep(3)

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
