"""OpenClaw Tools Invoke API client (forward message to main session)."""

import json
import urllib.error
import urllib.request
from typing import Any


def send_message(gateway_url: str, token: str, message: str) -> dict[str, Any]:
    """
    Send a message to OpenClaw's main session via POST /tools/invoke (sessions_send).
    Raises urllib.error.HTTPError on HTTP errors, other exceptions on failure.
    """
    invoke_url = gateway_url.rstrip("/") + "/tools/invoke"
    payload = {
        "tool": "sessions_send",
        "sessionKey": "main",
        "args": {"message": message},
    }
    req = urllib.request.Request(
        invoke_url,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)
