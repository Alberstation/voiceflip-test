"""
Minimal FastAPI app for Phase 1.
Exposes health endpoint for Docker health checks.
"""
from fastapi import FastAPI

app = FastAPI(
    title="RAG AI Engineer",
    description="VoiceFlip Technical Test — RAG pipeline and agent",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
def health():
    """Health check for Docker and load balancers."""
    return {"status": "ok"}
