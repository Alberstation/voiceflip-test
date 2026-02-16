"""
Load evaluation dataset from question_list.docx.
Format: one question per paragraph. Optional ground truth if "Q:" / "A:" pattern.
"""
import re
from pathlib import Path
from typing import Any

from docx import Document as DocxDocument


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
    items: list[dict[str, str]] = []
    buf_q = ""
    buf_a = ""
    for para in doc.paragraphs:
        text = para.text.strip()
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
