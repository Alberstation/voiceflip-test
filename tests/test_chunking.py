"""
Unit tests for chunking (overlap and row-based).
Run inside container: docker compose run --rm app pytest tests/test_chunking.py -v
"""
import pytest

from app.chunking import chunk_content, overlap_chunk, row_based_chunk


def test_overlap_chunk_basic():
    text = "a " * 100  # ~200 chars
    meta = {"doc_id": "test", "source": "test.docx"}
    chunks = overlap_chunk(text, meta, chunk_size=50, overlap=10)
    assert len(chunks) >= 2
    for c, m in chunks:
        assert len(c) <= 55
        assert m["doc_id"] == "test"
        assert "chunk_index" in m


def test_overlap_chunk_preserves_metadata():
    text = "short"
    meta = {"doc_id": "x", "page_or_para": 1}
    chunks = overlap_chunk(text, meta, chunk_size=100, overlap=0)
    assert len(chunks) == 1
    assert chunks[0][1]["page_or_para"] == 1


def test_row_based_chunk():
    lines = ["line1", "line2", "line3", "line4", "line5"]
    text = "\n".join(lines)
    meta = {"doc_id": "t"}
    chunks = row_based_chunk(text, meta, max_chars_per_row_chunk=20)
    assert len(chunks) >= 1
    all_text = " ".join(c for c, _ in chunks)
    assert "line1" in all_text and "line5" in all_text


def test_chunk_content_overlap():
    blocks = [("hello world here is some content " * 20, {"doc_id": "d1"})]
    out = chunk_content(blocks, strategy="overlap", chunk_size=80, chunk_overlap=10)
    assert len(out) >= 2
    assert all(isinstance(o[0], str) and isinstance(o[1], dict) for o in out)


def test_chunk_content_row_table():
    blocks = [("row1\nrow2\nrow3\nrow4", {"doc_id": "t"})]
    out = chunk_content(blocks, strategy="row_table")
    assert len(out) >= 1
    assert "row1" in out[0][0] or "row2" in out[0][0]
