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
