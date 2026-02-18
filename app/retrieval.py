"""
Two retrieval techniques: Similarity Top-k and MMR.
Post-filters: minimum content length (drop header/cover-only chunks), dedupe by (doc_id, span, chunk_index).
"""
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from app.config import settings


def _doc_span_chunk_key(d: Document) -> tuple[str, str, int]:
    """Key for dedupe: (doc_id, span, chunk_index)."""
    doc_id = (d.metadata.get("doc_id") or d.metadata.get("source") or "").strip()
    span = d.metadata.get("page_or_para") or d.metadata.get("row_range")
    chunk_idx = d.metadata.get("chunk_index", 0)
    if not isinstance(chunk_idx, int):
        chunk_idx = 0
    return (doc_id, str(span), chunk_idx)


def _dedupe_by_doc_span_chunk(docs: list[Document]) -> list[Document]:
    """Dedupe by (doc_id, page_or_para or row_range, chunk_index). Keeps multiple chunks per page."""
    seen: set[tuple[str, str, int]] = set()
    out: list[Document] = []
    for d in docs:
        key = _doc_span_chunk_key(d)
        if key in seen:
            continue
        seen.add(key)
        out.append(d)
    return out


def _filter_by_min_length(docs: list[Document], min_length: int) -> list[Document]:
    """Drop chunks shorter than min_length (avoids cover/header-only chunks ranking first)."""
    if min_length <= 0:
        return docs
    return [d for d in docs if len((d.page_content or "").strip()) >= min_length]


def _filter_by_min_words(docs: list[Document], min_words: int) -> list[Document]:
    """Drop chunks with fewer than min_words (filters cover/header-only chunks)."""
    if min_words <= 0:
        return docs
    out = []
    for d in docs:
        text = (d.page_content or "").strip()
        word_count = len(text.split()) if text else 0
        if word_count >= min_words:
            out.append(d)
    return out


def _chunk_passes_filters(doc: Document) -> bool:
    """True if chunk passes min length and min words (when set)."""
    text = (doc.page_content or "").strip()
    min_len = getattr(settings, "retrieval_min_chunk_length", 0) or 0
    min_words = getattr(settings, "retrieval_min_chunk_words", 0) or 0
    if min_len > 0 and len(text) < min_len:
        return False
    if min_words > 0 and len(text.split()) < min_words:
        return False
    return True


def _chunk_passes_filters_with_overrides(
    doc: Document,
    min_length_override: int | None = None,
    min_words_override: int | None = None,
) -> bool:
    """True if chunk passes filters; use overrides when provided (e.g. 0 for eval)."""
    text = (doc.page_content or "").strip()
    min_len = min_length_override if min_length_override is not None else (getattr(settings, "retrieval_min_chunk_length", 0) or 0)
    min_words = min_words_override if min_words_override is not None else (getattr(settings, "retrieval_min_chunk_words", 0) or 0)
    if min_len > 0 and len(text) < min_len:
        return False
    if min_words > 0 and len(text.split()) < min_words:
        return False
    return True


def _top_k_pairs_with_scores(
    vector_store: VectorStore,
    query: str,
    *,
    top_k_override: int | None = None,
    min_chunk_length_override: int | None = None,
    min_chunk_words_override: int | None = None,
) -> tuple[list[Document], list[float]]:
    """Internal: top-k (doc, score) pairs after optional min-length/min-words filter and dedupe. Single search for correct scores."""
    k = top_k_override if top_k_override is not None else settings.retrieval_top_k
    min_len = min_chunk_length_override if min_chunk_length_override is not None else (getattr(settings, "retrieval_min_chunk_length", 0) or 0)
    min_words = min_chunk_words_override if min_chunk_words_override is not None else (getattr(settings, "retrieval_min_chunk_words", 0) or 0)
    has_filter = min_len > 0 or min_words > 0
    fetch_k = max(k * 8, 50) if has_filter else k * 5
    raw = vector_store.similarity_search_with_score(query, k=fetch_k)
    pairs = [(doc, score) for doc, score in raw]
    pairs = [(d, s) for d, s in pairs if _chunk_passes_filters_with_overrides(d, min_length_override=min_chunk_length_override, min_words_override=min_chunk_words_override)]
    seen: set[tuple[str, str, int]] = set()
    deduped: list[tuple[Document, float]] = []
    for d, s in pairs:
        key = _doc_span_chunk_key(d)
        if key in seen:
            continue
        seen.add(key)
        deduped.append((d, s))
    deduped = deduped[:k]
    return [d for d, _ in deduped], [s for _, s in deduped]


def retrieval_similarity_top_k(
    vector_store: VectorStore,
    query: str,
) -> list[Document]:
    """Top-k by similarity. Drops very short chunks, dedupes by (doc_id, span, chunk_index), returns top k."""
    docs, _ = _top_k_pairs_with_scores(vector_store, query)
    return docs


def retrieval_mmr(
    vector_store: VectorStore,
    query: str,
) -> list[Document]:
    """MMR: fetch_k candidates, then max marginal relevance. Min-length/min-words filter + dedupe by (doc_id, span, chunk_index)."""
    fetch_k = settings.retrieval_mmr_fetch_k
    k = settings.retrieval_mmr_k
    lambda_mult = settings.retrieval_mmr_lambda
    raw = vector_store.max_marginal_relevance_search(
        query, k=min(k * 2, fetch_k), fetch_k=fetch_k, lambda_mult=lambda_mult, filter=None
    )
    raw = [d for d in raw if _chunk_passes_filters(d)]
    deduped = _dedupe_by_doc_span_chunk(raw)
    return deduped[:k]


def retrieval_with_scores(
    vector_store: VectorStore,
    query: str,
    technique: str = "top_k",
    *,
    eval_mode: bool = False,
) -> tuple[list[Document], list[float], bool]:
    """
    Run retrieval; return (documents, scores, below_threshold).
    below_threshold=True when no documents retrieved.
    eval_mode: if True, use unfiltered retrieval (no min length/words) and eval_retrieval_top_k for better RAGAS metrics.
    """
    if technique == "mmr" and not eval_mode:
        docs = retrieval_mmr(vector_store, query)
        scores = [1.0] * len(docs) if docs else []
    elif technique == "top_k" and eval_mode:
        k_override = getattr(settings, "eval_retrieval_top_k", 0) or settings.retrieval_top_k
        docs, scores = _top_k_pairs_with_scores(
            vector_store,
            query,
            top_k_override=k_override,
            min_chunk_length_override=0,
            min_chunk_words_override=0,
        )
    else:
        docs, scores = _top_k_pairs_with_scores(vector_store, query)
    below = not docs
    return docs, scores, below
