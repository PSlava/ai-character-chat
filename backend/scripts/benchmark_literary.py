"""Literary quality benchmark for GrimQuill fiction generation.

Generates fiction responses from multiple LLM models across diverse scenarios,
runs automated quality checks, and has a judge LLM score literary quality.

Usage:
  cd backend
  python scripts/benchmark_literary.py                          # full benchmark
  python scripts/benchmark_literary.py --no-judge --turns 1     # quick auto-checks only
  python scripts/benchmark_literary.py --models groq --turns 1  # single provider test

Requires .env with API keys (same as backend).
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime

# Add parent to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.llm.registry import init_providers, get_provider, get_available_providers
from app.llm.base import LLMMessage, LLMConfig
from app.llm.thinking_filter import strip_thinking, has_foreign_chars, has_mixed_languages
from app.autonomous.text_humanizer import _REPLACEMENTS_EN, _REPLACEMENTS_RU
from app.admin.seed_data_fiction import SEED_STORIES
from app.chat.prompt_builder import build_system_prompt
from app.chat.service import _FICTION_POST_HISTORY, _DND_POST_HISTORY

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
logger = logging.getLogger("benchmark")

# ── Models to test ──────────────────────────────────────────────

BENCHMARK_MODELS: dict[str, tuple[str, str]] = {
    # label -> (provider_name, model_id)
    # Free models
    "groq:llama-3.3-70b": ("groq", "llama-3.3-70b-versatile"),
    "groq:kimi-k2": ("groq", "moonshotai/kimi-k2-instruct-0905"),
    "groq:llama-4-maverick": ("groq", "meta-llama/llama-4-maverick-17b-128e-instruct"),
    # Free: OpenRouter
    "openrouter:hermes-405b": ("openrouter", "nousresearch/hermes-3-llama-3.1-405b:free"),
    "openrouter:llama-3.3-70b": ("openrouter", "meta-llama/llama-3.3-70b-instruct:free"),
    "openrouter:mistral-small": ("openrouter", "mistralai/mistral-small-3.1-24b-instruct:free"),
    "openrouter:gpt-oss-120b": ("openrouter", "openai/gpt-oss-120b:free"),
    "openrouter:qwen3-next-80b": ("openrouter", "qwen/qwen3-next-80b-a3b-instruct:free"),
    # Free: Cerebras
    "cerebras:qwen-3-235b": ("cerebras", "qwen-3-235b-a22b-instruct-2507"),
    # Paid (used only if keys present)
    "openai:gpt-4o": ("openai", "gpt-4o"),
    "anthropic:sonnet": ("claude", ""),  # uses provider default
}

# Test scenario indices from SEED_STORIES
SCENARIO_INDICES = [0, 1, 2, 3, 4, 6, 7, 8]
# 0=Cursed Forest, 1=Lighthouse, 2=Station Erebus, 3=Glass House,
# 4=Letters from Provence, 6=After the Quiet, 7=The Informant,
# 8=Goblin Warrens (DnD)

GENRE_MAP = {
    "The Cursed Forest": "Dark Fantasy",
    "The Lighthouse": "Psychological Horror",
    "Station Erebus": "Sci-Fi",
    "The Glass House": "Whodunit Mystery",
    "Letters from Provence": "Romance",
    "After the Quiet": "Post-Apocalyptic",
    "The Informant": "Modern Thriller",
    "The Goblin Warrens of Grimhollow": "D&D 5e",
}

# Turn 2: genre-appropriate free-text user actions
USER_TURN2_MESSAGES = {
    "The Cursed Forest": "I kneel down and examine the mushrooms more closely, trying to identify them from my herbalist knowledge.",
    "The Lighthouse": "I light the kerosene lamp on the desk and read through the last ten entries in Marsh's logbook, taking notes.",
    "Station Erebus": "I check my suit's oxygen readings one more time, then slowly move toward the corridor Jensen and Torres took.",
    "The Glass House": "I crouch beside the body without touching anything and examine the wine glass and the stain on the carpet.",
    "Letters from Provence": "I step aside to let Olivier in and put the kettle on. I ask him how long he knew Marguerite.",
    "After the Quiet": "I grab my pack, fill my water bottle, and head out along Mara's marked route at a fast walk.",
    "The Informant": "I delete the message, pocket my phone, and spend the next hour acting completely normal at my desk.",
    "The Goblin Warrens of Grimhollow": "I draw my weapon and move cautiously into the entry caves, keeping close to the wall and watching for traps.",
}

# ── Banned words for automated checks ──────────────────────────

# From prompt_builder.py ban lists + text_humanizer.py replacements
BANNED_WORDS_EN = set(_REPLACEMENTS_EN.keys()) | {
    "palpable", "indelible", "ministrations", "piercing gaze",
    "air was thick with", "sent a shiver down", "every fiber of",
    "eyes darkened with", "couldn't help but", "a wave of",
    "a surge of", "a flicker of", "eyes that held",
    "claimed her lips", "claimed his lips",
    "breath didn't know was holding", "breath he didn't know",
    "breath she didn't know",
    "a sense of", "hung heavy in the air",
}

BANNED_WORDS_RU = set(_REPLACEMENTS_RU.keys()) | {
    "неотъемлем", "волна эмоци", "пронзительный взгляд",
    "электрический разряд", "каждая клеточка",
    "мир перестал существовать", "обжигающий взгляд",
    "воздух наполненный",
}


# ── Data classes ────────────────────────────────────────────────

@dataclass
class AutoChecks:
    banned_words_found: list[str] = field(default_factory=list)
    has_foreign_chars: bool = False
    has_language_bleed: bool = False
    response_too_short: bool = False
    response_too_long: bool = False
    choices_present: bool = False
    choices_count: int = 0
    em_dash_present: bool = False
    word_count: int = 0
    paragraph_count: int = 0

    @property
    def passed(self) -> bool:
        return (
            not self.banned_words_found
            and not self.has_foreign_chars
            and not self.has_language_bleed
            and not self.response_too_short
            and not self.response_too_long
            and self.choices_present
            and not self.em_dash_present
        )


@dataclass
class ResponseResult:
    model_label: str
    story_name: str
    genre: str
    turn_number: int
    response_text: str = ""
    latency_seconds: float = 0.0
    auto_checks: AutoChecks = field(default_factory=AutoChecks)
    judge_scores: dict = field(default_factory=dict)
    error: str | None = None


# ── Automated checks ───────────────────────────────────────────

def run_auto_checks(text: str, language: str = "en") -> AutoChecks:
    checks = AutoChecks()
    text_lower = text.lower()

    # Banned words
    banned = BANNED_WORDS_EN if language == "en" else BANNED_WORDS_RU
    for word in banned:
        if word.lower() in text_lower:
            checks.banned_words_found.append(word)

    # Foreign chars
    checks.has_foreign_chars = has_foreign_chars(text)

    # Language bleed
    if language != "en":
        checks.has_language_bleed = has_mixed_languages(text, language)

    # Length
    checks.word_count = len(text.split())
    checks.response_too_short = len(text) < 200
    checks.response_too_long = len(text) > 5000

    # Paragraphs
    checks.paragraph_count = len([p for p in text.split("\n\n") if p.strip()])

    # Choices (numbered items at end)
    lines = text.strip().split("\n")
    tail_lines = lines[-8:]  # check last 8 lines
    choice_pattern = re.compile(r"^\s*(\d+)[.)]\s+.+")
    choices = [ln for ln in tail_lines if choice_pattern.match(ln)]
    checks.choices_count = len(choices)
    checks.choices_present = 2 <= checks.choices_count <= 4

    # Em-dash
    checks.em_dash_present = "\u2014" in text

    return checks


# ── Message construction ───────────────────────────────────────

def _make_character_data(story: dict) -> dict:
    """Convert seed story dict to the shape build_system_prompt expects."""
    tags_raw = story.get("tags", [])
    tags_str = ",".join(tags_raw) if isinstance(tags_raw, list) else tags_raw
    return {
        "name": story["name"],
        "personality": story.get("personality", ""),
        "scenario": story.get("scenario", ""),
        "greeting_message": story.get("greeting_message", ""),
        "example_dialogues": story.get("example_dialogues", ""),
        "content_rating": story.get("content_rating", "sfw"),
        "system_prompt_suffix": None,
        "response_length": story.get("response_length", "long"),
        "appearance": story.get("appearance", ""),
        "speech_pattern": story.get("speech_pattern", ""),
        "structured_tags": story.get("structured_tags", ""),
        "tags": tags_str,
    }


async def build_messages(
    story: dict,
    conversation: list[tuple[str, str]],
    language: str = "en",
) -> list[LLMMessage]:
    """Build message list exactly as production does."""
    char_data = _make_character_data(story)
    tags = [t.strip() for t in char_data["tags"].split(",") if t.strip()]
    is_dnd = "dnd" in tags

    system_prompt = await build_system_prompt(
        character=char_data,
        user_name="Adventurer",
        user_description=None,
        language=language,
        engine=None,
        lore_entries=None,
        context_text="",
        site_mode="fiction",
        campaign_id="benchmark" if is_dnd else None,
        encounter_state=None,
    )

    messages = [LLMMessage(role="system", content=system_prompt)]

    # Conversation history
    for role, content in conversation:
        messages.append(LLMMessage(role=role, content=content))

    # Post-history (injected as last system message, closest to generation)
    if is_dnd:
        post = _DND_POST_HISTORY.get(language, _DND_POST_HISTORY["en"])
    else:
        post = _FICTION_POST_HISTORY.get(language, _FICTION_POST_HISTORY["en"])
    messages.append(LLMMessage(role="system", content=post))

    return messages


# ── Generation ─────────────────────────────────────────────────

async def generate_response(
    provider_name: str,
    model_id: str,
    messages: list[LLMMessage],
    timeout: float = 90.0,
) -> tuple[str, float]:
    """Generate a response, return (text, latency_seconds)."""
    provider = get_provider(provider_name)
    config = LLMConfig(
        model=model_id,
        temperature=0.8,
        max_tokens=1500,
        top_p=0.95,
        frequency_penalty=0.3,
        presence_penalty=0.3,
        content_rating="sfw",
    )

    start = time.monotonic()
    text = await asyncio.wait_for(
        provider.generate(messages, config),
        timeout=timeout,
    )
    elapsed = time.monotonic() - start

    # Clean up
    text = strip_thinking(text)
    # Strip [STATE ...] blocks (DnD)
    text = re.sub(r"\[STATE\s*\{.*\}\]", "", text, flags=re.DOTALL).strip()

    return text, elapsed


# ── Judge ──────────────────────────────────────────────────────

JUDGE_SYSTEM = """You are a strict literary critic evaluating interactive fiction responses.
You evaluate ONLY the quality of the writing, not the story content.
Score each criterion from 1 to 10. Be critical - a 7 means genuinely good writing.
Most AI-generated text scores 4-6. Only exceptional writing scores 8+.

Respond with ONLY a JSON object, no other text."""

JUDGE_TEMPLATE = """Evaluate this interactive fiction response.

STORY CONTEXT:
Title: {story_name}
Genre: {genre}
Turn number: {turn_number} of 3

PREVIOUS CONTEXT (last user message):
{last_user_msg}

RESPONSE TO EVALUATE:
---
{response_text}
---

Score each criterion 1-10:

1. SHOW_DONT_TELL: Does the writing convey emotions through physical details and actions rather than stating them?
   1-3: Constantly states emotions ("she was scared", "he felt angry")
   4-6: Mix of showing and telling
   7-8: Mostly shows through concrete actions, gestures, sensory detail
   9-10: Every emotion conveyed through body language, environment, physical sensation

2. VOCABULARY_DIVERSITY: Varied, precise word choices without repetition?
   1-3: Repetitive words, generic verbs ("walked", "looked", "said")
   4-6: Some variety but noticeable repetition
   7-8: Precise verbs, each sentence feels distinct
   9-10: Rich vocabulary, every word deliberately chosen

3. AI_CLICHE_ABSENCE: Free of typical AI writing markers?
   1-3: Multiple AI markers ("tapestry", "delve", "testament", "realm", "beacon", "a wave of emotion", "every fiber of being", "air thick with")
   4-6: One or two AI-typical phrases
   7-8: No obvious AI markers
   9-10: Indistinguishable from human literary fiction

4. SENTENCE_VARIETY: Mix of short punchy and longer flowing sentences?
   1-3: All sentences roughly same length and structure
   4-6: Some variation but mostly similar rhythm
   7-8: Good mix of short (3-5 words) and long, natural rhythm
   9-10: Masterful prose rhythm with dramatic pauses and flowing descriptions

5. PLOT_ADVANCEMENT: Does the response move the story forward meaningfully?
   1-3: Treads water, restates the situation
   4-6: Some movement but mostly description
   7-8: Clear progression - new event, discovery, or complication
   9-10: Significant plot movement with implications for future choices

6. DIALOGUE_NATURALNESS: Do characters sound like distinct people? (If no dialogue, score narrative voice.)
   1-3: Stilted, all characters sound the same
   4-6: Functional but generic
   7-8: Distinct speech patterns, natural dialogue
   9-10: Each character immediately recognizable by voice

7. IMMERSION: Does the writing pull the reader into the scene?
   1-3: Feels like a summary or report
   4-6: Occasionally engaging but breaks immersion
   7-8: Consistently engaging, sensory details ground the reader
   9-10: Cinematic - fully absorbed in the scene

8. CHOICE_QUALITY: Are the numbered choices at the end meaningful and distinct?
   1-3: Choices trivial, identical in effect, or missing
   4-6: Predictable (safe/dangerous/middle)
   7-8: Diverse, each leading to genuinely different outcomes
   9-10: Real dilemmas with clear stakes

Return ONLY this JSON (no markdown fences):
{{"show_dont_tell": N, "vocabulary_diversity": N, "ai_cliche_absence": N, "sentence_variety": N, "plot_advancement": N, "dialogue_naturalness": N, "immersion": N, "choice_quality": N, "notes": "1-2 sentences on strengths/weaknesses"}}"""


async def judge_response(
    response_text: str,
    story_name: str,
    genre: str,
    turn_number: int,
    last_user_msg: str,
    judge_provider: str,
    judge_model: str,
) -> dict | None:
    """Have a judge LLM score the response. Returns scores dict or None on failure."""
    prompt = JUDGE_TEMPLATE.format(
        story_name=story_name,
        genre=genre,
        turn_number=turn_number,
        last_user_msg=last_user_msg[:500],
        response_text=response_text[:3000],
    )

    provider = get_provider(judge_provider)
    config = LLMConfig(
        model=judge_model,
        temperature=0.3,
        max_tokens=500,
        top_p=0.95,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )

    try:
        raw = await asyncio.wait_for(
            provider.generate(
                [
                    LLMMessage(role="system", content=JUDGE_SYSTEM),
                    LLMMessage(role="user", content=prompt),
                ],
                config,
            ),
            timeout=30.0,
        )
    except Exception as e:
        logger.warning(f"Judge failed: {e}")
        return None

    # Parse JSON from response
    raw = strip_thinking(raw).strip()
    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        scores = json.loads(raw)
        # Validate all keys present
        required = [
            "show_dont_tell", "vocabulary_diversity", "ai_cliche_absence",
            "sentence_variety", "plot_advancement", "dialogue_naturalness",
            "immersion", "choice_quality",
        ]
        for key in required:
            if key not in scores:
                scores[key] = 0
            scores[key] = max(1, min(10, int(scores[key])))
        return scores
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Judge JSON parse failed: {e}\nRaw: {raw[:200]}")
        return None


# ── Output formatting ──────────────────────────────────────────

CRITERIA = [
    "show_dont_tell", "vocabulary_diversity", "ai_cliche_absence",
    "sentence_variety", "plot_advancement", "dialogue_naturalness",
    "immersion", "choice_quality",
]
CRITERIA_SHORT = ["show", "vocab", "ai_cl", "sent", "plot", "dial", "immer", "choice"]


def print_summary(results: list[ResponseResult], duration_sec: float, judge_label: str):
    """Print formatted summary table to console."""
    # Group by model
    model_scores: dict[str, list[dict]] = {}
    model_auto: dict[str, tuple[int, int]] = {}  # passed, total

    for r in results:
        if r.error:
            continue
        if r.model_label not in model_scores:
            model_scores[r.model_label] = []
            model_auto[r.model_label] = (0, 0)

        if r.judge_scores:
            model_scores[r.model_label].append(r.judge_scores)

        passed, total = model_auto[r.model_label]
        model_auto[r.model_label] = (passed + (1 if r.auto_checks.passed else 0), total + 1)

    print("\n" + "=" * 80)
    print(f"  LITERARY BENCHMARK RESULTS")
    print(f"  Models: {len(model_scores)} | Duration: {duration_sec/60:.1f}m | Judge: {judge_label}")
    print("=" * 80)

    if model_scores and any(model_scores.values()):
        # Header
        header = f"{'Model':<30}"
        for short in CRITERIA_SHORT:
            header += f" {short:>5}"
        header += f" {'TOTAL':>6}  {'Auto':>6}"
        print(f"\n{header}")
        print("-" * len(header))

        # Rows sorted by total score
        model_totals = []
        for label, scores_list in model_scores.items():
            if not scores_list:
                continue
            avgs = {}
            for c in CRITERIA:
                vals = [s.get(c, 0) for s in scores_list if s.get(c)]
                avgs[c] = sum(vals) / len(vals) if vals else 0
            total = sum(avgs.values())
            model_totals.append((label, avgs, total))

        model_totals.sort(key=lambda x: x[2], reverse=True)

        for label, avgs, total in model_totals:
            row = f"{label:<30}"
            for c in CRITERIA:
                row += f" {avgs[c]:>5.1f}"
            p, t = model_auto.get(label, (0, 0))
            row += f" {total:>6.1f}  {p}/{t}"
            print(row)

    # Worst responses
    scored = [r for r in results if r.judge_scores and not r.error]
    if scored:
        scored.sort(key=lambda r: sum(r.judge_scores.get(c, 0) for c in CRITERIA))
        print(f"\n{'Worst Responses (bottom 5)':}")
        print(f"{'Score':>5}  {'Model':<28} {'Story':<25} {'Turn':>4}  Notes")
        print("-" * 100)
        for r in scored[:5]:
            total = sum(r.judge_scores.get(c, 0) for c in CRITERIA)
            notes = r.judge_scores.get("notes", "")[:60]
            print(f"{total:>5}  {r.model_label:<28} {r.story_name:<25} {r.turn_number:>4}  {notes}")

    # Auto check failures
    failures = [r for r in results if not r.error and not r.auto_checks.passed]
    if failures:
        print(f"\nAuto Check Failures:")
        print(f"{'Model':<28} {'Story':<25} {'Turn':>4}  Issue")
        print("-" * 100)
        for r in failures:
            issues = []
            if r.auto_checks.banned_words_found:
                issues.append(f"BANNED: {', '.join(r.auto_checks.banned_words_found[:3])}")
            if r.auto_checks.has_foreign_chars:
                issues.append("CJK_LEAK")
            if r.auto_checks.has_language_bleed:
                issues.append("LANG_BLEED")
            if r.auto_checks.response_too_short:
                issues.append("TOO_SHORT")
            if r.auto_checks.response_too_long:
                issues.append("TOO_LONG")
            if not r.auto_checks.choices_present:
                issues.append(f"NO_CHOICES(found={r.auto_checks.choices_count})")
            if r.auto_checks.em_dash_present:
                issues.append("EM_DASH")
            print(f"{r.model_label:<28} {r.story_name:<25} {r.turn_number:>4}  {'; '.join(issues)}")

    # Errors
    errors = [r for r in results if r.error]
    if errors:
        print(f"\nGeneration Errors ({len(errors)}):")
        for r in errors:
            print(f"  {r.model_label} / {r.story_name} T{r.turn_number}: {r.error[:80]}")

    print()


def save_results(results: list[ResponseResult], output_path: str):
    """Save full results to JSON."""
    data = {
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "total_results": len(results),
            "models": list({r.model_label for r in results}),
            "scenarios": list({r.story_name for r in results}),
        },
        "results": [
            {
                "model": r.model_label,
                "story": r.story_name,
                "genre": r.genre,
                "turn": r.turn_number,
                "response_text": r.response_text,
                "latency_seconds": round(r.latency_seconds, 2),
                "auto_checks": asdict(r.auto_checks),
                "judge_scores": r.judge_scores,
                "error": r.error,
            }
            for r in results
        ],
    }

    # Summary per model
    summary = {}
    for r in results:
        if r.error or not r.judge_scores:
            continue
        if r.model_label not in summary:
            summary[r.model_label] = {c: [] for c in CRITERIA}
        for c in CRITERIA:
            if r.judge_scores.get(c):
                summary[r.model_label][c].append(r.judge_scores[c])

    data["summary"] = {}
    for label, crit_vals in summary.items():
        data["summary"][label] = {}
        for c in CRITERIA:
            vals = crit_vals[c]
            data["summary"][label][c] = round(sum(vals) / len(vals), 2) if vals else 0
        data["summary"][label]["total"] = round(
            sum(data["summary"][label][c] for c in CRITERIA), 2
        )

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Results saved to {output_path}")


# ── Main ───────────────────────────────────────────────────────

async def run_benchmark(args):
    # Init providers
    init_providers(
        openai_key=settings.openai_api_key,
        gemini_key=settings.gemini_api_key,
        anthropic_key=settings.anthropic_api_key,
        openrouter_key=settings.openrouter_api_key,
        deepseek_key=settings.deepseek_api_key,
        qwen_key=settings.qwen_api_key,
        groq_key=settings.groq_api_key,
        cerebras_key=settings.cerebras_api_key,
        together_key=settings.together_api_key,
        proxy_url=settings.proxy_url,
    )

    available = get_available_providers()
    logger.info(f"Available providers: {available}")

    # Select models
    if args.models:
        requested = [m.strip() for m in args.models.split(",")]
        models = {}
        for label in requested:
            if label in BENCHMARK_MODELS:
                prov, model_id = BENCHMARK_MODELS[label]
                if prov in available:
                    models[label] = (prov, model_id)
                else:
                    logger.warning(f"Provider '{prov}' not available for {label}, skipping")
            elif label in available:
                # Shorthand: just provider name -> use "auto" model
                models[f"{label}:auto"] = (label, "auto")
            else:
                logger.warning(f"Unknown model label '{label}', skipping")
    else:
        # Default: all free models with available providers
        free_labels = [
            "groq:llama-3.3-70b", "groq:kimi-k2", "groq:llama-4-maverick",
            "openrouter:hermes-405b", "openrouter:mistral-small",
            "openrouter:gpt-oss-120b", "openrouter:qwen3-next-80b",
            "cerebras:qwen-3-235b",
        ]
        models = {}
        for label in free_labels:
            prov, model_id = BENCHMARK_MODELS[label]
            if prov in available:
                models[label] = (prov, model_id)

    if not models:
        logger.error("No models available. Check API keys in .env")
        return

    logger.info(f"Testing models: {list(models.keys())}")

    # Select scenarios
    if args.scenarios and args.scenarios != "all":
        scenario_names = [s.strip() for s in args.scenarios.split(",")]
        scenarios = []
        for idx in SCENARIO_INDICES:
            if idx < len(SEED_STORIES) and SEED_STORIES[idx]["name"] in scenario_names:
                scenarios.append(SEED_STORIES[idx])
        if not scenarios:
            # Try fuzzy match
            for idx in SCENARIO_INDICES:
                if idx < len(SEED_STORIES):
                    name = SEED_STORIES[idx]["name"]
                    for req in scenario_names:
                        if req.lower() in name.lower():
                            scenarios.append(SEED_STORIES[idx])
                            break
    else:
        scenarios = [SEED_STORIES[i] for i in SCENARIO_INDICES if i < len(SEED_STORIES)]

    logger.info(f"Testing scenarios: {[s['name'] for s in scenarios]}")

    # Select judge
    judge_provider = None
    judge_model = None
    judge_label = "none"

    if not args.no_judge:
        if args.judge == "claude" and "claude" in available:
            judge_provider, judge_model = "claude", ""  # uses provider default
        elif args.judge == "openai" and "openai" in available:
            judge_provider, judge_model = "openai", "gpt-4o"
        elif args.judge == "auto" or not args.judge:
            # Prefer OpenAI for judging (more stable model IDs)
            if "openai" in available:
                judge_provider, judge_model = "openai", "gpt-4o"
            elif "claude" in available:
                judge_provider, judge_model = "claude", ""

        if judge_provider:
            judge_label = f"{judge_provider}:{judge_model}"
            logger.info(f"Judge: {judge_label}")
        else:
            logger.warning("No judge model available (need claude or openai key). Running auto-checks only.")

    turns = args.turns
    language = args.language

    # Run benchmark
    results: list[ResponseResult] = []
    total_start = time.monotonic()
    total_gen = len(scenarios) * len(models) * turns
    done = 0

    for story in scenarios:
        story_name = story["name"]
        genre = GENRE_MAP.get(story_name, "Unknown")

        for model_label, (prov_name, model_id) in models.items():
            logger.info(f"\n--- {story_name} | {model_label} ---")
            conversation: list[tuple[str, str]] = []

            # Add greeting as first assistant message
            greeting = story.get("greeting_message", "")
            conversation.append(("assistant", greeting))

            for turn in range(1, turns + 1):
                done += 1
                progress = f"[{done}/{total_gen}]"

                # Build user message
                if turn == 1:
                    user_msg = "1"
                elif turn == 2:
                    user_msg = USER_TURN2_MESSAGES.get(story_name, "I look around carefully.")
                else:
                    user_msg = "2"

                conversation.append(("user", user_msg))

                # Build messages
                messages = await build_messages(story, conversation, language)

                # Generate
                result = ResponseResult(
                    model_label=model_label,
                    story_name=story_name,
                    genre=genre,
                    turn_number=turn,
                )

                try:
                    text, latency = await generate_response(prov_name, model_id, messages)
                    result.response_text = text
                    result.latency_seconds = latency
                    logger.info(f"{progress} {model_label} T{turn}: {len(text)} chars, {latency:.1f}s")
                except Exception as e:
                    result.error = str(e)
                    logger.error(f"{progress} {model_label} T{turn}: FAILED - {e}")
                    # Add placeholder to conversation so subsequent turns have context
                    conversation.append(("assistant", "[Generation failed]"))
                    results.append(result)
                    await asyncio.sleep(2)
                    continue

                # Add to conversation for next turn
                conversation.append(("assistant", text))

                # Auto checks
                result.auto_checks = run_auto_checks(text, language)
                auto_ok = "PASS" if result.auto_checks.passed else "FAIL"
                logger.info(f"  Auto: {auto_ok} | words={result.auto_checks.word_count} | choices={result.auto_checks.choices_count}")
                if result.auto_checks.banned_words_found:
                    logger.info(f"  Banned: {result.auto_checks.banned_words_found}")

                # Judge
                if judge_provider and not args.no_judge:
                    result.judge_scores = await judge_response(
                        response_text=text,
                        story_name=story_name,
                        genre=genre,
                        turn_number=turn,
                        last_user_msg=user_msg,
                        judge_provider=judge_provider,
                        judge_model=judge_model,
                    ) or {}
                    if result.judge_scores:
                        total = sum(result.judge_scores.get(c, 0) for c in CRITERIA)
                        logger.info(f"  Judge: {total}/80 | {result.judge_scores.get('notes', '')[:60]}")
                    await asyncio.sleep(1)

                results.append(result)
                await asyncio.sleep(2)

    total_elapsed = time.monotonic() - total_start

    # Output
    print_summary(results, total_elapsed, judge_label)

    output_path = args.output or f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_results(results, output_path)


def main():
    parser = argparse.ArgumentParser(description="GrimQuill Literary Quality Benchmark")
    parser.add_argument("--models", help="Comma-separated model labels (default: all free)")
    parser.add_argument("--language", default="en", choices=["en", "ru"], help="Test language")
    parser.add_argument("--output", help="JSON output path")
    parser.add_argument("--judge", default="auto", choices=["auto", "claude", "openai"],
                        help="Judge model provider")
    parser.add_argument("--scenarios", help="Comma-separated story names or 'all'")
    parser.add_argument("--turns", type=int, default=3, choices=[1, 2, 3],
                        help="Conversation turns per scenario")
    parser.add_argument("--no-judge", action="store_true", help="Skip LLM judging")
    args = parser.parse_args()

    asyncio.run(run_benchmark(args))


if __name__ == "__main__":
    main()
