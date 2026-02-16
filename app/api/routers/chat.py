"""Chat (LangGraph agent) endpoint."""

import uuid

import structlog
from fastapi import APIRouter, HTTPException

from app.api.schemas import ChatRequest, ChatResponse
from app.services import invoke_agent

router = APIRouter()
logger = structlog.get_logger()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Chat with the LangGraph agent. Uses conversational memory per session_id."""
    session_id = request.session_id or str(uuid.uuid4())
    try:
        result = invoke_agent(request.message, session_id)
        return ChatResponse(answer=result["answer"], session_id=session_id)
    except Exception as e:
        logger.error("chat_failed", error=str(e), session_id=session_id)
        raise HTTPException(500, str(e)) from e
