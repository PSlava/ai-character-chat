import re

# Cyrillic → Latin transliteration table
_TRANSLIT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
}


def transliterate(text: str) -> str:
    result = []
    for ch in text:
        lower = ch.lower()
        if lower in _TRANSLIT:
            mapped = _TRANSLIT[lower]
            result.append(mapped.upper() if ch.isupper() and mapped else mapped)
        else:
            result.append(ch)
    return ''.join(result)


def validate_slug(slug: str) -> str:
    """Validate and normalize user-provided slug."""
    slug = slug.strip().lower()
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    if len(slug) < 3:
        raise ValueError("slug_too_short")
    if len(slug) > 50:
        slug = slug[:50].rstrip('-')
    return slug


def generate_slug(name: str, short_id: str) -> str:
    """Generate URL-friendly slug from character name + short ID suffix."""
    text = transliterate(name)
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    if not text:
        text = 'character'
    # Append short ID for uniqueness
    suffix = short_id[:8]
    return f"{text}-{suffix}"
