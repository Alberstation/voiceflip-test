"""OpenClaw proxy endpoint (forward message to OpenClaw main session)."""

import json
import urllib.error

import structlog
from fastapi import APIRouter, HTTPException

from app.api.schemas import OpenClawSendRequest, OpenClawSendResponse
from app.config import settings
from app.openclaw_client import send_message

router = APIRouter()
logger = structlog.get_logger()


@router.post("/openclaw/send", response_model=OpenClawSendResponse)
def openclaw_send(request: OpenClawSendRequest):
    """Forward a message to OpenClaw's main session (Tools Invoke API). Requires OPENCLAW_GATEWAY_URL and OPENCLAW_GATEWAY_TOKEN."""
    url = settings.openclaw_gateway_url
    token = settings.openclaw_gateway_token
    if not url or not token:
        raise HTTPException(
            503,
            "OpenClaw integration not configured: set OPENCLAW_GATEWAY_URL and OPENCLAW_GATEWAY_TOKEN",
        )
    try:
        data = send_message(url, token, request.message)
        return OpenClawSendResponse(
            ok=data.get("ok", True), result=data.get("result")
        )
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        logger.error("openclaw_send_http_error", status=e.code, body=body[:500])
        try:
            err = json.loads(body)
            msg = (
                err.get("error", {}).get("message", body)
                if isinstance(err.get("error"), dict)
                else body
            )
        except Exception:
            msg = body or str(e)
        raise HTTPException(e.code, msg) from e
    except Exception as e:
        logger.error("openclaw_send_failed", error=str(e))
        raise HTTPException(502, str(e)) from e
