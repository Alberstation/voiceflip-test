"""Document upload and generate-from-text endpoints."""

import structlog
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.api.schemas import GenerateDocumentRequest
from app.document_generator import generate_document
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


@router.post("/documents/generate")
def generate_document_file(request: GenerateDocumentRequest):
    """
    Generate a DOCX or PDF from title + content (e.g. text from OpenClaw research).
    Returns the file for download. Use the Upload tab to add it to the RAG context.
    """
    fmt = request.format.lower()
    if fmt not in ("docx", "pdf"):
        raise HTTPException(400, "format must be 'docx' or 'pdf'")
    try:
        data, filename, media_type = generate_document(
            request.title, request.content, fmt
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return Response(
        content=data,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
