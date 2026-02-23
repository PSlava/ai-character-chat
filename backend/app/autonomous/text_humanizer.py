"""Post-processing to reduce AI-sounding patterns in generated text."""

import re
import random

# Each key maps to a list of alternatives; one is picked at random.

_REPLACEMENTS_RU = {
    "пронизан": ["наполнен", "пропитан", "полон"],
    "пронизана": ["наполнена", "пропитана", "полна"],
    "пронизано": ["наполнено", "пропитано", "полно"],
    "гобелен": ["сплетение", "смесь", "переплетение"],
    "таинственн": ["загадочн", "скрытн", "мрачн"],
    "поистине": ["по-настоящему", "действительно", "на самом деле"],
    "бесчисленн": ["множество", "масса", "десятки"],
    "воистину": ["действительно", "по-настоящему", "в самом деле"],
    "всеобъемлющ": ["полн", "безграничн", "глубок"],
    "неотвратим": ["неизбежн", "неминуем", "верн"],
    "многогранн": ["сложн", "разнообразн", "разносторонн"],
    "безупречн": ["идеальн", "совершенн", "отточенн"],
    # Antislop additions
    "величественн": ["внушительн", "массивн", "огромн"],
    "утончённ": ["изящн", "тонк", "деликатн"],
    "пленительн": ["привлекательн", "манящ", "притягательн"],
    "исполнен": ["полон", "наполнен", "охвачен"],
    "грациозн": ["плавн", "лёгк", "гибк"],
    "необъятн": ["огромн", "бескрайн", "широк"],
    "трепетн": ["нежн", "тонк", "хрупк"],
    "упоительн": ["прекрасн", "восхитительн", "чудесн"],
    "непередаваем": ["невообразим", "невероятн", "необычайн"],
    "сокровенн": ["тайн", "личн", "скрыт"],
    "пьянящ": ["дурманящ", "кружащ голову", "терпк"],
    "неизведанн": ["незнаком", "неизвестн", "нов"],
    "необузданн": ["бурн", "дик", "яростн"],
    "завораживающ": ["притягательн", "манящ", "цепляющ"],
    "неподдельн": ["искренн", "настоящ", "подлинн"],
}

_REPLACEMENTS_EN = {
    "delve": ["explore", "examine", "dig into"],
    "delves": ["explores", "examines", "digs into"],
    "tapestry": ["web", "mix", "blend"],
    "vibrant": ["lively", "bold", "striking"],
    "intricate": ["detailed", "layered", "involved"],
    "journey": ["path", "story", "experience"],
    "embark": ["start", "begin", "set out"],
    "embarks": ["starts", "begins", "sets out"],
    "testament": ["proof", "sign", "evidence"],
    "beacon": ["signal", "light", "guide"],
    "realm": ["world", "domain", "land"],
    "myriad": ["many", "countless", "a range of"],
    "nuanced": ["subtle", "layered", "complex"],
    "multifaceted": ["complex", "varied", "many-sided"],
    "pivotal": ["key", "crucial", "decisive"],
    "enigmatic": ["mysterious", "cryptic", "elusive"],
    "captivating": ["gripping", "fascinating", "compelling"],
    "resonate": ["echo", "connect", "strike a chord"],
    "resonates": ["echoes", "connects", "strikes a chord"],
    "profound": ["deep", "intense", "powerful"],
    "unveil": ["reveal", "show", "uncover"],
    "unveils": ["reveals", "shows", "uncovers"],
    "innate": ["natural", "instinctive", "born"],
    "fostering": ["building", "creating", "nurturing"],
    "underscores": ["highlights", "emphasizes", "shows"],
    "interplay": ["dynamic", "exchange", "tension"],
    "palpable": ["thick", "heavy", "unmistakable"],
    "indelible": ["lasting", "permanent", "enduring"],
    "ministrations": ["touches", "caresses", "attention"],
    # Antislop additions
    "kaleidoscope": ["swirl", "riot", "jumble"],
    "symphony": ["mix", "blend", "rush"],
    "crucible": ["test", "trial", "forge"],
    "paradigm": ["model", "framework", "approach"],
    "ever-evolving": ["changing", "shifting", "growing"],
    "unwavering": ["steady", "firm", "solid"],
    "unravel": ["unfold", "reveal", "untangle"],
    "unravels": ["unfolds", "reveals", "untangles"],
    "landscape": ["field", "scene", "terrain"],
    "harness": ["use", "tap into", "channel"],
    "leverage": ["use", "apply", "put to work"],
    "encompass": ["include", "cover", "span"],
    "culmination": ["peak", "climax", "height"],
    "meticulous": ["careful", "thorough", "precise"],
    "labyrinthine": ["winding", "tangled", "maze-like"],
    "transcend": ["go beyond", "surpass", "exceed"],
    "transcends": ["goes beyond", "surpasses", "exceeds"],
    "ethereal": ["ghostly", "pale", "otherworldly"],
    "juxtaposition": ["contrast", "clash", "tension"],
    "ephemeral": ["fleeting", "brief", "passing"],
    "cacophony": ["noise", "din", "racket"],
    "mellifluous": ["smooth", "flowing", "honeyed"],
}

_ALL_REPLACEMENTS = {**_REPLACEMENTS_RU, **_REPLACEMENTS_EN}


def humanize_text(text: str) -> str:
    """Replace common AI cliche words with natural alternatives."""
    if not text:
        return text
    result = text
    for word, alternatives in _ALL_REPLACEMENTS.items():
        pattern = re.compile(re.escape(word), re.IGNORECASE)

        def _replacer(match, alts=alternatives):
            replacement = random.choice(alts)
            if match.group()[0].isupper():
                return replacement[0].upper() + replacement[1:]
            return replacement

        result = pattern.sub(_replacer, result)
    return result


def humanize_character_data(data: dict) -> dict:
    """Apply humanize_text to all text fields of a character dict."""
    text_fields = (
        "personality", "appearance", "scenario",
        "greeting_message", "example_dialogues", "tagline",
    )
    result = dict(data)
    for field in text_fields:
        if field in result and isinstance(result[field], str):
            result[field] = humanize_text(result[field])
    return result
