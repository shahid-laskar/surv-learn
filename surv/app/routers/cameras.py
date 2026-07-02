import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.camera import Camera
from app.schemas.camera import CameraCreate, CameraUpdate, CameraOut
from app.dependencies.auth import get_current_user, require_admin, require_permission, CurrentUser
from app.services.access_service import get_accessible_camera_ids

log = logging.getLogger(__name__)
router = APIRouter(prefix="/cameras", tags=["cameras"])


@router.get("/", response_model=List[CameraOut])
async def list_cameras(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("camera.view")),
):
    """List cameras the current user is allowed to see (org-scope + direct grants + groups)."""
    accessible_ids = await get_accessible_camera_ids(user, db)

    q = select(Camera).where(Camera.is_active == True).order_by(Camera.cam_id)  # noqa: E712
    if accessible_ids is not None:
        # Scoped access — filter by allowed IDs
        if not accessible_ids:
            return []   # user has no cameras at all
        q = q.where(Camera.id.in_(accessible_ids))

    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=CameraOut, status_code=201)
async def create_camera(
    payload: CameraCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("camera.create")),
):
    existing = await db.execute(select(Camera).where(Camera.cam_id == payload.cam_id))
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Camera '{payload.cam_id}' already exists")
    cam = Camera(**payload.model_dump())
    db.add(cam)
    await db.commit()
    await db.refresh(cam)
    log.info(f"Camera registered: {cam.cam_id} ({cam.cam_ip}) by {user.username}")
    return cam


@router.get("/{cam_id}", response_model=CameraOut)
async def get_camera(
    cam_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("camera.view")),
):
    result = await db.execute(select(Camera).where(Camera.cam_id == cam_id))
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(404, f"Camera '{cam_id}' not found")

    # Check scoped access
    accessible_ids = await get_accessible_camera_ids(user, db)
    if accessible_ids is not None and cam.id not in accessible_ids:
        raise HTTPException(403, "Access to this camera is not permitted")

    return cam


@router.patch("/{cam_id}", response_model=CameraOut)
async def update_camera(
    cam_id: str,
    payload: CameraUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("camera.update")),
):
    result = await db.execute(select(Camera).where(Camera.cam_id == cam_id))
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(404, f"Camera '{cam_id}' not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(cam, field, value)
    await db.commit()
    await db.refresh(cam)
    return cam


@router.delete("/{cam_id}", status_code=204)
async def deactivate_camera(
    cam_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("camera.delete")),
):
    result = await db.execute(select(Camera).where(Camera.cam_id == cam_id))
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(404, f"Camera '{cam_id}' not found")
    cam.is_active = False
    await db.commit()
    log.info(f"Camera deactivated: {cam_id} by {user.username}")
