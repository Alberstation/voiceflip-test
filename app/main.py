"""
FastAPI app: health, RAG query, chat agent, documents, retrieval.
Run inside Docker; no local installs.
"""
import uuid

import structlog
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings
from app.constants import RETRIEVAL_MMR, RETRIEVAL_TECHNIQUES, RETRIEVAL_TOP_K
from app.logging_config import configure_logging
from app.rag import query_rag
from app.services import ingest_documents_from_files, invoke_agent, retrieve

configure_logging(settings.log_level)
logger = structlog.get_logger()

app = FastAPI(
    title="RAG AI Engineer",
    description="VoiceFlip Technical Test — RAG pipeline, LangGraph agent, chatbot",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str
    retrieval_technique: str = RETRIEVAL_TOP_K


class QueryResponse(BaseModel):
    answer: str
    citations: list[dict]
    below_threshold: bool


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str


class RetrieveRequest(BaseModel):
    query: str
    technique: str = RETRIEVAL_TOP_K


@app.on_event("startup")
def startup():
    logger.info("app_started", version="0.2.0")


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
        logger.error("query_failed", error=str(e))
        raise HTTPException(500, str(e))


@app.post("/chat", response_model=ChatResponse, tags=["chat"])
def chat(request: ChatRequest):
    """Chat with the LangGraph agent. Uses conversational memory per session_id."""
    session_id = request.session_id or str(uuid.uuid4())
    try:
        result = invoke_agent(request.message, session_id)
        return ChatResponse(answer=result["answer"], session_id=session_id)
    except Exception as e:
        logger.error("chat_failed", error=str(e), session_id=session_id)
        raise HTTPException(500, str(e))


@app.post("/documents", tags=["documents"])
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
        result = ingest_documents_from_files(file_data)
        return result
    except Exception as e:
        logger.error("documents_failed", error=str(e))
        raise HTTPException(500, str(e))


@app.post("/retrieve", tags=["retrieval"])
def retrieve_endpoint(request: RetrieveRequest):
    """Retrieve documents using top_k or MMR. For frontend retrieval selection."""
    if request.technique not in RETRIEVAL_TECHNIQUES:
        raise HTTPException(400, f"technique must be one of {RETRIEVAL_TECHNIQUES}")
    try:
        return retrieve(request.query, request.technique)
    except Exception as e:
        logger.error("retrieve_failed", error=str(e))
        raise HTTPException(500, str(e))


# --- OpenClaw (Phase 6) ---

class OpenClawSendRequest(BaseModel):
    message: str


class OpenClawSendResponse(BaseModel):
    ok: bool
    result: dict | None = None
    error: str | None = None


@app.post("/openclaw/send", response_model=OpenClawSendResponse, tags=["openclaw"])
def openclaw_send(request: OpenClawSendRequest):
    """Forward a message to OpenClaw's main session (Tools Invoke API). Requires OPENCLAW_GATEWAY_URL and OPENCLAW_GATEWAY_TOKEN."""
    import urllib.request
    import json as _json

    url = settings.openclaw_gateway_url
    token = settings.openclaw_gateway_token
    if not url or not token:
        raise HTTPException(
            503,
            "OpenClaw integration not configured: set OPENCLAW_GATEWAY_URL and OPENCLAW_GATEWAY_TOKEN",
        )
    invoke_url = url.rstrip("/") + "/tools/invoke"
    payload = {
        "tool": "sessions_send",
        "sessionKey": "main",
        "args": {"message": request.message},
    }
    try:
        req = urllib.request.Request(
            invoke_url,
            data=_json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = _json.load(resp)
            return OpenClawSendResponse(ok=data.get("ok", True), result=data.get("result"))
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        logger.error("openclaw_send_http_error", status=e.code, body=body[:500])
        try:
            err = _json.loads(body)
            msg = err.get("error", {}).get("message", body) if isinstance(err.get("error"), dict) else body
        except Exception:
            msg = body or str(e)
        raise HTTPException(e.code, msg)
    except Exception as e:
        logger.error("openclaw_send_failed", error=str(e))
        raise HTTPException(502, str(e))
