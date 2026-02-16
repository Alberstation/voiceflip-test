"""RAG query endpoint."""

import structlog
from fastapi import APIRouter, HTTPException

from app.api.schemas import QueryRequest, QueryResponse
from app.constants import RETRIEVAL_TECHNIQUES
from app.rag import query_rag

router = APIRouter()
logger = structlog.get_logger()


@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    """RAG query: retrieval + LLM answer with citations. technique: top_k | mmr."""
    if request.retrieval_technique not in RETRIEVAL_TECHNIQUES:
        raise HTTPException(
            400, f"retrieval_technique must be one of {RETRIEVAL_TECHNIQUES}"
        )
    try:
        out = query_rag(
            request.question, retrieval_technique=request.retrieval_technique
        )
        return QueryResponse(
            answer=out["answer"],
            citations=out["citations"],
            below_threshold=out["below_threshold"],
        )
    except Exception as e:
        logger.error("query_failed", error=str(e))
        raise HTTPException(500, str(e)) from e
