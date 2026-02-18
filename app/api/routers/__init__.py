"""API route modules."""

from fastapi import APIRouter

from app.api.routers import chat, documents, eval as eval_router, health, openclaw, rag, retrieval

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(rag.router, prefix="", tags=["rag"])
api_router.include_router(chat.router, prefix="", tags=["chat"])
api_router.include_router(documents.router, prefix="", tags=["documents"])
api_router.include_router(retrieval.router, prefix="", tags=["retrieval"])
api_router.include_router(openclaw.router, prefix="", tags=["openclaw"])
api_router.include_router(eval_router.router, prefix="", tags=["eval"])
