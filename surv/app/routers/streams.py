from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.camera import Camera
from app.services.mediamtx_service import is_path_ready
from app.services.minio_service import get_presigned_url
from app.config import settings

router = APIRouter(prefix="/streams", tags=["streams"])


@router.get("/{cam_id}/hls-url")
async def get_hls_url(cam_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Camera).where(Camera.cam_id == cam_id))
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(404, f"Camera '{cam_id}' not found")
    ready = await is_path_ready(cam_id)
    return {
        "cam_id":   cam_id,
        "hls_url":  f"{settings.mediamtx_hls_base}/{cam_id}/index.m3u8",
        "ready":    ready,
    }


@router.get("/{cam_id}/webrtc-url")
async def get_webrtc_url(cam_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Camera).where(Camera.cam_id == cam_id))
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(404, f"Camera '{cam_id}' not found")
    return {
        "cam_id":     cam_id,
        "webrtc_url": f"{settings.mediamtx_webrtc_base}/{cam_id}",
    }


@router.get("/{cam_id}/snapshot-url")
async def get_snapshot_url(cam_id: str):
    # Latest snapshot is stored as cam_id/latest.jpg by convention
    # (snapshot_worker saves timestamped files; update if you want latest symlink)
    url = get_presigned_url(
        object_key=f"{cam_id}/latest.jpg",
        bucket=settings.minio_bucket_snapshots,
        expires_in=300,
    )
    return {"cam_id": cam_id, "snapshot_url": url}