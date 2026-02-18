"""
Document metadata parsing. Reads chunking strategy per file from Excel.
"""
from pathlib import Path
from typing import Literal

from app.constants import CHUNKING_OVERLAP, CHUNKING_ROW_TABLE

ChunkingStrategy = Literal["overlap", "row_table"]


def get_doc_chunking_from_xlsx(xlsx_path: Path) -> dict[str, ChunkingStrategy]:
    """
    Parse Excel metadata and return mapping filename -> chunking strategy.
    Expected columns: filename/document, chunking_type with values overlap | row_table.
    """
    try:
        import openpyxl
    except ImportError:
        return {}
    if not xlsx_path.exists():
        return {}
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.active
    if not ws:
        wb.close()
        return {}
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        return {}
    header = [str(c).lower().strip() if c else "" for c in rows[0]]
    filename_col = _find_column_index(header, ("file", "document", "name"), default=0)
    chunk_col = _find_column_index(header, ("chunk", "strategy", "type"), default=1 if len(header) > 1 else 0)
    result: dict[str, ChunkingStrategy] = {}
    for row in rows[1:]:
        if not row:
            continue
        name = row[filename_col] if filename_col < len(row) else None
        val = row[chunk_col] if chunk_col < len(row) else None
        if not name:
            continue
        fname = _normalize_filename(str(name).strip())
        if not fname:
            continue
        strategy = _parse_strategy(str(val).strip().lower() if val else CHUNKING_OVERLAP)
        result[fname] = strategy
    return result


def _find_column_index(header: list[str], keywords: tuple[str, ...], default: int = 0) -> int:
    """Find first column index whose header contains any of the keywords."""
    for i, h in enumerate(header):
        if any(kw in h for kw in keywords):
            return i
    return default


def _normalize_filename(fname: str) -> str:
    """Ensure filename has a supported extension."""
    if not fname:
        return ""
    if not fname.lower().endswith((".docx", ".html", ".htm", ".pdf")):
        return fname + ".docx"
    return fname


def _parse_strategy(val: str) -> ChunkingStrategy:
    """Parse chunking strategy from cell value."""
    return CHUNKING_ROW_TABLE if "row" in val or "table" in val else CHUNKING_OVERLAP
