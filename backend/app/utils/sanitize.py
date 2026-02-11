"""Simple HTML tag stripper for defense-in-depth. No external dependencies."""
import re

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text. Keeps the text content inside tags."""
    return _HTML_TAG_RE.sub("", text)
