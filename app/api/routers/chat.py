"""Chat (LangGraph agent) endpoint."""

import uuid

import structlog
from fastapi import APIRouter, HTTPException

from app.api.schemas import ChatRequest, ChatResponse
from app.services import invoke_agent

router = APIRouter()
logger = structlog.get_logger()


def _is_payment_required(exc: Exception) -> bool:
    """True if the exception is Hugging Face 402 Payment Required."""
    msg = str(exc).lower()
    return "402" in msg or "payment required" in msg


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Chat with the LangGraph agent. Uses conversational memory per session_id."""
    session_id = request.session_id or str(uuid.uuid4())
    try:
        result = invoke_agent(request.message, session_id)
        return ChatResponse(answer=result["answer"], session_id=session_id)
    except Exception as e:
        logger.error("chat_failed", error=str(e), session_id=session_id)
        if _is_payment_required(e):
            raise HTTPException(
                402,
                "Hugging Face returned Payment Required (402). The free tier limit may be reached or this model requires billing. Set HUGGINGFACEHUB_API_TOKEN and check https://huggingface.co/settings/billing, or try a different model via LLM_MODEL.",
            ) from e
        raise HTTPException(500, str(e)) from e
