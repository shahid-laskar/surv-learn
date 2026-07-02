"""
app/routers/auth.py
Authentication endpoints — login, logout, me, user CRUD.

PHASE 0003: login now queries user roles + permissions from DB,
creates a UserSession row, and embeds the full hierarchy payload in the JWT.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.database import get_db
from app.models.user import User
from app.models.rbac import AuditLog
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserOut
from app.services.auth_service import (
    hash_password, verify_password,
    create_access_token, create_session, revoke_session,
    load_user_roles_permissions,
)
from app.dependencies.auth import get_current_user, require_admin, CurrentUser

log = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


async def _write_audit(
    db: AsyncSession,
    *,
    user_id: int | None,
    username: str | None,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    ip_address: str | None = None,
) -> None:
    db.add(AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
    ))
    await db.flush()


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalar_one_or_none()

    # Security: same error for missing user vs wrong password
    if not user or not user.is_active:
        raise HTTPException(401, "Invalid username or password")

    if user.is_locked:
        raise HTTPException(403, "Account is locked. Contact your administrator.")

    if not verify_password(payload.password, user.password_hash):
        # Increment failed login counter
        user.failed_login_count = (user.failed_login_count or 0) + 1
        if user.failed_login_count >= 5:
            user.is_locked = True
            log.warning(f"User '{user.username}' locked after 5 failed attempts")
        await db.commit()
        raise HTTPException(401, "Invalid username or password")

    # Reset failed login counter on success
    user.failed_login_count = 0
    user.last_login = datetime.now(timezone.utc)

    # Load roles + permissions
    roles, permissions = await load_user_roles_permissions(db, user.id)

    # Determine legacy flat role for backward-compat
    legacy_role = "admin" if ("SUPER_ADMIN" in roles or user.role == "admin") else "operator"

    # Create session
    ip = request.client.host if request.client else None
    session_id = await create_session(
        db,
        user_id=user.id,
        ip_address=ip,
        device_type="web",
        expires_in_seconds=int(8 * 3600),  # 8 hours
    )

    # Issue JWT
    token, expires_in = create_access_token(
        user_id=user.id,
        username=user.username,
        user_type=user.user_type,
        org_id=user.organization_id,
        customer_id=user.customer_id,
        roles=roles,
        permissions=permissions,
        session_id=session_id,
    )

    await _write_audit(db, user_id=user.id, username=user.username,
                       action="LOGIN", ip_address=ip)
    await db.commit()

    log.info(f"User '{user.username}' logged in (roles={roles})")
    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        username=user.username,
        user_type=user.user_type,
        role=legacy_role,
        roles=roles,
        permissions=permissions,
        org_id=user.organization_id,
        customer_id=user.customer_id,
    )


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke current session (soft-delete user_session row)."""
    if current.session_id:
        await revoke_session(db, current.session_id)
    ip = request.client.host if request.client else None
    await _write_audit(db, user_id=current.user_id or None,
                       username=current.username, action="LOGOUT", ip_address=ip)
    await db.commit()


@router.get("/me", response_model=UserOut)
async def get_me(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == current.username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    roles, permissions = await load_user_roles_permissions(db, user.id)
    out = UserOut.model_validate(user)
    out.roles = roles
    out.permissions = permissions
    return out


@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    """Admin-only — register a new user account."""
    existing = await db.execute(select(User).where(User.username == payload.username))
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Username '{payload.username}' already exists")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        email=payload.email,
        mobile=payload.mobile,
        first_name=payload.first_name,
        last_name=payload.last_name,
        full_name=payload.full_name,
        user_type=payload.user_type,
        role=payload.role,
        organization_id=payload.organization_id,
        customer_id=payload.customer_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    log.info(f"User '{user.username}' created (user_type={user.user_type})")
    out = UserOut.model_validate(user)
    out.roles = []
    out.permissions = []
    return out


@router.get("/users", response_model=list[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    result = await db.execute(select(User).order_by(User.username))
    users = result.scalars().all()
    out = []
    for u in users:
        roles, permissions = await load_user_roles_permissions(db, u.id)
        user_out = UserOut.model_validate(u)
        user_out.roles = roles
        user_out.permissions = permissions
        out.append(user_out)
    return out
