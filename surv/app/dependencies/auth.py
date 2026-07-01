"""
app/dependencies/auth.py
FastAPI dependency for extracting and validating the current user from the
Authorization header. Even though Kong validates the JWT signature/expiry
before the request reaches FastAPI, FastAPI re-validates here too — Kong
should never be the only line of defense, and this also lets local dev
(hitting FastAPI directly on :8000, bypassing Kong on :8000 external)
still enforce auth.
"""

import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from app.services.auth_service import decode_access_token

log = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser:
    def __init__(self, username: str, role: str):
        self.username = username
        self.role = role


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError as e:
        log.warning(f"Token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    role     = payload.get("role", "operator")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return CurrentUser(username=username, role=role)


async def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return user
