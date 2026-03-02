"""Generate backstory, hidden_layers, inner_conflict for existing characters via LLM.

Backfills the 3 new depth fields for all public characters that don't have them yet.
Uses paid providers (Together -> Groq -> OpenAI -> Claude -> DeepSeek).

Run inside Docker container:
  docker compose exec -T backend python scripts/generate_character_depth.py

Options:
  --sweetsin-only   Only process @sweetsin characters (seed + auto-generated)
  --fiction-only    Only process @fiction characters (seed stories)
  --all             Process ALL public characters (default)
  --dry-run         Show what would be generated without writing to DB
  --force           Regenerate even if fields already exist
"""

import asyncio
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.llm.registry import init_providers, get_provider
from app.llm.base import LLMMessage, LLMConfig
from app.db.session import engine as db_engine
from app.autonomous.text_humanizer import humanize_text

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
logger = logging.getLogger("depth")

_PROVIDER_ORDER = ("openai", "claude", "deepseek", "together", "groq")
_TIMEOUT = 90.0

# --- Prompt for generating all 3 fields at once ---
_DEPTH_PROMPT = """На основе описания персонажа, создай три поля глубины характера. Ответь строго JSON.

Персонаж: {name}
Описание: {personality}
Внешность: {appearance}
Сценарий: {scenario}

Верни JSON:
{{
  "backstory": "3-5 предложений. (1) ОДНО конкретное событие из прошлого (Ghost) - НЕ эпическая трагедия, а тихое предательство, потеря, ошибка. Назови дату, место, имя. (2) Эмоциональная рана (Wound) - как это влияет на поведение СЕЙЧАС, через конкретные действия. (3) Ложное убеждение (Lie) - защитная реакция одним предложением. (4) Секрет - что персонаж скрывает от всех.",
  "hidden_layers": "Level 1: [поведение с незнакомцем - конкретная маска, защитный жест, первая фраза] Level 2: [~10 сообщений - делится конкретными мнениями, проскальзывают намеки на прошлое через оговорки] Level 3: [~20 сообщений - раскрывает рану через конкретное действие или признание] Level 4: [30+ сообщений - главный секрет, момент когда Ложь ломается, конкретная сцена]",
  "inner_conflict": "ХОЧЕТ: [конкретная внешняя цель с деталями] vs НУЖДАЕТСЯ: [внутренний рост]. Они КОНФЛИКТУЮТ."
}}

ПРАВИЛА:
- backstory: конкретика. "Мать ушла в ноябре, когда ей было семь - забрала только кота" лучше чем "тяжелое детство"
- hidden_layers: формат СТРОГО "Level 1: текст Level 2: текст Level 3: текст Level 4: текст"
- inner_conflict: ХОЧЕТ и НУЖДАЕТСЯ должны ПРОТИВОРЕЧИТЬ друг другу
- Соответствуй характеру и тону персонажа
- Чередуй короткие рубленые предложения (3-6 слов) с длинными (20-35 слов). 3 предложения одной длины подряд = провал
- Используй второе слово, которое приходит в голову, не первое. "Пепельная" вместо "серая". "Ломкий" вместо "хрупкий"
- Покажи через действие, не рассказывай. "Прячет руки под стол когда врет" вместо "склонна ко лжи"

ЖЕСТКИЕ ЗАПРЕТЫ (любое = провал):
- Слова: пронизан, гобелен, поистине, многогранный, неотъемлемый, является, представляет собой, стоит отметить, важно подчеркнуть, величественный, утонченный, пленительный, грациозный, необъятный, трепетный, упоительный, непередаваемый, сокровенный, пьянящий, завораживающий, неподдельный, таинственный, роковой, судьбоносный
- Фразы: "волна чувств", "нахлынувшее чувство", "пронзительный взгляд", "воздух наполненный", "не смогла сдержать", "в рамках", "таким образом", "нечто большее"
- Структуры: "Это было не X. Это было Y." (6.3x AI-маркер). Списки ровно из трех. Начинать 2+ предложения с одного подлежащего (Она/Он)
- Клише тела: глаза заблестели/расширились, сердце забилось/замерло, дыхание перехватило, мурашки по спине, ком в горле, тепло разлилось по груди
- НЕ используй длинное тире, только обычный дефис
- Верни ТОЛЬКО JSON"""

_DEPTH_PROMPT_EN = """Based on the character description, create three depth fields. Reply with strict JSON.

Character: {name}
Description: {personality}
Appearance: {appearance}
Scenario: {scenario}

Return JSON:
{{
  "backstory": "3-5 sentences. (1) ONE specific past event (Ghost) - NOT an epic tragedy. A quiet betrayal, loss, or mistake. Name a date, place, person. (2) Emotional wound (Wound) - how it affects behavior NOW through concrete actions. (3) False belief (Lie) - defensive reaction, one sentence. (4) Secret - what they hide from everyone.",
  "hidden_layers": "Level 1: [stranger behavior - specific mask, defensive gesture, opening line] Level 2: [~10 messages - shares concrete opinions, past slips through in specific phrases] Level 3: [~20 messages - reveals wound through a specific action or confession] Level 4: [30+ messages - main secret, the moment the Lie breaks, a concrete scene]",
  "inner_conflict": "WANTS: [specific external goal with details] vs NEEDS: [internal growth]. They must CONFLICT."
}}

RULES:
- backstory: concrete. "Mother left in November when she was seven - took only the cat" beats "difficult childhood"
- hidden_layers: format STRICTLY "Level 1: text Level 2: text Level 3: text Level 4: text"
- inner_conflict: WANTS and NEEDS must CONTRADICT each other
- Match the character's personality and tone
- Alternate short punchy sentences (3-6 words) with longer ones (20-35 words). Three sentences of similar length in a row = fail
- Use the second word that comes to mind, not the first. "Soot-colored" not "dark". "Sharp-featured" not "beautiful"
- Show through action, don't tell. "Hides hands under the table when lying" not "prone to deception"

HARD BANS (any = instant fail):
- Words: tapestry, beacon, delve, enigmatic, realm, embark, testament, myriad, pivotal, captivating, resonate, profound, unveil, vibrant, intricate, nuanced, multifaceted, unravel, shrouded, intertwined, ethereal, celestial, labyrinthine, gossamer, ephemeral, palpable, culmination, indelible, meticulous, unwavering, crucible, paradigm, cacophony, vestiges, luminous, resplendent, symphony (metaphorical), kaleidoscope
- Phrases: "a tapestry of", "a testament to", "a symphony of", "something stirred", "the air crackled", "tension hung", "darkness crept", "walls crumbled", "everything changed", "in that moment", "couldn't help but", "little did they know", "maybe just maybe"
- Patterns: "It wasn't X. It was Y." construction (6.3x AI marker). Lists of exactly three. Starting 2+ sentences with same subject (She/He)
- Body cliches: eyes sparkled/widened/glistened, heart raced/pounded, breath caught/hitched, shivers down spine, knot in stomach, warmth spread through chest
- Do NOT use em-dashes, only regular hyphens
- Return ONLY JSON"""

_FICTION_DEPTH_PROMPT = """Based on this interactive fiction adventure, create three narrative depth fields. Reply with strict JSON.

Adventure: {name}
Setting: {personality}
Visual Details: {appearance}
Scenario: {scenario}

Return JSON:
{{
  "backstory": "3-5 sentences of WORLD HISTORY. Hidden truths, NPC secrets, lore discovered over time. NOT character backstory - world-building only. Be CONCRETE: names, dates, places, specific events. Vary sentence length wildly - mix 5-word punches with 30-word complex sentences.",
  "hidden_layers": "Phase 1: [specific opening events and hooks] Phase 2: [specific complications and betrayals] Phase 3: [specific climactic confrontations] Phase 4: [specific consequences and transformations]",
  "inner_conflict": "A single raw sentence. Two concrete options that collide. Example format: 'Burning the ledger protects the family but lets the cartel walk free vs handing it to police saves the city but destroys everyone she loves'"
}}

RULES:
- backstory: world lore only. Name a specific person, place, date, or event in every sentence. "The Thornwood pact of 1347 bound three houses to silence" not "ancient forces shaped the land"
- hidden_layers: STRICTLY "Phase 1: text Phase 2: text Phase 3: text Phase 4: text". Each phase describes CONCRETE plot events unique to THIS story. No generic placeholders
- inner_conflict: raw dilemma, one sentence. NEVER start with "The reader must choose" or "CENTRAL DILEMMA:" - just state the tension directly
- Vary sentence length: short punches (3-6 words) mixed with longer ones. Three sentences of similar length in a row = fail
- Use the second word that comes to mind, not the first. "Soot-colored" not "dark". "Sharp-featured" not "beautiful"

HARD BANS (any of these = instant fail):
- Words: tapestry, beacon, delve, enigmatic, realm, embark, testament, myriad, pivotal, captivating, resonate, profound, unveil, vibrant, intricate, nuanced, multifaceted, unravel, shrouded, intertwined, ethereal, celestial, labyrinthine, gossamer, ephemeral, palpable, culmination, indelible, meticulous, unwavering, crucible, paradigm, cacophony, vestiges, symphony (metaphorical), kaleidoscope, luminous, resplendent
- Phrases: "a tapestry of", "a testament to", "a symphony of", "something stirred", "the air crackled", "tension hung", "darkness crept", "walls crumbled", "everything changed", "in that moment", "was only just beginning", "little did they know"
- Patterns: "It wasn't X. It was Y." construction. Starting sentences with "The reader". Lists of exactly three adjectives/nouns
- Body cliches: eyes sparkled/widened/glistened, heart raced/pounded, breath caught/hitched, shivers down spine, knot in stomach, warmth spread through

Write like a thriller novelist on deadline. Gritty. Specific. No poetry.
Return ONLY JSON"""

_DND_DEPTH_PROMPT = """Based on this D&D campaign, create three narrative depth fields. Reply with strict JSON.

Campaign: {name}
Setting: {personality}
World Details: {appearance}
Scenario: {scenario}

Return JSON:
{{
  "backstory": "3-5 sentences of CAMPAIGN LORE. The BBEG's true motivation, faction secrets, hidden alliances. Be CONCRETE: name every person, place, event. Vary sentence length - short punches mixed with complex ones.",
  "hidden_layers": "Phase 1: [specific encounters and discoveries] Phase 2: [specific betrayals and reveals] Phase 3: [specific confrontations and sacrifices] Phase 4: [specific endgame conditions and consequences]",
  "inner_conflict": "A single raw sentence. Two concrete options from THIS campaign that collide. Example: 'Sparing the necromancer means saving the enslaved dead but dooms the valley to eternal winter vs destroying him frees the land but kills every revenant including the paladin's daughter'"
}}

RULES:
- backstory: campaign secrets only. Name a specific NPC, location, or event in every sentence. "Commander Voss sealed the tomb in 1183 to hide the failed ritual" not "ancient forces were at work"
- hidden_layers: STRICTLY "Phase 1: text Phase 2: text Phase 3: text Phase 4: text". Each phase describes CONCRETE events unique to THIS campaign. No stock D&D tropes
- inner_conflict: raw dilemma, one sentence. NEVER start with "The players must" or "Moral stakes:" - just state the tension directly using names from the campaign
- Vary sentence length: short punches (3-6 words) mixed with longer ones. No three sentences of similar length in a row

HARD BANS (any of these = instant fail):
- Words: tapestry, beacon, delve, enigmatic, realm, embark, testament, myriad, pivotal, captivating, resonate, profound, unveil, vibrant, intricate, nuanced, multifaceted, unravel, shrouded, intertwined, ethereal, celestial, labyrinthine, gossamer, ephemeral, palpable, culmination, indelible, meticulous, unwavering, crucible, paradigm, cacophony, vestiges, symphony (metaphorical), kaleidoscope, luminous, resplendent
- Phrases: "a tapestry of", "a testament to", "something stirred", "the air crackled", "tension hung", "darkness crept", "walls crumbled", "everything changed", "in that moment", "can the ends justify the means", "was only just beginning"
- Patterns: "It wasn't X. It was Y." construction. Starting sentences with "The players must" or "The campaign's central". Lists of exactly three
- Body cliches: eyes sparkled/widened, heart raced, breath caught, shivers down spine

Write like a game master whispering secrets at 2am. Blunt. Concrete. No grandeur.
Return ONLY JSON"""


async def _call_llm(messages: list[LLMMessage], config: LLMConfig, label: str = "") -> str | None:
    for provider_name in _PROVIDER_ORDER:
        try:
            provider = get_provider(provider_name)
        except ValueError:
            continue
        try:
            raw = await asyncio.wait_for(
                provider.generate(messages, config),
                timeout=_TIMEOUT,
            )
            result = raw.strip()
            if result and len(result) > 50:
                logger.info("  %s via %s (%d chars)", label, provider_name, len(result))
                return result
        except Exception as e:
            logger.warning("  %s: %s failed: %s", label, provider_name, str(e)[:100])
            continue
    return None


async def _generate_depth(name: str, personality: str, appearance: str, scenario: str, lang: str = "ru", mode: str = "rp") -> dict | None:
    """Generate backstory, hidden_layers, inner_conflict for a character.

    mode: 'rp' (SweetSin), 'fiction' (GrimQuill IF), 'dnd' (GrimQuill DnD)
    """
    if mode == "fiction":
        prompt_tpl = _FICTION_DEPTH_PROMPT
    elif mode == "dnd":
        prompt_tpl = _DND_DEPTH_PROMPT
    elif lang == "ru":
        prompt_tpl = _DEPTH_PROMPT
    else:
        prompt_tpl = _DEPTH_PROMPT_EN
    prompt = prompt_tpl.format(
        name=name,
        personality=personality[:1500],
        appearance=(appearance or "")[:500],
        scenario=(scenario or "")[:500],
    )
    if mode in ("fiction", "dnd"):
        sys_msg = (
            "You are an expert narrative designer. Write like a human novelist - gritty, specific, varied rhythm. "
            "NEVER use AI-typical words: tapestry, beacon, delve, enigmatic, realm, embark, profound, unveil, vibrant, intricate, nuanced, pivotal, multifaceted, unravel, shrouded, intertwined, ethereal, celestial, palpable, culmination. "
            "Vary sentence length aggressively. Use concrete details, not abstractions. Reply with strict JSON only."
        )
    elif lang == "ru":
        sys_msg = (
            "Ты - писатель с 20-летним опытом, создаешь глубоких персонажей для ролевых чатов. "
            "Пиши как человек - рвано, конкретно, с перепадами ритма. "
            "ЗАПРЕЩЕНО: пронизан, гобелен, многогранный, неотъемлемый, является, представляет собой, величественный, утонченный, "
            "пленительный, завораживающий, непередаваемый, сокровенный, таинственный, роковой, судьбоносный. "
            "Чередуй короткие предложения (3-6 слов) с длинными. Покажи через действие, не рассказывай. "
            "Отвечай строго JSON."
        )
    else:
        sys_msg = (
            "You are a novelist with 20 years of experience, creating deep characters for roleplay chats. "
            "Write like a human - rough, specific, varied rhythm. "
            "BANNED words: tapestry, beacon, delve, enigmatic, realm, embark, testament, myriad, pivotal, captivating, "
            "resonate, profound, unveil, vibrant, intricate, nuanced, multifaceted, ethereal, palpable, luminous. "
            "Alternate short sentences (3-6 words) with longer ones. Show through action, don't tell. "
            "Reply with strict JSON."
        )
    messages = [
        LLMMessage(role="system", content=sys_msg),
        LLMMessage(role="user", content=prompt),
    ]
    config = LLMConfig(model="", temperature=0.85, max_tokens=1500)

    raw = await _call_llm(messages, config, label=f"depth({name})")
    if not raw:
        return None

    # Strip markdown fences
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("  Failed to parse JSON for %s", name)
        return None

    # Validate
    result = {}
    for key in ("backstory", "hidden_layers", "inner_conflict"):
        val = data.get(key, "")
        if isinstance(val, str) and len(val) > 20:
            result[key] = humanize_text(val)

    return result if result else None


async def main():
    args = set(sys.argv[1:])
    dry_run = "--dry-run" in args
    force = "--force" in args
    sweetsin_only = "--sweetsin-only" in args
    fiction_only = "--fiction-only" in args

    # Initialize providers
    init_providers(
        openrouter_key=settings.openrouter_api_key or "",
        groq_key=settings.groq_api_key or "",
        cerebras_key=settings.cerebras_api_key or "",
        together_key=settings.together_api_key or "",
        deepseek_key=settings.deepseek_api_key or "",
        qwen_key=settings.qwen_api_key or "",
        anthropic_key=settings.anthropic_api_key or "",
        openai_key=settings.openai_api_key or "",
        gemini_key=settings.gemini_api_key or "",
        proxy_url=settings.proxy_url or "",
    )

    available = []
    for p in _PROVIDER_ORDER:
        try:
            get_provider(p)
            available.append(p)
        except ValueError:
            pass
    logger.info("Available providers: %s", ", ".join(available))
    if not available:
        logger.error("No providers available!")
        return

    # Build query
    from sqlalchemy import text
    where_clauses = ["c.is_public = true"]

    if sweetsin_only:
        where_clauses.append("u.email = 'system@sweetsin.cc'")
    elif fiction_only:
        where_clauses.append("u.email = 'system@fiction.local'")

    if not force:
        where_clauses.append("(c.backstory IS NULL OR c.hidden_layers IS NULL OR c.inner_conflict IS NULL)")

    where_sql = " AND ".join(where_clauses)

    async with db_engine.connect() as conn:
        result = await conn.execute(text(f"""
            SELECT c.id, c.name, c.personality, c.appearance, c.scenario, c.original_language,
                   c.backstory, c.hidden_layers, c.inner_conflict, c.tags
            FROM characters c
            JOIN users u ON c.creator_id = u.id
            WHERE {where_sql}
            ORDER BY c.created_at
        """))
        characters = result.fetchall()

    logger.info("Found %d characters to process (dry_run=%s, force=%s)", len(characters), dry_run, force)

    updated = 0
    skipped = 0
    failed = 0

    for char in characters:
        char_id, name, personality, appearance, scenario, orig_lang, existing_bs, existing_hl, existing_ic, tags_str = char

        # Skip if all fields already filled (unless --force)
        if not force and existing_bs and existing_hl and existing_ic:
            skipped += 1
            continue

        # Detect mode from tags and owner
        tag_list = [t.strip().lower() for t in (tags_str or "").split(",") if t.strip()]
        if fiction_only or "dnd" in tag_list:
            mode = "dnd" if "dnd" in tag_list else "fiction"
        else:
            mode = "rp"

        logger.info("\n=== %s (id=%s, lang=%s, mode=%s) ===", name, char_id[:8], orig_lang, mode)

        if dry_run:
            logger.info("  [DRY RUN] Would generate depth fields")
            updated += 1
            continue

        lang = orig_lang if orig_lang in ("ru", "en") else "en"
        depth = await _generate_depth(name, personality, appearance or "", scenario or "", lang=lang, mode=mode)

        if not depth:
            logger.warning("  Failed to generate depth for %s", name)
            failed += 1
            await asyncio.sleep(1)
            continue

        # Only update fields that are missing (unless --force)
        updates = {}
        if force or not existing_bs:
            if "backstory" in depth:
                updates["backstory"] = depth["backstory"]
        if force or not existing_hl:
            if "hidden_layers" in depth:
                updates["hidden_layers"] = depth["hidden_layers"]
        if force or not existing_ic:
            if "inner_conflict" in depth:
                updates["inner_conflict"] = depth["inner_conflict"]

        if updates:
            set_clauses = ", ".join(f"{k} = :{k}" for k in updates)
            updates["cid"] = char_id
            async with db_engine.begin() as conn:
                await conn.execute(
                    text(f"UPDATE characters SET {set_clauses}, updated_at = NOW() WHERE id = :cid"),
                    updates,
                )
            updated += 1
            logger.info("  Updated %d fields: %s", len(updates), ", ".join(k for k in updates if k != "cid"))
            for k, v in updates.items():
                if k != "cid":
                    logger.info("    %s: %s", k, v[:100] + "..." if len(v) > 100 else v)
        else:
            skipped += 1

        await asyncio.sleep(2)

    logger.info("\n=== Done: %d updated, %d skipped, %d failed (of %d total) ===",
                updated, skipped, failed, len(characters))


if __name__ == "__main__":
    asyncio.run(main())
