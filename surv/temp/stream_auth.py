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
from fastapi import APIRouter, Request, Response
from jose import JWTError
from app.services.auth_service import decode_stream_token

log = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["stream-auth"])


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

    if not token:
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

    return {"status": "ok"}
