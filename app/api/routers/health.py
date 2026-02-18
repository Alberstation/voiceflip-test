"""Health check endpoint and aggregated service health for System Metrics Dashboard."""

import urllib.error
import urllib.request

from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/health")
def health():
    """Health check for Docker and load balancers."""
    return {"status": "ok"}


def _check_qdrant() -> dict:
    """Check Qdrant vector DB readiness. Returns {status, message?}."""
    url = f"http://{settings.qdrant_host}:{settings.qdrant_port}/readyz"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status in (200, 204):
                return {"status": "ok"}
            return {"status": "error", "message": f"HTTP {resp.status}"}
    except urllib.error.HTTPError as e:
        return {"status": "error", "message": f"HTTP {e.code}"}
    except OSError as e:
        return {"status": "error", "message": str(e) or "Connection failed"}


def _check_openclaw_gateway() -> dict:
    """Check OpenClaw gateway reachability. Returns {status, message?}."""
    url = settings.openclaw_gateway_url.strip().rstrip("/")
    if not url:
        return {"status": "unconfigured"}
    if not url.startswith("http"):
        url = f"http://{url}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            # 2xx or 401 (auth required) means service is up
            if resp.status in (200, 204, 401):
                return {"status": "ok"}
            return {"status": "error", "message": f"HTTP {resp.status}"}
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return {"status": "ok"}
        return {"status": "error", "message": f"HTTP {e.code}"}
    except OSError as e:
        return {"status": "error", "message": str(e) or "Connection failed"}


@router.get("/health/services")
def health_services():
    """Aggregated health of all services for the System Metrics Dashboard."""
    return {
        "services": {
            "api": {"status": "ok"},
            "vectordb": _check_qdrant(),
            "openclaw_gateway": _check_openclaw_gateway(),
        }
    }
