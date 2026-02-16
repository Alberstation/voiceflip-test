"""Retrieval endpoint (vector store search for frontend)."""

import structlog
from fastapi import APIRouter, HTTPException

from app.api.schemas import RetrieveRequest
from app.constants import RETRIEVAL_TECHNIQUES
from app.services import retrieve

router = APIRouter()
logger = structlog.get_logger()


@router.post("/retrieve")
def retrieve_endpoint(request: RetrieveRequest):
    """Retrieve documents using top_k or MMR. For frontend retrieval selection."""
    if request.technique not in RETRIEVAL_TECHNIQUES:
        raise HTTPException(
            400, f"technique must be one of {RETRIEVAL_TECHNIQUES}"
        )
    try:
        return retrieve(request.query, request.technique)
    except Exception as e:
        logger.error("retrieve_failed", error=str(e))
        raise HTTPException(500, str(e)) from e
