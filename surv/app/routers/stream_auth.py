"""
app/routers/stream_auth.py
Called by MediaMTX (authMethod: http, authHTTPAddress) to validate stream
access tokens. MediaMTX POSTs the connection details here on every publish/
read/playback attempt; we return 200 to allow, any other status to deny.

This endpoint is NOT behind Kong's JWT plugin (Kong would reject MediaMTX's
internal request since it has no Authorization header) — it's reached
directly, container-to-container, on FastAPI's internal port.
"""

import logging
import time
from fastapi import APIRouter, Request, Response
from jose import JWTError
from app.services.auth_service import decode_stream_token

log = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["stream-auth"])

# HLS clients often send the JWT only on the initial playlist request.
# Segment/part requests can arrive without the token query; allow those
# requests when they come from the same MediaMTX client IP + path and the
# original token has not expired yet.
_stream_session_expiry: dict[tuple[str, str], int] = {}


@router.post("/stream", status_code=200)
async def validate_stream_access(request: Request, response: Response):
    """
    MediaMTX sends a JSON body like:
      {"ip": "...", "user": "...", "password": "...", "path": "CAMKRTVM00001",
       "protocol": "hls", "action": "read", "query": "token=<jwt>"}

    We extract the token from the query string and validate it grants
    access to the requested path.
    """
    body = await request.json()
    client_ip = body.get("ip", "")
    path  = body.get("path", "")
    query = body.get("query", "")
    action = body.get("action", "")

    # Only gate read/playback actions — publish is handled separately
    # (cameras publish via RTSP with no token, internal network only)
    if action not in ("read", "playback"):
        return {"status": "ok"}

    token = None
    for part in query.split("&"):
        if part.startswith("token="):
            token = part[len("token="):]
            break

    now = int(time.time())
    key = (client_ip, path)

    if not token:
        # Opportunistically clear stale session entries.
        expired = [k for k, exp in _stream_session_expiry.items() if exp <= now]
        for stale_key in expired:
            _stream_session_expiry.pop(stale_key, None)

        session_exp = _stream_session_expiry.get(key)
        if session_exp and session_exp > now:
            return {"status": "ok"}

        log.warning(f"Stream access denied — no token for path '{path}'")
        response.status_code = 401
        return {"status": "denied", "reason": "missing token"}

    try:
        payload = decode_stream_token(token)
    except JWTError as e:
        log.warning(f"Stream access denied — invalid token for path '{path}': {e}")
        response.status_code = 401
        return {"status": "denied", "reason": "invalid or expired token"}

    token_path = payload.get("path")
    if token_path != path:
        log.warning(f"Stream access denied — token scoped to '{token_path}', requested '{path}'")
        response.status_code = 403
        return {"status": "denied", "reason": "token not valid for this camera"}

    token_exp = payload.get("exp")
    if isinstance(token_exp, int):
        _stream_session_expiry[key] = token_exp

    return {"status": "ok"}
