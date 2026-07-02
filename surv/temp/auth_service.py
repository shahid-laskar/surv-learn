"""
auth_service.py
Single source of truth for password hashing and JWT generation/validation.

PHASE 0003 UPDATE:
  - create_access_token() now embeds user_id, user_type, org_id, customer_id,
    roles[], permissions[], and session_id in the JWT (per company_hierarchy_arch.md).
  - create_session() persists a UserSession row and returns the session UUID
    that gets embedded in the JWT.
  - revoke_session() soft-deletes a session on logout.
  - Legacy signature kept via create_access_token_legacy() for any code that
    hasn't been migrated yet.

CRITICAL: The JWT issued here must validate against Kong's JWT plugin.
Kong's "iss" (issuer) claim must match the Kong consumer's `key` field,
and the signing secret here must match the consumer's `secret` field
exactly. See kong/setup-kong-jwt.sh for consumer provisioning.
"""

import uuid
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import bcrypt
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings

log = logging.getLogger(__name__)

# Must exactly match the Kong consumer's JWT credential `key` field.
KONG_JWT_ISSUER = settings.kong_jwt_issuer


# ── Passwords ──────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt()
    pwd_bytes = plain.encode("utf-8")
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        pwd_bytes = plain.encode("utf-8")
        hashed_bytes = hashed.encode("utf-8") if isinstance(hashed, str) else hashed
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except ValueError:
        return False


# ── Session management ─────────────────────────────────────────────────────────

async def create_session(
    db: AsyncSession,
    user_id: int,
    ip_address: Optional[str] = None,
    device_name: Optional[str] = None,
    device_type: Optional[str] = "web",
    expires_in_seconds: Optional[int] = None,
) -> str:
    """
    Persist a UserSession row and return the session UUID.
    The UUID is embedded in the JWT as the `session_id` claim.
    """
    from app.models.rbac import UserSession  # local import avoids circular

    session_id = str(uuid.uuid4())
    expires_at = None
    if expires_in_seconds:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)

    session = UserSession(
        id=session_id,
        user_id=user_id,
        ip_address=ip_address,
        device_name=device_name,
        device_type=device_type,
        expires_at=expires_at,
        is_active=True,
    )
    db.add(session)
    await db.flush()   # get the row into the DB within the caller's transaction
    return session_id


async def revoke_session(db: AsyncSession, session_id: str) -> None:
    """Soft-delete a session (logout). Raises nothing if not found."""
    from app.models.rbac import UserSession

    result = await db.execute(select(UserSession).where(UserSession.id == session_id))
    session = result.scalar_one_or_none()
    if session:
        session.is_active = False
        await db.flush()


# ── User session JWTs (for API access via Kong) ───────────────────────────────

def create_access_token(
    *,
    user_id: int,
    username: str,
    user_type: str,
    org_id: Optional[int],
    customer_id: Optional[int],
    roles: list[str],
    permissions: list[str],
    session_id: str,
    expires_in: Optional[int] = None,
) -> tuple[str, int]:
    """
    Returns (token, expires_in_seconds).
    JWT payload per company_hierarchy_arch.md:
      sub           → user_id (int)
      username      → username string (for logging/display)
      user_type     → EMPLOYEE | CUSTOMER | PARTNER | SYSTEM
      org_id        → organization.id or null
      customer_id   → customer.id or null
      roles         → list of role codes
      permissions   → list of permission codes
      session_id    → user_session.id UUID
      iss, iat, exp → standard claims
    Signed with the same secret as the Kong JWT consumer credential.
    """
    expires_in = expires_in or settings.access_token_expire_minutes * 60
    now = int(time.time())
    payload = {
        "iss":         KONG_JWT_ISSUER,
        "sub":         str(user_id),
        "username":    username,
        "user_type":   user_type,
        "org_id":      org_id,
        "customer_id": customer_id,
        "roles":       roles,
        "permissions": permissions,
        "session_id":  session_id,
        "iat":         now,
        "exp":         now + expires_in,
        "type":        "access",
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


# ── Stream tokens (for token-gated HLS playback) ──────────────────────────────

def create_stream_token(cam_id: str, username: str, expires_in: int = 3600) -> str:
    """
    Short-lived token scoped to a single camera path. Validated by
    MediaMTX's authMethod: http hook (see app/routers/stream_auth.py),
    NOT by Kong — this token never goes through Kong's JWT plugin since
    MediaMTX is queried directly by FastAPI's auth webhook.
    """
    now = int(time.time())
    payload = {
        "iss":  KONG_JWT_ISSUER,
        "sub":  username,
        "path": cam_id,
        "iat":  now,
        "exp":  now + expires_in,
        "type": "stream",
    }
    return jwt.encode(payload, settings.kong_jwt_secret, algorithm="HS256")


def decode_stream_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.kong_jwt_secret,
        algorithms=["HS256"],
        options={"verify_iss": False},
    )


# ── Helper: load all roles + permissions for a user ───────────────────────────

async def load_user_roles_permissions(db: AsyncSession, user_id: int) -> tuple[list[str], list[str]]:
    """
    Returns (role_codes, permission_codes) for the given user.
    Eagerly joins user_role → role → role_permission → permission.
    """
    from app.models.rbac import UserRole, Role, RolePermission, Permission

    # Roles
    result = await db.execute(
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
    )
    roles = [r for (r,) in result.all()]

    # Permissions (deduplicated)
    result = await db.execute(
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role,           Role.id           == RolePermission.role_id)
        .join(UserRole,       UserRole.role_id  == Role.id)
        .where(UserRole.user_id == user_id)
        .distinct()
    )
    permissions = [p for (p,) in result.all()]

    return roles, permissions
