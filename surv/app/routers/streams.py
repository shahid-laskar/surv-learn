from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.database import get_db
from app.models.camera import Camera
from app.services.mediamtx_service import is_path_ready
from app.services.minio_service import get_presigned_url
from app.services.auth_service import create_stream_token
from app.dependencies.auth import get_current_user, CurrentUser
from app.schemas.auth import StreamTokenResponse
from app.config import settings

router = APIRouter(prefix="/streams", tags=["streams"])


@router.get("/{cam_id}/hls-url", response_model=StreamTokenResponse)
async def get_hls_url(
    cam_id: str,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(Camera).where(Camera.cam_id == cam_id))
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(404, f"Camera '{cam_id}' not found")

    ready = await is_path_ready(cam_id)
    token = create_stream_token(cam_id, current.username, expires_in=3600)

    return StreamTokenResponse(
        cam_id=cam_id,
        hls_url=f"{settings.mediamtx_hls_base}/{cam_id}/index.m3u8?token={token}",
        token=token,
        expires_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/{cam_id}/webrtc-url")
async def get_webrtc_url(
    cam_id: str,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(Camera).where(Camera.cam_id == cam_id))
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(404, f"Camera '{cam_id}' not found")

    token = create_stream_token(cam_id, current.username, expires_in=3600)
    return {
        "cam_id":     cam_id,
        "webrtc_url": f"{settings.mediamtx_webrtc_base}/{cam_id}?token={token}",
    }


@router.get("/{cam_id}/snapshot-url")
async def get_snapshot_url(
    cam_id: str,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(Camera).where(Camera.cam_id == cam_id))
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(404, f"Camera '{cam_id}' not found")
    try:
        url = get_presigned_url(
            object_key=f"{cam_id}/latest.jpg",
            bucket=settings.minio_bucket_snapshots,
            expires_in=300,
        )
    except Exception:
        raise HTTPException(503, "Snapshot not available")
    return {"cam_id": cam_id, "snapshot_url": url}
