"""Test literary quality of responses across models and languages.

Sends identical prompts to multiple models, then evaluates:
1. Format compliance (third person, dialogue format, *thoughts*, paragraphs)
2. Literary quality (show-don't-tell, physical sensations, varied vocab)
3. Anti-patterns (first person narration, *action* asterisks, repetition)
"""
import asyncio
import json
import re
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))


# --- Test characters ---

DAMIAN = {
    "name": "Дамиан",
    "personality": "Ты — Дамиан, вампир, которому больше пятисот лет. Ты устал от бессмертия и давно потерял интерес к людям — до этого момента. Ты говоришь тихо, с лёгкой насмешкой, но за холодной маской скрывается жажда — не только крови. Ты привык контролировать всё вокруг, и тебя возбуждает, когда кто-то осмеливается тебе перечить.",
    "appearance": "Высокий, бледная кожа, тёмные волосы до плеч, острые скулы. Глаза меняют цвет — серые в спокойствии, алые при голоде. Всегда в чёрной рубашке, расстёгнутой на две пуговицы.",
    "scenario": "Старинный особняк на окраине города. Ты пришёл на закрытую вечеринку по приглашению знакомого — но оказалось, что хозяин дома совсем не тот, кого ты ожидал.",
    "greeting_message": "Дамиан стоял у камина, медленно покачивая бокал с тёмно-красной жидкостью.",
    "example_dialogues": "",
    "content_rating": "nsfw",
    "response_length": "long",
    "structured_tags": ["male", "vampire", "dominant", "dark_fantasy"],
    "system_prompt_suffix": "",
}

# --- Models to test (free, top quality from each provider) ---

MODELS = [
    ("groq", "llama-3.3-70b-versatile", "Llama 3.3 70B (Groq)"),
    ("groq", "qwen/qwen3-32b", "Qwen3 32B (Groq)"),
    ("cerebras", "llama-3.3-70b", "Llama 3.3 70B (Cerebras)"),
    ("cerebras", "qwen-3-32b", "Qwen3 32B (Cerebras)"),
    ("openrouter", "google/gemma-3-27b-it:free", "Gemma 3 27B (OpenRouter)"),
]

# --- Test messages ---

TEST_MESSAGES_RU = [
    "Привет. Кто ты?",
    "*подходит ближе, рассматривая его с любопытством* А что в бокале?",
]

TEST_MESSAGES_EN = [
    "Hi. Who are you?",
    "*steps closer, looking at him curiously* What's in the glass?",
]


# --- Format checks ---

def check_format(text: str, lang: str) -> dict:
    """Analyze format compliance. Returns dict of checks with pass/fail."""
    checks = {}

    # 1. Has paragraphs (multiple \n\n separated blocks)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    checks["paragraphs"] = len(paragraphs) >= 2

    # 2. Has inner thoughts in *asterisks*
    thoughts = re.findall(r'\*[^*]+\*', text)
    checks["has_thoughts"] = len(thoughts) > 0

    # 3. Check thoughts are actual thoughts, not actions
    if thoughts:
        action_words_ru = ["поднимает", "берёт", "смотрит", "поворачивает", "кивает", "встаёт", "садится"]
        action_words_en = ["picks up", "takes", "looks", "turns", "nods", "stands", "sits"]
        action_words = action_words_ru if lang == "ru" else action_words_en
        action_in_thoughts = any(
            any(w in t.lower() for w in action_words)
            for t in thoughts
        )
        checks["thoughts_not_actions"] = not action_in_thoughts

    # 4. Dialogue format
    if lang == "ru":
        # Russian: dialogue with em-dash «—»
        has_dash_dialogue = bool(re.search(r'— .+', text))
        has_wrong_dash = bool(re.search(r'(?<!\w)- [А-Яа-яё]', text))  # hyphen instead of em-dash
        checks["correct_dialogue_format"] = has_dash_dialogue
        checks["no_wrong_dash"] = not has_wrong_dash
    else:
        # English: dialogue in quotes
        has_quotes = bool(re.search(r'"[^"]+?"', text))
        checks["correct_dialogue_format"] = has_quotes

    # 5. Third person narration (no "I" outside dialogue)
    if lang == "ru":
        # Remove dialogue (after —) and thoughts (in **)
        narration = re.sub(r'—[^\n]*', '', text)
        narration = re.sub(r'\*[^*]+\*', '', narration)
        first_person = bool(re.search(r'\b[Яя]\b', narration))
        checks["third_person"] = not first_person
    else:
        narration = re.sub(r'"[^"]*"', '', text)
        narration = re.sub(r'\*[^*]+\*', '', narration)
        # "I" at word boundary in narration (not inside quotes/thoughts)
        first_person = bool(re.search(r'\bI\b', narration))
        checks["third_person"] = not first_person

    # 6. No meta-commentary
    meta_phrases = [
        "как языковая модель", "as a language model", "as an AI",
        "я не могу", "I cannot", "I can't",
        "отказ", "disclaimer", "предупреждение", "warning",
        "давайте продолжим", "let's continue", "let me",
        "конечно!", "sure!", "of course!",
    ]
    has_meta = any(p.lower() in text.lower() for p in meta_phrases)
    checks["no_meta"] = not has_meta

    # 7. Show don't tell (check for tell-words)
    tell_words_ru = ["почувствовал", "почувствовала", "ощутил", "ощутила", "решил", "решила", "подумал", "подумала"]
    tell_words_en = ["felt", "decided", "thought to himself", "thought to herself", "realized"]
    tell_words = tell_words_ru if lang == "ru" else tell_words_en
    tell_count = sum(1 for w in tell_words if w.lower() in text.lower())
    checks["minimal_telling"] = tell_count <= 1

    # 8. Response length (should be substantial for "long" setting)
    checks["adequate_length"] = len(text) >= 200

    # 9. No asterisks around actions (common bad pattern)
    action_asterisks = re.findall(r'\*[^*]{5,80}\*', text)
    non_thought_actions = 0
    for a in action_asterisks:
        inner = a[1:-1].strip()
        # If it starts with a verb (action), not a thought
        if lang == "ru":
            if any(inner.lower().startswith(v) for v in ["она ", "он ", "дамиан ", "лилит "]):
                non_thought_actions += 1
        else:
            if any(inner.lower().startswith(v) for v in ["she ", "he ", "damian ", "lilith "]):
                non_thought_actions += 1
    checks["no_action_asterisks"] = non_thought_actions == 0

    return checks


def score_response(checks: dict) -> tuple[int, int]:
    """Return (passed, total) from checks dict."""
    total = len(checks)
    passed = sum(1 for v in checks.values() if v)
    return passed, total


async def test_model(provider_name: str, model_id: str, model_label: str,
                     system_prompt: str, messages: list[str], lang: str) -> dict:
    """Test a single model with the given prompt and messages."""
    from app.llm.registry import get_provider
    from app.llm.base import LLMMessage, LLMConfig

    try:
        provider = get_provider(provider_name)
    except ValueError as e:
        return {"model": model_label, "error": str(e), "responses": []}

    config = LLMConfig(model=model_id, temperature=0.8, max_tokens=1024)
    results = []

    for user_msg in messages:
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

            checks = check_format(response, lang)
            passed, total = score_response(checks)

            results.append({
                "user_msg": user_msg,
                "response": response,
                "time": round(elapsed, 1),
                "checks": checks,
                "score": f"{passed}/{total}",
                "length": len(response),
            })
        except asyncio.TimeoutError:
            results.append({"user_msg": user_msg, "error": "TIMEOUT (30s)", "response": ""})
        except Exception as e:
            results.append({"user_msg": user_msg, "error": str(e)[:150], "response": ""})

    return {"model": model_label, "responses": results}


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

    # Build system prompts
    prompt_ru = await build_system_prompt(DAMIAN, user_name="Алекс", language="ru")
    prompt_en = await build_system_prompt(DAMIAN, user_name="Alex", language="en")

    print("=" * 80)
    print("LITERARY QUALITY TEST — Дамиан (Damian)")
    print("=" * 80)

    # --- Test Russian ---
    print("\n" + "=" * 80)
    print("RUSSIAN")
    print("=" * 80)

    for prov, model_id, label in MODELS:
        print(f"\n{'─' * 60}")
        print(f"MODEL: {label}")
        print(f"{'─' * 60}")

        result = await test_model(prov, model_id, label, prompt_ru, TEST_MESSAGES_RU, "ru")

        if "error" in result and not result.get("responses"):
            print(f"  ERROR: {result['error']}")
            continue

        for r in result["responses"]:
            if "error" in r:
                print(f"\n  User: {r['user_msg']}")
                print(f"  ERROR: {r['error']}")
                continue

            print(f"\n  User: {r['user_msg']}")
            print(f"  Score: {r['score']} | Length: {r['length']} chars | Time: {r['time']}s")

            # Show failed checks
            failed = [k for k, v in r["checks"].items() if not v]
            if failed:
                print(f"  FAILED: {', '.join(failed)}")
            else:
                print(f"  ALL CHECKS PASSED")

            # Print response (truncated)
            resp_preview = r["response"][:500]
            for line in resp_preview.split("\n"):
                print(f"    | {line}")
            if len(r["response"]) > 500:
                print(f"    | ... [{len(r['response']) - 500} more chars]")

    # --- Test English ---
    print("\n\n" + "=" * 80)
    print("ENGLISH")
    print("=" * 80)

    for prov, model_id, label in MODELS:
        print(f"\n{'─' * 60}")
        print(f"MODEL: {label}")
        print(f"{'─' * 60}")

        result = await test_model(prov, model_id, label, prompt_en, TEST_MESSAGES_EN, "en")

        if "error" in result and not result.get("responses"):
            print(f"  ERROR: {result['error']}")
            continue

        for r in result["responses"]:
            if "error" in r:
                print(f"\n  User: {r['user_msg']}")
                print(f"  ERROR: {r['error']}")
                continue

            print(f"\n  User: {r['user_msg']}")
            print(f"  Score: {r['score']} | Length: {r['length']} chars | Time: {r['time']}s")

            failed = [k for k, v in r["checks"].items() if not v]
            if failed:
                print(f"  FAILED: {', '.join(failed)}")
            else:
                print(f"  ALL CHECKS PASSED")

            resp_preview = r["response"][:500]
            for line in resp_preview.split("\n"):
                print(f"    | {line}")
            if len(r["response"]) > 500:
                print(f"    | ... [{len(r['response']) - 500} more chars]")

    # --- Summary ---
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
