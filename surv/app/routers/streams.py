from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone

from app.database import get_db
from app.models.camera import Camera
from app.models.nvr import NvrNode
from app.services.mediamtx_service import is_path_ready
from app.services.minio_service import get_presigned_url
from app.services.auth_service import create_stream_token
from app.dependencies.auth import require_permission, CurrentUser
from app.schemas.auth import StreamTokenResponse
from app.config import settings

router = APIRouter(prefix="/streams", tags=["streams"])


@router.get("/{cam_id}/hls-url", response_model=StreamTokenResponse)
async def get_hls_url(
    cam_id: str,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_permission("camera.live")),
):
    q = select(Camera, NvrNode).outerjoin(NvrNode, Camera.nvr_node_id == NvrNode.id).where(Camera.cam_id == cam_id)
    result = await db.execute(q)
    row = result.first()
    if not row:
        raise HTTPException(404, f"Camera '{cam_id}' not found")
        
    cam, nvr = row

    if not nvr:
        await is_path_ready(cam_id)
        token = create_stream_token(cam_id, current.username, expires_in=3600)
        hls_url = f"{settings.mediamtx_hls_base}/{cam_id}/index.m3u8?token={token}"
    else:
        # Edge Camera branch
        token = create_stream_token(cam_id, current.username, expires_in=3600)
        # Using the overlay IP from VPN
        overlay_ip = nvr.overlay_ip or "127.0.0.1" # fallback
        hls_url = f"http://{overlay_ip}:8888/{cam_id}/index.m3u8?token={token}"

    return StreamTokenResponse(
        cam_id=cam_id,
        hls_url=hls_url,
        token=token,
        expires_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/{cam_id}/webrtc-url")
async def get_webrtc_url(
    cam_id: str,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(require_permission("camera.live")),
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
    current: CurrentUser = Depends(require_permission("camera.view")),
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
