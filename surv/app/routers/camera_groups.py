"""
app/routers/camera_groups.py
Camera group CRUD and camera/user assignment endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies.auth import get_current_user, require_permission, CurrentUser
from app.models.rbac import CameraGroup, CameraGroupMapping, UserGroupMapping
from app.models.camera import Camera
from app.schemas.rbac import CameraGroupCreate, CameraGroupOut, CameraGroupCameraAssign, UserGroupAssign

log = logging.getLogger(__name__)
router = APIRouter(prefix="/camera-groups", tags=["camera groups"])


@router.get("/", response_model=list[CameraGroupOut])
async def list_groups(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(CameraGroup).order_by(CameraGroup.id))
    return result.scalars().all()


@router.post("/", response_model=CameraGroupOut, status_code=201)
async def create_group(
    payload: CameraGroupCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("camera.create")),
):
    group = CameraGroup(**payload.model_dump())
    db.add(group)
    await db.commit()
    await db.refresh(group)
    log.info(f"Camera group created: {group.name} (id={group.id})")
    return group


@router.get("/{group_id}", response_model=CameraGroupOut)
async def get_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    group = await db.get(CameraGroup, group_id)
    if not group:
        raise HTTPException(404, "Camera group not found")
    return group


@router.post("/{group_id}/cameras", status_code=204)
async def add_camera_to_group(
    group_id: int,
    payload: CameraGroupCameraAssign,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("camera.update")),
):
    group = await db.get(CameraGroup, group_id)
    if not group:
        raise HTTPException(404, "Camera group not found")
    camera = await db.get(Camera, payload.camera_id)
    if not camera:
        raise HTTPException(404, "Camera not found")
    existing = await db.execute(
        select(CameraGroupMapping)
        .where(CameraGroupMapping.group_id == group_id)
        .where(CameraGroupMapping.camera_id == payload.camera_id)
    )
    if not existing.scalar_one_or_none():
        db.add(CameraGroupMapping(group_id=group_id, camera_id=payload.camera_id))
        await db.commit()


@router.delete("/{group_id}/cameras/{camera_id}", status_code=204)
async def remove_camera_from_group(
    group_id: int,
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("camera.update")),
):
    result = await db.execute(
        select(CameraGroupMapping)
        .where(CameraGroupMapping.group_id == group_id)
        .where(CameraGroupMapping.camera_id == camera_id)
    )
    mapping = result.scalar_one_or_none()
    if mapping:
        await db.delete(mapping)
        await db.commit()


@router.post("/{group_id}/users", status_code=204)
async def add_user_to_group(
    group_id: int,
    payload: UserGroupAssign,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("user.update")),
):
    group = await db.get(CameraGroup, group_id)
    if not group:
        raise HTTPException(404, "Camera group not found")
    existing = await db.execute(
        select(UserGroupMapping)
        .where(UserGroupMapping.group_id == group_id)
        .where(UserGroupMapping.user_id == payload.user_id)
    )
    if not existing.scalar_one_or_none():
        db.add(UserGroupMapping(group_id=group_id, user_id=payload.user_id))
        await db.commit()
