"""Pydantic request/response models for all API endpoints."""

from pydantic import BaseModel

from app.constants import RETRIEVAL_TOP_K


# ----- RAG -----
class QueryRequest(BaseModel):
    question: str
    retrieval_technique: str = RETRIEVAL_TOP_K


class QueryResponse(BaseModel):
    answer: str
    citations: list[dict]
    below_threshold: bool


# ----- Chat -----
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str


# ----- Retrieval -----
class RetrieveRequest(BaseModel):
    query: str
    technique: str = RETRIEVAL_TOP_K


# ----- OpenClaw -----
class OpenClawSendRequest(BaseModel):
    message: str


class OpenClawSendResponse(BaseModel):
    ok: bool
    result: dict | None = None
    error: str | None = None


# ----- Generate document (from OpenClaw research text) -----
class GenerateDocumentRequest(BaseModel):
    title: str
    content: str
    format: str = "docx"  # "docx" | "pdf"
