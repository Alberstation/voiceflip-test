"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    """Health check for Docker and load balancers."""
    return {"status": "ok"}
