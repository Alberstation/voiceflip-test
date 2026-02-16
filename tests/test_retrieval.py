"""
Unit tests for retrieval (dedupe, score threshold).
Run inside container: docker compose run --rm app pytest tests/test_retrieval.py -v
"""
import pytest
from langchain_core.documents import Document

from app.retrieval import _dedupe_by_doc_and_span


def test_dedupe_by_doc_and_span():
    d1 = Document(page_content="a", metadata={"doc_id": "x", "page_or_para": 1})
    d2 = Document(page_content="b", metadata={"doc_id": "x", "page_or_para": 1})
    d3 = Document(page_content="c", metadata={"doc_id": "x", "page_or_para": 2})
    out = _dedupe_by_doc_and_span([d1, d2, d3])
    assert len(out) == 2  # same (x,1) once; (x,2) once
    contents = [d.page_content for d in out]
    assert "a" in contents or "b" in contents
    assert "c" in contents


def test_dedupe_uses_source_if_no_doc_id():
    d1 = Document(page_content="a", metadata={"source": "/path/to/doc", "page_or_para": 1})
    d2 = Document(page_content="b", metadata={"source": "/path/to/doc", "page_or_para": 1})
    out = _dedupe_by_doc_and_span([d1, d2])
    assert len(out) == 1
