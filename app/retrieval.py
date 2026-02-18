"""
Two retrieval techniques: Similarity Top-k and MMR.
All parameters from config (.env). Post-filter: dedupe by (doc_id, page/para range).
"""
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from app.config import settings


def _dedupe_by_doc_and_span(docs: list[Document]) -> list[Document]:
    """Post-filter: dedupe by (doc_id, page_or_para / row_range)."""
    seen: set[tuple[str, str]] = set()
    out: list[Document] = []
    for d in docs:
        doc_id = (d.metadata.get("doc_id") or d.metadata.get("source") or "").strip()
        span = d.metadata.get("page_or_para") or d.metadata.get("row_range")
        key = (doc_id, str(span))
        if key in seen:
            continue
        seen.add(key)
        out.append(d)
    return out


def retrieval_similarity_top_k(
    vector_store: VectorStore,
    query: str,
) -> list[Document]:
    """Public API: Top-k with config params and dedupe. Returns top-k by similarity (no score filter)."""
    k = settings.retrieval_top_k
    raw = vector_store.similarity_search_with_score(query, k=k * 5)
    # Raw results are already ordered by relevance; dedupe and take top k
    docs = [doc for doc, _ in raw]
    deduped = _dedupe_by_doc_and_span(docs)
    return deduped[:k]


def retrieval_mmr(
    vector_store: VectorStore,
    query: str,
) -> list[Document]:
    """
    MMR: fetch_k candidates, then max marginal relevance. Dedupe by (doc_id, page/para).
    """
    fetch_k = settings.retrieval_mmr_fetch_k
    k = settings.retrieval_mmr_k
    lambda_mult = settings.retrieval_mmr_lambda
    raw = vector_store.max_marginal_relevance_search(
        query, k=k, fetch_k=fetch_k, lambda_mult=lambda_mult, filter=None
    )
    deduped = _dedupe_by_doc_and_span(raw)
    return deduped[:k]


def retrieval_with_scores(
    vector_store: VectorStore,
    query: str,
    technique: str = "top_k",
) -> tuple[list[Document], list[float], bool]:
    """
    Run retrieval; return (documents, scores, below_threshold).
    below_threshold=True when no documents retrieved.
    """
    if technique == "mmr":
        docs = retrieval_mmr(vector_store, query)
        scores = [1.0] * len(docs) if docs else []
    else:
        docs = retrieval_similarity_top_k(vector_store, query)
        raw = vector_store.similarity_search_with_score(query, k=settings.retrieval_top_k * 3)
        score_map = {id(d): s for d, s in raw}
        scores = [score_map.get(id(d), 0.0) for d in docs]
    below = not docs
    return docs, scores, below
