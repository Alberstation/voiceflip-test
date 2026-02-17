"""
Load evaluation dataset from question_list.docx or question_list.pdf.
Format: one question per paragraph. Optional ground truth if "Q:" / "A:" pattern.
"""
import re
from pathlib import Path
from typing import Any

from docx import Document as DocxDocument


def _parse_qa_items(lines: list[str]) -> list[dict[str, str]]:
    """Parse Q/A items from a list of non-empty lines (shared by docx and PDF)."""
    items: list[dict[str, str]] = []
    buf_q = ""
    buf_a = ""
    for text in lines:
        text = text.strip()
        if not text:
            continue
        lower = text.lower()
        if lower.startswith(("q:", "question:")):
            if buf_q:
                items.append({"question": buf_q, "ground_truth": buf_a})
            buf_q = re.sub(r"^(Q|Question):\s*", "", text, flags=re.I).strip()
            buf_a = ""
        elif lower.startswith(("a:", "answer:")):
            buf_a = re.sub(r"^(A|Answer):\s*", "", text, flags=re.I).strip()
            if buf_q:
                items.append({"question": buf_q, "ground_truth": buf_a})
            buf_q = ""
            buf_a = ""
        elif buf_q and not buf_a:
            buf_a = text
            items.append({"question": buf_q, "ground_truth": buf_a})
            buf_q = ""
            buf_a = ""
        else:
            items.append({"question": text, "ground_truth": ""})
    if buf_q:
        items.append({"question": buf_q, "ground_truth": buf_a})
    return items


def load_questions_from_docx(path: Path) -> list[dict[str, str]]:
    """
    Load questions from question_list.docx.
    Returns list of {"question": str, "ground_truth": str}.
    - One question per non-empty paragraph (default).
    - If "Q:" or "Question:" followed by "A:" or "Answer:", extracts both.
    """
    if not path.exists():
        return []
    doc = DocxDocument(path)
    lines = [para.text for para in doc.paragraphs]
    return _parse_qa_items(lines)


def load_questions_from_pdf(path: Path) -> list[dict[str, str]]:
    """
    Load questions from question_list.pdf.
    Extracts text from all pages and parses Q/A like load_questions_from_docx.
    """
    if not path.exists():
        return []
    from pypdf import PdfReader

    reader = PdfReader(path)
    lines: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            lines.extend(text.splitlines())
    return _parse_qa_items(lines)


def load_questions(path: Path) -> list[dict[str, str]]:
    """Load questions from DOCX or PDF by file extension."""
    suf = path.suffix.lower()
    if suf == ".pdf":
        return load_questions_from_pdf(path)
    if suf in (".docx", ".doc"):
        return load_questions_from_docx(path)
    return []
