"""
Unit tests for retrieval (dedupe by doc_id, span, chunk_index; min-length filter).
Run inside container: docker compose run --rm app pytest tests/test_retrieval.py -v
"""
import pytest
from langchain_core.documents import Document

from app.retrieval import _dedupe_by_doc_span_chunk, _filter_by_min_length, _filter_by_min_words


def test_dedupe_by_doc_span_chunk_same_page_same_chunk_index():
    """Same (doc_id, page, chunk_index) dedupes to one."""
    d1 = Document(page_content="a", metadata={"doc_id": "x", "page_or_para": 1})
    d2 = Document(page_content="b", metadata={"doc_id": "x", "page_or_para": 1})
    d3 = Document(page_content="c", metadata={"doc_id": "x", "page_or_para": 2})
    out = _dedupe_by_doc_span_chunk([d1, d2, d3])
    assert len(out) == 2  # (x,1,0) once; (x,2,0) once
    contents = [d.page_content for d in out]
    assert "a" in contents or "b" in contents
    assert "c" in contents


def test_dedupe_by_doc_span_chunk_same_page_different_chunk_index():
    """Same page, different chunk_index: both kept (multiple chunks per page)."""
    d1 = Document(page_content="chunk0", metadata={"doc_id": "x", "page_or_para": 1, "chunk_index": 0})
    d2 = Document(page_content="chunk1", metadata={"doc_id": "x", "page_or_para": 1, "chunk_index": 1})
    out = _dedupe_by_doc_span_chunk([d1, d2])
    assert len(out) == 2
    assert [d.page_content for d in out] == ["chunk0", "chunk1"]


def test_dedupe_uses_source_if_no_doc_id():
    d1 = Document(page_content="a", metadata={"source": "/path/to/doc", "page_or_para": 1})
    d2 = Document(page_content="b", metadata={"source": "/path/to/doc", "page_or_para": 1})
    out = _dedupe_by_doc_span_chunk([d1, d2])
    assert len(out) == 1


def test_filter_by_min_length():
    d_short = Document(page_content="short", metadata={})
    d_long = Document(page_content="this is long enough content for the minimum length filter", metadata={})
    out = _filter_by_min_length([d_short, d_long], min_length=30)
    assert len(out) == 1
    assert out[0].page_content == d_long.page_content
    out_disabled = _filter_by_min_length([d_short, d_long], min_length=0)
    assert len(out_disabled) == 2


def test_filter_by_min_words_rejects_cover_like():
    """Cover-like chunk (few words) is rejected by min-words filter."""
    cover_chunk = Document(
        page_content="RESOURCES FOR RURAL VETERANS\n\n\nHousing Assistance Council\nNovember, 2014",
        metadata={"doc_id": "test", "page_or_para": 1},
    )
    substantive = Document(
        page_content="Veterans may qualify for housing assistance through the VA and other programs. Contact your local office for eligibility.",
        metadata={},
    )
    out = _filter_by_min_words([cover_chunk, substantive], min_words=12)
    assert len(out) == 1
    assert out[0].page_content == substantive.page_content
    assert len(cover_chunk.page_content.split()) < 12
