"""
Unit tests for text cleaning.
Run inside container: docker compose run --rm app pytest tests/test_cleaning.py -v
"""
import pytest
from app.cleaning import clean_text, collapse_newlines, collapse_spaces, normalize_unicode


def test_normalize_unicode():
    assert normalize_unicode("café") == "café"
    assert len(normalize_unicode("\u00a0")) == 1


def test_collapse_spaces():
    assert collapse_spaces("a   b\t\tc") == "a b c"


def test_collapse_newlines():
    assert collapse_newlines("a\n\n\n\nb", max_consecutive=2) == "a\n\nb"


def test_clean_text_preserves_semantics():
    t = "  Hello   world.\n\n\nNext paragraph.  "
    out = clean_text(t)
    assert "Hello" in out and "world" in out and "Next" in out
    assert "\n\n\n" not in out
