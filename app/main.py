"""
FastAPI application: CORS, router mounting.
Run inside Docker; no local installs.
"""
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import settings
from app.logging_config import configure_logging

configure_logging(settings.log_level)
logger = structlog.get_logger()

app = FastAPI(
    title="RAG AI Engineer",
    description="VoiceFlip Technical Test — RAG pipeline, LangGraph agent, chatbot",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
def startup():
    logger.info("app_started", version="0.2.0")
