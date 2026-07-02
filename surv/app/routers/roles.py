"""
app/routers/roles.py
CRUD for roles and permissions, and user/role assignment endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies.auth import get_current_user, require_permission, CurrentUser
from app.models.rbac import Role, Permission, RolePermission, UserRole
from app.models.user import User
from app.schemas.rbac import (
    RoleCreate, RoleOut, PermissionCreate, PermissionOut,
    RolePermissionAssign, UserRoleAssign,
)

log = logging.getLogger(__name__)
router = APIRouter(tags=["roles & permissions"])


# ── Roles ─────────────────────────────────────────────────────────────────────

@router.get("/roles/", response_model=list[RoleOut])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(Role).order_by(Role.code))
    return result.scalars().all()


@router.post("/roles/", response_model=RoleOut, status_code=201)
async def create_role(
    payload: RoleCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("system.settings")),
):
    role = Role(**payload.model_dump())
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


@router.get("/roles/{role_id}/permissions", response_model=list[PermissionOut])
async def list_role_permissions(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        select(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role_id)
        .order_by(Permission.code)
    )
    return result.scalars().all()


@router.post("/roles/{role_id}/permissions", status_code=204)
async def assign_permission_to_role(
    role_id: int,
    payload: RolePermissionAssign,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("system.settings")),
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(404, "Role not found")
    perm = await db.get(Permission, payload.permission_id)
    if not perm:
        raise HTTPException(404, "Permission not found")
    # Idempotent
    existing = await db.execute(
        select(RolePermission)
        .where(RolePermission.role_id == role_id)
        .where(RolePermission.permission_id == payload.permission_id)
    )
    if not existing.scalar_one_or_none():
        db.add(RolePermission(role_id=role_id, permission_id=payload.permission_id))
        await db.commit()
        log.info(f"Permission {perm.code} assigned to role {role.code}")


@router.delete("/roles/{role_id}/permissions/{perm_id}", status_code=204)
async def remove_permission_from_role(
    role_id: int,
    perm_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("system.settings")),
):
    result = await db.execute(
        select(RolePermission)
        .where(RolePermission.role_id == role_id)
        .where(RolePermission.permission_id == perm_id)
    )
    rp = result.scalar_one_or_none()
    if rp:
        await db.delete(rp)
        await db.commit()


# ── Permissions ───────────────────────────────────────────────────────────────

@router.get("/permissions/", response_model=list[PermissionOut])
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(Permission).order_by(Permission.code))
    return result.scalars().all()


@router.post("/permissions/", response_model=PermissionOut, status_code=201)
async def create_permission(
    payload: PermissionCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("system.settings")),
):
    perm = Permission(**payload.model_dump())
    db.add(perm)
    await db.commit()
    await db.refresh(perm)
    return perm


# ── User role assignment ──────────────────────────────────────────────────────

@router.post("/users/{user_id}/roles", status_code=204)
async def assign_role_to_user(
    user_id: int,
    payload: UserRoleAssign,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("user.update")),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        raise HTTPException(404, "User not found")
    role = await db.get(Role, payload.role_id)
    if not role:
        raise HTTPException(404, "Role not found")
    existing = await db.execute(
        select(UserRole)
        .where(UserRole.user_id == user_id)
        .where(UserRole.role_id == payload.role_id)
    )
    if not existing.scalar_one_or_none():
        db.add(UserRole(user_id=user_id, role_id=payload.role_id))
        await db.commit()
        log.info(f"Role {role.code} assigned to user {target_user.username}")


@router.delete("/users/{user_id}/roles/{role_id}", status_code=204)
async def remove_role_from_user(
    user_id: int,
    role_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("user.update")),
):
    result = await db.execute(
        select(UserRole)
        .where(UserRole.user_id == user_id)
        .where(UserRole.role_id == role_id)
    )
    ur = result.scalar_one_or_none()
    if ur:
        await db.delete(ur)
        await db.commit()
