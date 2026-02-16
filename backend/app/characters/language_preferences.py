"""Language preference weights for character types.

Different audiences prefer different character archetypes. This module provides
multipliers that influence initial base_chat_count and daily counter growth,
so homepage sorting naturally reflects per-language popularity.

Based on competitor analysis: SpicyChat, CrushOn, JanitorAI, Chub, Talkie AI.
"""

# ── Setting affinities ─────────────────────────────────────────
# {setting: {lang: multiplier}} — 1.0 = baseline, >1 = boost, <1 = reduce
_SETTING_AFFINITY = {
    "fantasy": {"ru": 1.4, "en": 1.1, "es": 1.2, "fr": 1.2, "de": 1.1},
    "modern":  {"ru": 1.2, "en": 0.9, "es": 1.3, "fr": 1.1, "de": 1.0},
}

# ── Tag affinities ─────────────────────────────────────────────
# Structured tags or free-form tag keywords → per-language multiplier
_TAG_AFFINITY = {
    # Dark romance (huge in RU & ES)
    "yandere":              {"ru": 1.5, "en": 1.0, "es": 1.1, "fr": 1.2, "de": 1.0},
    "villain":              {"ru": 1.3, "en": 1.0, "es": 1.2, "fr": 1.2, "de": 1.1},
    "cold":                 {"ru": 1.3, "en": 0.9, "es": 1.2, "fr": 1.1, "de": 1.0},
    "aggressive":           {"ru": 1.3, "en": 0.9, "es": 1.1, "fr": 1.0, "de": 1.0},
    "mysterious_stranger":  {"ru": 1.3, "en": 1.1, "es": 1.2, "fr": 1.2, "de": 1.1},
    # Anime tropes (big in EN)
    "tsundere":             {"ru": 1.0, "en": 1.4, "es": 0.8, "fr": 1.1, "de": 1.0},
    "kuudere":              {"ru": 0.9, "en": 1.3, "es": 0.8, "fr": 1.0, "de": 0.9},
    # Romantic / emotional (ES & FR love this)
    "love_interest":        {"ru": 1.1, "en": 1.0, "es": 1.4, "fr": 1.3, "de": 1.0},
    "flirty":               {"ru": 1.1, "en": 1.0, "es": 1.3, "fr": 1.3, "de": 1.0},
    "emotional":            {"ru": 1.0, "en": 0.9, "es": 1.3, "fr": 1.2, "de": 0.9},
    "shy":                  {"ru": 1.0, "en": 1.2, "es": 1.0, "fr": 1.1, "de": 1.0},
    # General
    "cheerful":             {"ru": 0.8, "en": 1.1, "es": 1.0, "fr": 1.0, "de": 1.0},
    "sarcastic":            {"ru": 1.1, "en": 1.2, "es": 1.0, "fr": 1.1, "de": 1.1},
}

# ── Free-text tag keywords ─────────────────────────────────────
# Matched against comma-separated `tags` field (case-insensitive substring)
_KEYWORD_AFFINITY = {
    # RU-heavy keywords
    "вампир":       {"ru": 1.5, "en": 1.0, "es": 1.2, "fr": 1.3, "de": 1.1},
    "демон":        {"ru": 1.4, "en": 1.0, "es": 1.2, "fr": 1.2, "de": 1.1},
    "оборотень":    {"ru": 1.4, "en": 0.9, "es": 1.1, "fr": 1.1, "de": 1.0},
    "мафи":         {"ru": 1.4, "en": 0.8, "es": 1.2, "fr": 1.1, "de": 0.9},
    "булли":        {"ru": 1.5, "en": 0.9, "es": 1.0, "fr": 1.0, "de": 0.9},
    "ceo":          {"ru": 1.4, "en": 0.8, "es": 1.3, "fr": 1.2, "de": 1.0},
    "похитител":    {"ru": 1.4, "en": 0.9, "es": 1.0, "fr": 1.1, "de": 0.9},
    "яндере":       {"ru": 1.5, "en": 1.0, "es": 0.9, "fr": 1.0, "de": 0.9},
    "сводн":        {"ru": 1.4, "en": 0.8, "es": 1.0, "fr": 1.0, "de": 0.9},
    # EN-heavy keywords
    "аниме":        {"ru": 0.9, "en": 1.4, "es": 0.7, "fr": 1.0, "de": 0.9},
    "кошкодевоч":   {"ru": 0.9, "en": 1.4, "es": 0.7, "fr": 0.9, "de": 0.8},
    "фембой":       {"ru": 0.8, "en": 1.3, "es": 0.6, "fr": 0.8, "de": 0.7},
    "омегаверс":    {"ru": 1.0, "en": 1.3, "es": 0.7, "fr": 0.8, "de": 0.7},
    "монстр":       {"ru": 0.7, "en": 1.3, "es": 0.6, "fr": 0.8, "de": 0.7},
    "киборг":       {"ru": 0.8, "en": 1.3, "es": 0.9, "fr": 1.0, "de": 1.0},
    "кицунэ":       {"ru": 0.9, "en": 1.3, "es": 0.8, "fr": 0.9, "de": 0.8},
    # ES/FR-heavy keywords
    "романтик":     {"ru": 1.0, "en": 0.9, "es": 1.4, "fr": 1.3, "de": 1.0},
    "принц":        {"ru": 1.2, "en": 1.0, "es": 1.3, "fr": 1.3, "de": 1.1},
    "рыцарь":       {"ru": 1.1, "en": 1.0, "es": 1.3, "fr": 1.2, "de": 1.2},
    "друг детства":  {"ru": 1.1, "en": 1.0, "es": 1.3, "fr": 1.2, "de": 1.0},
}

# ── Rating adjustments ──────────────────────────────────────────
_RATING_AFFINITY = {
    "nsfw":     {"ru": 1.2, "en": 1.0, "es": 1.1, "fr": 1.1, "de": 1.0},
    "moderate": {"ru": 1.0, "en": 1.1, "es": 1.1, "fr": 1.1, "de": 1.1},
    "sfw":      {"ru": 0.8, "en": 1.2, "es": 1.0, "fr": 1.0, "de": 1.1},
}

# ── Base ranges ─────────────────────────────────────────────────
# Default random ranges for initial base_chat_count / base_like_count
_BASE_CHAT_RANGE = {"ru": (50, 250), "en": (30, 180), "es": (10, 70), "fr": (10, 60), "de": (8, 50)}
_BASE_LIKE_RANGE = {"ru": (20, 80), "en": (10, 50), "es": (5, 25), "fr": (5, 20), "de": (4, 18)}

# Daily growth increment ranges (before multiplier)
_GROWTH_CHAT_RANGE = {"ru": (4, 14), "en": (3, 10), "es": (1, 6), "fr": (1, 5), "de": (1, 4)}
_GROWTH_LIKE_RANGE = {"ru": (1, 5), "en": (1, 3), "es": (0, 2), "fr": (0, 2), "de": (0, 2)}


def _compute_multiplier(
    setting: str,
    rating: str,
    structured_tags: list[str],
    free_tags: str,
    lang: str,
) -> float:
    """Compute a combined affinity multiplier for a language."""
    mult = 1.0

    # Setting
    if setting in _SETTING_AFFINITY:
        mult *= _SETTING_AFFINITY[setting].get(lang, 1.0)

    # Rating
    if rating in _RATING_AFFINITY:
        mult *= _RATING_AFFINITY[rating].get(lang, 1.0)

    # Structured tags — average of matching tag multipliers
    tag_mults = []
    for tag in structured_tags:
        if tag in _TAG_AFFINITY:
            tag_mults.append(_TAG_AFFINITY[tag].get(lang, 1.0))
    if tag_mults:
        mult *= sum(tag_mults) / len(tag_mults)

    # Free-text tag keywords — best match
    if free_tags:
        tags_lower = free_tags.lower()
        best_kw = 1.0
        for keyword, affinities in _KEYWORD_AFFINITY.items():
            if keyword in tags_lower:
                best_kw = max(best_kw, affinities.get(lang, 1.0))
        mult *= best_kw

    return mult


def get_initial_base_counts(
    setting: str = "",
    rating: str = "nsfw",
    structured_tags: list[str] | None = None,
    free_tags: str = "",
) -> tuple[dict, dict]:
    """Generate initial base_chat_count and base_like_count dicts.

    Returns (base_chat, base_like) where each is {"ru": N, "en": N, "es": N}.
    Values are scaled by language preference multipliers.
    """
    import random

    structured = structured_tags or []
    base_chat = {}
    base_like = {}

    for lang in ("ru", "en", "es", "fr", "de"):
        mult = _compute_multiplier(setting, rating, structured, free_tags, lang)

        lo, hi = _BASE_CHAT_RANGE[lang]
        base_chat[lang] = int(random.randint(lo, hi) * mult)

        lo, hi = _BASE_LIKE_RANGE[lang]
        base_like[lang] = int(random.randint(lo, hi) * mult)

    return base_chat, base_like


def get_growth_increments(
    setting: str = "",
    rating: str = "",
    structured_tags: list[str] | None = None,
    free_tags: str = "",
) -> tuple[dict, dict]:
    """Get daily growth increments for a character, scaled by language preference.

    Returns (chat_increment, like_increment) where each is {"ru": N, "en": N, "es": N}.
    """
    import random

    structured = structured_tags or []
    chat_inc = {}
    like_inc = {}

    for lang in ("ru", "en", "es", "fr", "de"):
        mult = _compute_multiplier(setting, rating, structured, free_tags, lang)

        lo, hi = _GROWTH_CHAT_RANGE[lang]
        chat_inc[lang] = max(1, int(random.randint(lo, hi) * mult))

        lo, hi = _GROWTH_LIKE_RANGE[lang]
        like_inc[lang] = max(0, int(random.randint(lo, hi) * mult))

    return chat_inc, like_inc
