"""
auth_service.py
Single source of truth for password hashing and JWT generation/validation.

Per Known Risk #5 in the build plan ("JWT Duplication — auth logic scattered
across views and utils"), all auth logic lives here and nowhere else.

CRITICAL: The JWT issued here must validate against Kong's JWT plugin.
Kong's "iss" (issuer) claim must match the Kong consumer's `key` field,
and the signing secret here must match the consumer's `secret` field
exactly. See kong/setup-kong-jwt.sh for consumer provisioning.
"""

import time
import logging
from datetime import datetime, timezone
import bcrypt
from jose import jwt, JWTError
from app.config import settings

log = logging.getLogger(__name__)

# Must exactly match the Kong consumer's JWT credential `key` field.
# Kong's JWT plugin looks up the consumer/secret using this "iss" claim.
KONG_JWT_ISSUER = settings.kong_jwt_issuer


# ── Passwords ──────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt()
    pwd_bytes = plain.encode('utf-8')
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    try:
        pwd_bytes = plain.encode('utf-8')
        hashed_bytes = hashed.encode('utf-8') if isinstance(hashed, str) else hashed
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except ValueError:
        return False


# ── User session JWTs (for API access via Kong) ─────────────────────────────

def create_access_token(username: str, role: str, expires_in: int | None = None) -> tuple[str, int]:
    """
    Returns (token, expires_in_seconds).
    Signed with the same secret as the Kong JWT consumer credential.
    """
    expires_in = expires_in or settings.access_token_expire_minutes * 60
    now = int(time.time())
    payload = {
        "iss":      KONG_JWT_ISSUER,
        "sub":      username,
        "role":     role,
        "iat":      now,
        "exp":      now + expires_in,
        "type":     "access",
    }
    token = jwt.encode(payload, settings.kong_jwt_secret, algorithm="HS256")
    return token, expires_in


def decode_access_token(token: str) -> dict:
    """Raises JWTError on invalid/expired token."""
    return jwt.decode(
        token,
        settings.kong_jwt_secret,
        algorithms=["HS256"],
        options={"verify_iss": False},  # Kong already verified iss upstream
    )


# ── Stream tokens (for token-gated HLS playback) ───────────────────────────

def create_stream_token(cam_id: str, username: str, expires_in: int = 3600) -> str:
    """
    Short-lived token scoped to a single camera path. Validated by
    MediaMTX's authMethod: http hook (see app/routers/stream_auth.py),
    NOT by Kong — this token never goes through Kong's JWT plugin since
    MediaMTX is queried directly by FastAPI's auth webhook.
    """
    now = int(time.time())
    payload = {
        "iss":   KONG_JWT_ISSUER,
        "sub":   username,
        "path":  cam_id,
        "iat":   now,
        "exp":   now + expires_in,
        "type":  "stream",
    }
    return jwt.encode(payload, settings.kong_jwt_secret, algorithm="HS256")


def decode_stream_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.kong_jwt_secret,
        algorithms=["HS256"],
        options={"verify_iss": False},
    )
