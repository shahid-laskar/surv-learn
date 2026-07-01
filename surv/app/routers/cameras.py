import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.camera import Camera
from app.schemas.camera import CameraCreate, CameraUpdate, CameraOut
from app.dependencies.auth import get_current_user, require_admin, CurrentUser

log = logging.getLogger(__name__)
router = APIRouter(prefix="/cameras", tags=["cameras"])


@router.get("/", response_model=List[CameraOut])
async def list_cameras(
    db: AsyncSession = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        select(Camera).where(Camera.is_active == True).order_by(Camera.cam_id)
    )
    return result.scalars().all()


@router.post("/", response_model=CameraOut, status_code=201)
async def create_camera(
    payload: CameraCreate,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    existing = await db.execute(select(Camera).where(Camera.cam_id == payload.cam_id))
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Camera '{payload.cam_id}' already exists")
    cam = Camera(**payload.model_dump())
    db.add(cam)
    await db.commit()
    await db.refresh(cam)
    log.info(f"Camera registered: {cam.cam_id} ({cam.cam_ip})")
    return cam


@router.get("/{cam_id}", response_model=CameraOut)
async def get_camera(
    cam_id: str,
    db: AsyncSession = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(Camera).where(Camera.cam_id == cam_id))
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(404, f"Camera '{cam_id}' not found")
    return cam


@router.patch("/{cam_id}", response_model=CameraOut)
async def update_camera(
    cam_id: str,
    payload: CameraUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
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
    _admin: CurrentUser = Depends(require_admin),
):
    result = await db.execute(select(Camera).where(Camera.cam_id == cam_id))
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(404, f"Camera '{cam_id}' not found")
    cam.is_active = False
    await db.commit()
