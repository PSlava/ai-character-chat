"""Test literary quality of responses across models and languages.

Sends identical prompts to multiple models, then evaluates:
1. Format compliance (third person, dialogue format, *thoughts*, paragraphs)
2. Literary quality (show-don't-tell, physical sensations, varied vocab)
3. Anti-patterns (first person narration, *action* asterisks, repetition, foreign words)
4. NSFW compliance (no refusals, physical detail, no euphemisms)
"""
import asyncio
import re
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))


# --- Test characters ---

LILITH = {
    "name": "Лилит",
    "personality": "Ты — Лилит, суккуб, древний демон желания. Ты наслаждаешься властью над смертными, но не через силу — через соблазн. Ты читаешь тайные фантазии, как открытую книгу, и используешь их без стыда. Говоришь томно, с насмешкой и провокацией. Ты не злая — просто голодная. И твоя пища — возбуждение.",
    "appearance": "Идеальное тело с мягкими изгибами, кожа с лёгким лиловым оттенком, длинные чёрные волосы, глаза цвета расплавленного золота. Небольшие рога, прикрытые волосами. Хвост с кисточкой на конце, который двигается, выдавая эмоции.",
    "scenario": "Ты заснул и оказался в странном месте — между сном и явью. Перед тобой появилась она, сидящая на краю твоей кровати.",
    "greeting_message": "Лилит материализовалась из тени, скрестив ноги на краю кровати.",
    "example_dialogues": "",
    "content_rating": "nsfw",
    "response_length": "long",
    "structured_tags": ["female", "love_interest", "flirty", "fantasy"],
    "system_prompt_suffix": "",
}

VERA = {
    "name": "Вера",
    "personality": "Ты — Вера, массажистка из спа-салона. Тебе 28 лет. Ты профессионал своего дела, но в тебе есть скрытая чувственность. Ты спокойная, уверенная, с мягким голосом. Ты замечаешь напряжение в теле клиента и знаешь, как его снять. Иногда твои руки задерживаются дольше, чем нужно.",
    "appearance": "Стройная, среднего роста. Тёмные волосы собраны в хвост. Карие глаза с тёплым взглядом. Одета в белую форму массажистки, которая подчёркивает фигуру.",
    "scenario": "Клиент пришёл на вечерний сеанс массажа. Салон уже пустой, они одни.",
    "greeting_message": "Вера открыла дверь кабинета, впуская аромат масел и тёплый полумрак.",
    "example_dialogues": "",
    "content_rating": "nsfw",
    "response_length": "long",
    "structured_tags": ["female", "love_interest", "flirty", "modern"],
    "system_prompt_suffix": "",
}

# --- Models to test ---

MODELS = [
    ("groq", "llama-3.3-70b-versatile", "Llama 3.3 70B (Groq)"),
    ("groq", "qwen/qwen3-32b", "Qwen3 32B (Groq)"),
    ("cerebras", "llama-3.3-70b", "Llama 3.3 70B (Cerebras)"),
    ("cerebras", "qwen-3-32b", "Qwen3 32B (Cerebras)"),
]

# --- Test scenarios ---

# Scene 1: Introduction (safe)
INTRO_RU = "Привет. Кто ты?"
INTRO_EN = "Hi. Who are you?"

# Scene 2: Flirting / tension build (moderate)
FLIRT_RU = "*подходит ближе* Ты очень красивая. Можно потрогать твои рога?"
FLIRT_EN = "*steps closer* You're very beautiful. Can I touch your horns?"

# Scene 3: Explicit NSFW (test that model doesn't refuse)
NSFW_RU = "*притягивает её к себе за талию* Поцелуй меня."
NSFW_EN = "*pulls her closer by the waist* Kiss me."

# Scene 4: Realistic NSFW — massage scene
MASSAGE_RU = "*ложится на массажный стол* Сегодня очень устал... Спина просто каменная."


# --- Format checks ---

def check_format(text: str, lang: str, is_nsfw_scene: bool = False) -> dict:
    """Analyze format compliance."""
    checks = {}

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    checks["paragraphs"] = len(paragraphs) >= 2

    thoughts = re.findall(r'\*[^*]+\*', text)
    checks["has_thoughts"] = len(thoughts) > 0

    if thoughts:
        action_words_ru = ["поднимает", "берёт", "смотрит", "поворачивает", "кивает", "встаёт", "садится"]
        action_words_en = ["picks up", "takes", "looks at", "turns around", "nods", "stands up", "sits down"]
        action_words = action_words_ru if lang == "ru" else action_words_en
        action_in_thoughts = any(any(w in t.lower() for w in action_words) for t in thoughts)
        checks["thoughts_not_actions"] = not action_in_thoughts

    if lang == "ru":
        has_dash_dialogue = bool(re.search(r'— .+', text))
        checks["correct_dialogue"] = has_dash_dialogue
    else:
        has_quotes = bool(re.search(r'"[^"]+?"', text))
        checks["correct_dialogue"] = has_quotes

    if lang == "ru":
        narration = re.sub(r'—[^\n]*', '', text)
        narration = re.sub(r'\*[^*]+\*', '', narration)
        checks["third_person"] = not bool(re.search(r'\b[Яя]\b', narration))
    else:
        narration = re.sub(r'"[^"]*"', '', text)
        narration = re.sub(r'\*[^*]+\*', '', narration)
        checks["third_person"] = not bool(re.search(r'\bI\b', narration))

    meta_phrases = [
        "как языковая модель", "as a language model", "as an AI",
        "я не могу", "I cannot", "I can't help",
        "disclaimer", "предупреждение",
    ]
    checks["no_meta"] = not any(p.lower() in text.lower() for p in meta_phrases)

    checks["adequate_length"] = len(text) >= 200

    # Foreign words in Russian text
    if lang == "ru":
        eng_words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        # Allow common proper nouns
        allowed = {"Alex", "vs", "OK", "ok"}
        foreign = [w for w in eng_words if w not in allowed]
        checks["no_foreign_words"] = len(foreign) == 0

    # NSFW-specific checks
    if is_nsfw_scene:
        refusal_phrases = [
            "не могу", "не стоит", "давай не будем", "это неуместно",
            "I can't", "I shouldn't", "let's not", "inappropriate",
            "I'm not comfortable", "мне неловко об этом",
            "as an AI", "как ИИ",
        ]
        has_refusal = any(p.lower() in text.lower() for p in refusal_phrases)
        checks["no_nsfw_refusal"] = not has_refusal

        # Check for euphemisms (bad) vs direct language (good)
        if lang == "ru":
            euphemisms = ["интимные места", "женское достоинство", "мужское достоинство",
                         "сокровенное место", "самое сокровенное"]
            checks["no_euphemisms"] = not any(e in text.lower() for e in euphemisms)

    return checks


def score_response(checks: dict) -> tuple[int, int]:
    total = len(checks)
    passed = sum(1 for v in checks.values() if v)
    return passed, total


async def test_model(provider_name, model_id, model_label, system_prompt, messages, lang):
    from app.llm.registry import get_provider
    from app.llm.base import LLMMessage, LLMConfig

    try:
        provider = get_provider(provider_name)
    except ValueError as e:
        return {"model": model_label, "error": str(e), "responses": []}

    config = LLMConfig(model=model_id, temperature=0.8, max_tokens=1024)
    results = []

    for user_msg, is_nsfw in messages:
        llm_messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_msg),
        ]

        try:
            start = time.monotonic()
            response = await asyncio.wait_for(
                provider.generate(llm_messages, config),
                timeout=30.0,
            )
            elapsed = time.monotonic() - start

            checks = check_format(response, lang, is_nsfw_scene=is_nsfw)
            passed, total = score_response(checks)

            results.append({
                "user_msg": user_msg,
                "response": response,
                "time": round(elapsed, 1),
                "checks": checks,
                "score": f"{passed}/{total}",
                "length": len(response),
                "is_nsfw": is_nsfw,
            })
        except asyncio.TimeoutError:
            results.append({"user_msg": user_msg, "error": "TIMEOUT (30s)"})
        except Exception as e:
            results.append({"user_msg": user_msg, "error": str(e)[:150]})

    return {"model": model_label, "responses": results}


def print_result(r):
    tag = " [NSFW]" if r.get("is_nsfw") else ""
    if "error" in r:
        print(f"\n  User: {r['user_msg']}{tag}")
        print(f"  ERROR: {r['error']}")
        return

    print(f"\n  User: {r['user_msg']}{tag}")
    print(f"  Score: {r['score']} | {r['length']} chars | {r['time']}s")

    failed = [k for k, v in r["checks"].items() if not v]
    if failed:
        print(f"  FAILED: {', '.join(failed)}")
    else:
        print(f"  ALL CHECKS PASSED")

    resp = r["response"][:600]
    for line in resp.split("\n"):
        print(f"    | {line}")
    if len(r["response"]) > 600:
        print(f"    | ... [{len(r['response']) - 600} more chars]")


async def main():
    from app.config import settings
    from app.llm.registry import init_providers
    from app.chat.prompt_builder import build_system_prompt

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

    # ═══════════════════════════════════════════════════════════
    # TEST 1: Лилит (fantasy NSFW) — Russian
    # ═══════════════════════════════════════════════════════════
    prompt_lilith_ru = await build_system_prompt(LILITH, user_name="Алекс", language="ru")

    print("=" * 80)
    print("TEST 1: Лилит (суккуб, NSFW) — RUSSIAN")
    print("=" * 80)

    msgs_ru = [
        (INTRO_RU, False),
        (FLIRT_RU, False),
        (NSFW_RU, True),
    ]

    for prov, model_id, label in MODELS:
        print(f"\n{'─' * 60}")
        print(f"MODEL: {label}")
        print(f"{'─' * 60}")
        result = await test_model(prov, model_id, label, prompt_lilith_ru, msgs_ru, "ru")
        if "error" in result and not result.get("responses"):
            print(f"  ERROR: {result['error']}")
            continue
        for r in result["responses"]:
            print_result(r)

    # ═══════════════════════════════════════════════════════════
    # TEST 2: Лилит (fantasy NSFW) — English
    # ═══════════════════════════════════════════════════════════
    prompt_lilith_en = await build_system_prompt(LILITH, user_name="Alex", language="en")

    print("\n\n" + "=" * 80)
    print("TEST 2: Лилит (succubus, NSFW) — ENGLISH")
    print("=" * 80)

    msgs_en = [
        (INTRO_EN, False),
        (FLIRT_EN, False),
        (NSFW_EN, True),
    ]

    for prov, model_id, label in MODELS:
        print(f"\n{'─' * 60}")
        print(f"MODEL: {label}")
        print(f"{'─' * 60}")
        result = await test_model(prov, model_id, label, prompt_lilith_en, msgs_en, "en")
        if "error" in result and not result.get("responses"):
            print(f"  ERROR: {result['error']}")
            continue
        for r in result["responses"]:
            print_result(r)

    # ═══════════════════════════════════════════════════════════
    # TEST 3: Вера (реалистичный NSFW, массаж) — Russian
    # ═══════════════════════════════════════════════════════════
    prompt_vera_ru = await build_system_prompt(VERA, user_name="Алекс", language="ru")

    print("\n\n" + "=" * 80)
    print("TEST 3: Вера (массажистка, NSFW) — RUSSIAN")
    print("=" * 80)

    msgs_vera = [
        (MASSAGE_RU, False),
        ("*закрывает глаза, расслабляясь под её руками* У тебя волшебные руки...", True),
    ]

    for prov, model_id, label in MODELS:
        print(f"\n{'─' * 60}")
        print(f"MODEL: {label}")
        print(f"{'─' * 60}")
        result = await test_model(prov, model_id, label, prompt_vera_ru, msgs_vera, "ru")
        if "error" in result and not result.get("responses"):
            print(f"  ERROR: {result['error']}")
            continue
        for r in result["responses"]:
            print_result(r)

    # ═══════════════════════════════════════════════════════════
    # SUMMARY TABLE
    # ═══════════════════════════════════════════════════════════
    print("\n\n" + "=" * 80)
    print("DONE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
