"""
FastAPI app: health check and RAG query endpoint.
Run inside Docker; no local installs.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.constants import RETRIEVAL_TECHNIQUES
from app.rag import query_rag

app = FastAPI(
    title="RAG AI Engineer",
    description="VoiceFlip Technical Test — RAG pipeline and agent",
    version="0.1.0",
)


class QueryRequest(BaseModel):
    question: str
    retrieval_technique: str = "top_k"


class QueryResponse(BaseModel):
    answer: str
    citations: list[dict]
    below_threshold: bool


@app.get("/health", tags=["health"])
def health():
    """Health check for Docker and load balancers."""
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse, tags=["rag"])
def query(request: QueryRequest):
    """RAG query: retrieval + LLM answer with citations. technique: top_k | mmr."""
    if request.retrieval_technique not in RETRIEVAL_TECHNIQUES:
        raise HTTPException(400, f"retrieval_technique must be one of {RETRIEVAL_TECHNIQUES}")
    try:
        out = query_rag(request.question, retrieval_technique=request.retrieval_technique)
        return QueryResponse(
            answer=out["answer"],
            citations=out["citations"],
            below_threshold=out["below_threshold"],
        )
    except Exception as e:
        raise HTTPException(500, str(e))
