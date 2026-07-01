import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserOut
from app.services.auth_service import hash_password, verify_password, create_access_token
from app.dependencies.auth import get_current_user, require_admin, CurrentUser

log = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalar_one_or_none()

    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        # Same error for "no such user" and "wrong password" — don't leak which
        raise HTTPException(401, "Invalid username or password")

    token, expires_in = create_access_token(user.username, user.role)

    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    log.info(f"User '{user.username}' logged in")
    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        username=user.username,
        role=user.role,
    )


@router.get("/me", response_model=UserOut)
async def get_me(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == current.username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    """Admin-only — register a new operator/admin account."""
    existing = await db.execute(select(User).where(User.username == payload.username))
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Username '{payload.username}' already exists")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    log.info(f"User '{user.username}' created with role '{user.role}'")
    return user


@router.get("/users", response_model=list[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    result = await db.execute(select(User).order_by(User.username))
    return result.scalars().all()
