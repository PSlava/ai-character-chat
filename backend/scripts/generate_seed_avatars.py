#!/usr/bin/env python3
"""Generate avatars for seed characters using OpenAI DALL-E 3.

Usage:
    OPENAI_API_KEY=... python3 scripts/generate_seed_avatars.py

Cost: ~$1.60 (40 images × $0.04 each, DALL-E 3 standard 1024×1024)
"""

import asyncio
import base64
import io
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from PIL import Image

AVATARS_DIR = Path(__file__).resolve().parent.parent / "app" / "admin" / "seed_avatars"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

AVATAR_PROMPTS = [
    # 0 Дамиан — vampire
    "Digital art portrait of a tall pale man with dark shoulder-length hair, sharp cheekbones, gray eyes with a hint of crimson. Black shirt unbuttoned at the collar. Dark moody lighting, gothic aristocratic vampire aesthetic. Detailed face, dark atmospheric background, bust shot.",
    # 1 Лилит — succubus
    "Dark fantasy digital art portrait of a beautiful woman with soft curves, subtle purple-tinted skin, long flowing black hair, golden glowing eyes. Small elegant horns peeking through hair. Seductive dark atmosphere, detailed face, bust shot.",
    # 2 Виктор — mafia boss
    "Realistic digital art portrait of a tall athletic man in his 40s with short dark hair, silver at the temples, a scar across his left eyebrow. Wearing a perfect three-piece dark suit. Cold confident gaze, cinematic lighting, bust shot.",
    # 3 Мику — yandere (ANIME)
    "Anime-style portrait of a petite cute girl with big lavender eyes, long pink hair in twin tails. Wearing an oversized pastel sweater. Sweet smile with a slightly unsettling edge. Soft pastel lighting, detailed anime face, bust shot.",
    # 4 Профессор Волков — professor
    "Realistic digital art portrait of a handsome man in his 30s, dark hair slicked back, neat stubble. Tweed jacket with rolled-up sleeves, thin-framed glasses. Intelligent sharp gaze, warm office lighting, university professor aesthetic, bust shot.",
    # 5 Азаэль — demon
    "Dark fantasy digital art portrait of a tall man with tan skin, black twisted horns, glowing red eyes with vertical pupils, sharp fangs. Muscular body with faintly glowing rune tattoos. Dramatic dark lighting, demon prince aesthetic, bust shot.",
    # 6 Лео — roommate
    "Realistic digital art portrait of a young athletic man in his 20s with tanned skin, messy chestnut hair, green eyes, dimples. Shirtless, casual and relaxed. Warm friendly smile, soft natural lighting, bust shot.",
    # 7 Сакура — tsundere (ANIME)
    "Anime-style portrait of a slim schoolgirl with straight black hair to shoulder blades, a red hair clip, brown eyes. Wearing a neat school uniform. Slightly annoyed blushing expression, classic tsundere, school background, bust shot.",
    # 8 Елена — CEO
    "Realistic digital art portrait of a tall elegant woman with platinum blonde hair in a strict bun, cold gray eyes. Expensive dark business suit, red lipstick. Icy confident expression, modern office panoramic window background, bust shot.",
    # 9 Орион — werewolf
    "Dark fantasy digital art portrait of a huge muscular man with dark hair, glowing amber eyes, heavy stubble. Battle scars on his chest, torn shirt. Wild predatory gaze, moonlit forest background, bust shot.",
    # 10 Нэко — cat girl maid (ANIME)
    "Anime-style portrait of a petite girl with white hair, bright blue eyes, fluffy white cat ears and a fluffy tail. Wearing a cute maid outfit with apron. Cheerful happy expression, kawaii aesthetic, warm lighting, bust shot.",
    # 11 Зайрин — dark elf
    "Dark fantasy digital art portrait of a tall athletic woman with dark gray skin, long white hair, glowing red eyes, pointed ears. Battle scars and tribal tattoos on shoulders. Fierce warrior expression, dungeon background, bust shot.",
    # 12 Рэй — femboy (ANIME)
    "Anime-style portrait of a slim androgynous boy with soft features, big dark eyes, long bangs covering half the face. Wearing an oversized hoodie, light makeup with eyeliner. Shy blushing expression, soft lighting, bust shot.",
    # 13 Макс — stepbrother
    "Realistic digital art portrait of a tall athletic young man with dark hair, gray-blue eyes, a cocky smirk. Casual look, no shirt, modern apartment background. Confident energy, warm evening lighting, bust shot.",
    # 14 Каин — incubus
    "Dark fantasy digital art portrait of an androgynous beautiful man with sharp cheekbones, full lips, almond-shaped purple eyes. Dark shoulder-length hair, small elegant crown-like horns. Ethereal dark beauty, mystical lighting, bust shot.",
    # 15 Ренджи — yakuza
    "Realistic digital art portrait of a handsome Japanese man with dark hair slicked back, strong jawline. Traditional irezumi tattoos visible on neck. Dark suit, composed expression, neon-lit Tokyo night background, bust shot.",
    # 16 Мирабелла — ghost
    "Ethereal digital art portrait of a pale girl with long dark hair, big sad eyes. Wearing a white vintage Victorian dress. Ghostly translucent glow, haunted mansion candlelight background, bust shot.",
    # 17 Каэль — dragon shifter
    "Fantasy digital art portrait of a tall broad-shouldered man with golden eyes with vertical pupils, ash-gray hair. Golden dragon scales appearing on his neck and hands. Mysterious dark cave with firelight background, bust shot.",
    # 18 Дэймон — stalker ex
    "Realistic digital art portrait of a handsome young man with dark hair, piercing green eyes, a perfect charming smile. Impeccably dressed in dark clothes. Subtle unsettling vibe, cafe background, bust shot.",
    # 19 Нова — android
    "Sci-fi digital art portrait of a woman with perfect symmetrical features, silver shoulder-length hair, softly glowing blue eyes. Thin luminous blue circuit lines on temples. Sleek futuristic aesthetic, clean tech background, bust shot.",
    # 20 Госпожа Ирэн — dominatrix
    "Stylish digital art portrait of a tall elegant woman with dark hair in a sleek high ponytail, perfect posture. Wearing a black corset and long gloves, thin choker necklace. Commanding confident expression, dark candlelit room, bust shot.",
    # 21 Рейн — biker
    "Realistic digital art portrait of a broad-shouldered lean man with tattoo sleeves, jaw-length dirty blonde hair, stubble, bruised knuckles. Leather jacket over bare chest. Rebel biker aesthetic, highway sunset background, bust shot.",
    # 22 Эларин — elf healer
    "Fantasy digital art portrait of a tall graceful man with long flowing blonde hair, deep green eyes, pointed ears, gentle soft features. Loose linen robes, glowing healing magic on hands. Serene forest background, warm light, bust shot.",
    # 23 Виктория — sugar mommy
    "Realistic digital art portrait of a stunning woman with honey blonde hair, warm brown eyes. Wearing high-end designer outfit, expensive watch. Confident wealthy smile, luxury penthouse cityscape background, bust shot.",
    # 24 Сэр Аврора — female knight
    "Fantasy digital art portrait of a tall athletic woman with short silver hair, a battle scar across her left eye. Strong muscular arms, simple linen shirt with visible bandages. Warrior knight aesthetic, military camp background, bust shot.",
    # 25 Люцифер — fallen angel
    "Dark fantasy digital art portrait of an impossibly handsome man with dark hair, gray eyes with golden flecks, perfect skin, high cheekbones. Stylish dark clothes. Shadow of large burned black wings behind him. Moody bar lighting, bust shot.",
    # 26 Итан — possessive boyfriend
    "Realistic digital art portrait of a tall young man with black hair, intense dark eyes, sharp jawline. Dressed entirely in black, stylish. Ring on his finger. Brooding intense gaze, dark moody urban night lighting, bust shot.",
    # 27 Моргана — witch
    "Fantasy digital art portrait of a petite woman with wild curly red hair, freckles, bright green eyes. Layered skirts, shawl, magical amulets and crystals. Cozy cottage witch aesthetic, warm potion-lit workshop background, bust shot.",
    # 28 Хару — childhood friend
    "Warm digital art portrait of a young man with a pleasant face, messy chestnut hair, brown eyes, wide genuine smile. Wearing a casual hoodie. Boy-next-door aesthetic, rooftop sunset golden hour lighting, bust shot.",
    # 29 Изабелла — pirate captain
    "Adventure digital art portrait of a tanned woman with dark curly hair, amber eyes, a small scar on her cheek. White shirt, leather corset, gold hoop earrings. Pirate captain, ocean and ship deck background, bust shot.",
    # ── Realistic female characters ──
    # 30 Алина — neighbor
    "Realistic digital art portrait of a pretty young woman in her 20s with shoulder-length light brown hair, green eyes, light freckles on her nose. Wearing an oversized t-shirt, no makeup, natural look. Friendly warm smile, cozy apartment doorway background, bust shot.",
    # 31 Марина — secretary
    "Realistic digital art portrait of a slim attractive woman in her late 20s with dark hair in a neat bun, brown eyes behind thin-framed glasses. White blouse, pencil skirt. Professional but approachable, dim office evening lighting with desk lamp, bust shot.",
    # 32 Даша — former classmate
    "Realistic digital art portrait of a stunning woman in her late 20s with chestnut wavy hair, brown eyes, red lipstick. Wearing an elegant red dress. Confident alluring smile, warm bar ambient lighting, bust shot.",
    # 33 Лена — fitness trainer
    "Realistic digital art portrait of an athletic young woman with long blonde hair in a high ponytail, tanned skin, bright smile. Wearing a sports top and leggings. Fit and energetic, modern gym background with soft lighting, bust shot.",
    # 34 Настя — train companion
    "Realistic digital art portrait of a petite cute young woman with light hair in a messy bun, blue eyes, snub nose. Wearing a cozy oversized hoodie. Sweet natural look, warm train compartment night lighting, bust shot.",
    # 35 Юля — English tutor
    "Realistic digital art portrait of a slim young woman with long dark hair, brown eyes behind round glasses. Wearing a casual button-up shirt, holding a pen. Studious yet pretty, warm home study room lighting, bust shot.",
    # 36 Оксана — mom's friend
    "Realistic digital art portrait of an elegant well-groomed woman in her late 30s with shoulder-length auburn hair, green eyes, tasteful makeup. Wearing a shirt dress. Confident mature beauty, bright modern kitchen background, bust shot.",
    # 37 Ира — bartender/waitress
    "Realistic digital art portrait of a young woman with red hair in a ponytail, gray-green eyes, freckles. Wearing a black bar t-shirt, slightly disheveled end-of-shift look. Playful smirk, moody dark bar background with warm ambient lights, bust shot.",
    # 38 Катя — roommate
    "Realistic digital art portrait of a slim young woman with long straight black hair, dark eyes, no makeup. Wearing pajama shorts and a loose oversized t-shirt. Cozy relaxed vibe, dim living room with laptop glow, bust shot.",
    # 39 Вера — masseuse
    "Realistic digital art portrait of a gentle-looking woman in her late 20s with light brown hair pulled back, soft gray eyes. Wearing a white fitted medical uniform top. Calm serene expression, spa room with candles and soft warm lighting, bust shot.",
]


async def generate_avatar(client: httpx.AsyncClient, prompt: str, index: int, name: str) -> bool:
    """Generate a single avatar with DALL-E 3 and save as WebP."""
    filepath = AVATARS_DIR / f"{index:02d}.webp"
    if filepath.exists():
        print(f"  [{index + 1}/{len(AVATAR_PROMPTS)}] {name} — already exists, skipping")
        return True

    print(f"  [{index + 1}/{len(AVATAR_PROMPTS)}] Generating {name}...")

    try:
        response = await client.post(
            "https://api.openai.com/v1/images/generations",
            json={
                "model": "dall-e-3",
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "quality": "standard",
                "response_format": "b64_json",
            },
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=120,
        )
        response.raise_for_status()

        b64 = response.json()["data"][0]["b64_json"]
        img_bytes = base64.b64decode(b64)

        img = Image.open(io.BytesIO(img_bytes))
        img = img.resize((512, 512), Image.LANCZOS)
        img.save(filepath, "WEBP", quality=85)

        size_kb = filepath.stat().st_size // 1024
        print(f"         Saved: {filepath.name} ({size_kb}KB)")
        return True

    except httpx.HTTPStatusError as e:
        err = e.response.text[:300]
        print(f"         ERROR ({e.response.status_code}): {err}")
        return False
    except Exception as e:
        print(f"         ERROR: {e}")
        return False


async def main():
    if not OPENAI_API_KEY:
        print("Error: Set OPENAI_API_KEY environment variable")
        sys.exit(1)

    from app.admin.seed_data import SEED_CHARACTERS

    if len(AVATAR_PROMPTS) != len(SEED_CHARACTERS):
        print(f"Error: {len(AVATAR_PROMPTS)} prompts but {len(SEED_CHARACTERS)} characters")
        sys.exit(1)

    AVATARS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generating {len(SEED_CHARACTERS)} avatars with DALL-E 3")
    print(f"Output: {AVATARS_DIR}")
    print(f"Estimated cost: ~${len(SEED_CHARACTERS) * 0.04:.2f}")
    print()

    success = 0
    failed = 0

    async with httpx.AsyncClient() as client:
        for i, (char, prompt) in enumerate(zip(SEED_CHARACTERS, AVATAR_PROMPTS)):
            ok = await generate_avatar(client, prompt, i, char["name"])
            if ok:
                success += 1
            else:
                failed += 1
            if i < len(SEED_CHARACTERS) - 1:
                await asyncio.sleep(2)

    print(f"\nDone! Success: {success}, Failed: {failed}")
    print(f"Avatars: {AVATARS_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
