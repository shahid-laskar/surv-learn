"""
app/dependencies/auth.py
FastAPI dependency for extracting and validating the current user from the
Authorization header.

PHASE 0003 UPDATE:
  CurrentUser now carries the full JWT payload:
    user_id, username, user_type, org_id, customer_id,
    roles[], permissions[], session_id.

  require_permission(perm) — replaces the old require_admin() pattern.
  require_role(role)       — role-level guard.
  require_admin()          — backward-compat alias → require_role("SUPER_ADMIN").

Even though Kong validates the JWT signature/expiry before the request
reaches FastAPI, FastAPI re-validates here too — Kong should never be
the only line of defense, and this also lets local dev (hitting FastAPI
directly on :8000, bypassing Kong) still enforce auth.
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from app.services.auth_service import decode_access_token

log = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser:
    def __init__(
        self,
        user_id: int,
        username: str,
        user_type: str,
        org_id: Optional[int],
        customer_id: Optional[int],
        roles: list[str],
        permissions: list[str],
        session_id: str,
        # Legacy compat
        role: str = "operator",
    ):
        self.user_id     = user_id
        self.username    = username
        self.user_type   = user_type
        self.org_id      = org_id
        self.customer_id = customer_id
        self.roles       = roles
        self.permissions = permissions
        self.session_id  = session_id
        # Legacy flat role — maps to "admin" if SUPER_ADMIN in roles, else "operator"
        self.role = "admin" if "SUPER_ADMIN" in roles else role

    def has_permission(self, perm: str) -> bool:
        return perm in self.permissions

    def has_role(self, role_code: str) -> bool:
        return role_code in self.roles

    def is_super_admin(self) -> bool:
        return "SUPER_ADMIN" in self.roles


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

    user_id    = payload.get("sub")
    username   = payload.get("username") or payload.get("sub", "")
    user_type  = payload.get("user_type", "EMPLOYEE")
    org_id     = payload.get("org_id")
    customer_id = payload.get("customer_id")
    roles      = payload.get("roles", [])
    permissions = payload.get("permissions", [])
    session_id = payload.get("session_id", "")

    # Legacy tokens (Phase 7 era) carry sub=username and role=admin|operator
    # Support them transparently so existing sessions aren't broken immediately.
    if isinstance(user_id, str) and not user_id.isdigit():
        # Old token — synthesize minimal CurrentUser
        legacy_role = payload.get("role", "operator")
        roles = ["SUPER_ADMIN"] if legacy_role == "admin" else ["OPERATOR"]
        permissions = []   # old tokens have no permission list
        return CurrentUser(
            user_id=0,
            username=user_id,
            user_type="EMPLOYEE",
            org_id=None,
            customer_id=None,
            roles=roles,
            permissions=permissions,
            session_id=session_id,
            role=legacy_role,
        )

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return CurrentUser(
        user_id=int(user_id),
        username=str(username),
        user_type=user_type,
        org_id=int(org_id) if org_id else None,
        customer_id=int(customer_id) if customer_id else None,
        roles=roles,
        permissions=permissions,
        session_id=session_id,
    )


# ── Dependency factories ───────────────────────────────────────────────────────

def require_permission(perm: str):
    """
    Dependency factory: raises 403 if the current user lacks `perm`.

    Usage:
        @router.get("/cameras/", dependencies=[Depends(require_permission("camera.view"))])
        # or
        async def endpoint(user: CurrentUser = Depends(require_permission("camera.create"))):
    """
    async def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        # SUPER_ADMIN bypasses all permission checks
        if user.is_super_admin():
            return user
        if not user.has_permission(perm):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{perm}' required",
            )
        return user
    checker.__name__ = f"require_permission_{perm.replace('.', '_')}"
    return checker


def require_role(role_code: str):
    """
    Dependency factory: raises 403 if the current user does not have `role_code`.
    """
    async def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not user.has_role(role_code) and not user.is_super_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_code}' required",
            )
        return user
    checker.__name__ = f"require_role_{role_code}"
    return checker


async def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    Backward-compatible admin guard.
    Accepts legacy role='admin' tokens OR new SUPER_ADMIN role tokens.
    """
    if user.role != "admin" and not user.is_super_admin():
        raise HTTPException(status_code=403, detail="Admin role required")
    return user
