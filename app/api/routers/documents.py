"""Document upload endpoint."""

import structlog
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services import ingest_documents_from_files

router = APIRouter()
logger = structlog.get_logger()


@router.post("/documents")
def add_documents(files: list[UploadFile] = File(...)):
    """Add new DOCX/HTML documents to the RAG. Accepts multipart/form-data with file(s)."""
    if not files:
        raise HTTPException(400, "No files provided")
    file_data = []
    for f in files:
        content = f.file.read()
        if not f.filename:
            raise HTTPException(400, "Filename required")
        file_data.append((f.filename, content))
    try:
        return ingest_documents_from_files(file_data)
    except Exception as e:
        logger.error("documents_failed", error=str(e))
        raise HTTPException(500, str(e)) from e
