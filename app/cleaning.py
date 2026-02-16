"""
Conservative text cleaning (no semantic destruction).
- Unicode NFKC
- \\s+ -> single space within lines
- Collapse \\n{3,} -> max 2 newlines (configurable)
"""
import re
import unicodedata
from typing import Any

from app.config import settings


def normalize_unicode(text: str) -> str:
    """NFKC normalization for consistency."""
    return unicodedata.normalize("NFKC", text)


def collapse_spaces(text: str) -> str:
    """Replace runs of whitespace with a single space within lines."""
    return re.sub(r"[ \t]+", " ", text)


def collapse_newlines(text: str, max_consecutive: int | None = None) -> str:
    """Collapse 3+ newlines to at most max_consecutive (default from settings)."""
    if max_consecutive is None:
        max_consecutive = settings.clean_max_consecutive_newlines
    pattern = r"\n{" + str(max_consecutive + 1) + r",}"
    replacement = "\n" * max_consecutive
    return re.sub(pattern, replacement, text)


def clean_text(text: str, max_consecutive_newlines: int | None = None) -> str:
    """
    Full conservative cleaning pipeline.
    Preserves semantics; avoids aggressive punctuation removal that hurts embeddings.
    """
    if not text or not text.strip():
        return ""
    t = normalize_unicode(text)
    t = collapse_spaces(t)
    t = collapse_newlines(t, max_consecutive_newlines)
    return t.strip()
