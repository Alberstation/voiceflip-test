"""
Chunking strategies: overlap (default) and row-based (for tables).
Strategy per document is read from the metadata Excel file.
"""
from typing import Any, Literal

from app.config import settings
from app.metadata import ChunkingStrategy, get_doc_chunking_from_xlsx


def overlap_chunk(
    text: str,
    meta: dict[str, Any],
    chunk_size: int,
    overlap: int,
) -> list[tuple[str, dict[str, Any]]]:
    """Split text into chunks with overlap. Preserves metadata plus chunk index and span."""
    if not text.strip():
        return []
    overlap_len = min(overlap or settings.chunk_overlap, chunk_size - 1)
    chunks: list[tuple[str, dict[str, Any]]] = []
    start = 0
    idx = 0
    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]
        if not chunk_text.strip():
            start = end - overlap_len
            continue
        chunk_meta = meta | {"chunk_index": idx, "chunk_start": start, "chunk_end": end}
        chunks.append((chunk_text.strip(), chunk_meta))
        idx += 1
        start = end - overlap_len
    return chunks


def row_based_chunk(
    text: str,
    meta: dict[str, Any],
    max_chars_per_row_chunk: int = 1024,
) -> list[tuple[str, dict[str, Any]]]:
    """Split by lines (table-friendly). Groups lines until max_chars_per_row_chunk is reached."""
    if not text.strip():
        return []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return [(text.strip(), meta | {"chunk_index": 0})]
    chunks: list[tuple[str, dict[str, Any]]] = []
    buf: list[str] = []
    row_start = 0
    for i, line in enumerate(lines):
        buf.append(line)
        buf_size = sum(len(l) + 1 for l in buf)
        if buf_size >= max_chars_per_row_chunk or i == len(lines) - 1:
            block = "\n".join(buf)
            if block.strip():
                chunks.append((block.strip(), meta | {"chunk_index": len(chunks), "row_range": (row_start, row_start + len(buf))}))
            row_start += len(buf)
            buf = []
    if buf:
        block = "\n".join(buf)
        if block.strip():
            chunks.append((block.strip(), meta | {"chunk_index": len(chunks), "row_range": (row_start, row_start + len(buf))}))
    return chunks


def chunk_content(
    content_blocks: list[tuple[str, dict[str, Any]]],
    strategy: ChunkingStrategy = "overlap",
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    """Apply one chunking strategy to a list of (text, metadata) blocks."""
    size = chunk_size or settings.chunk_size
    overlap = chunk_overlap or settings.chunk_overlap
    out: list[tuple[str, dict[str, Any]]] = []
    for text, meta in content_blocks:
        if strategy == "overlap":
            out.extend(overlap_chunk(text, meta, size, overlap))
        else:
            out.extend(row_based_chunk(text, meta))
    return out


