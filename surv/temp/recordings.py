import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from typing import List

from app.database import get_db
from app.models.camera import Camera, VideoSegment
from app.services.minio_service import get_presigned_url
from app.schemas.recording import TimelineOut, SegmentOut
from app.dependencies.auth import require_permission, CurrentUser

log = logging.getLogger(__name__)
router = APIRouter(prefix="/recordings", tags=["recordings"])


@router.get("/{cam_id}/timeline", response_model=TimelineOut)
async def get_timeline(
    cam_id: str,
    date:   str = Query(..., example="2026-06-27", description="YYYY-MM-DD"),
    db:     AsyncSession = Depends(get_db),
    user:   CurrentUser = Depends(require_permission("camera.playback")),
):
    cam_result = await db.execute(select(Camera).where(Camera.cam_id == cam_id))
    cam = cam_result.scalar_one_or_none()
    if not cam:
        raise HTTPException(404, f"Camera '{cam_id}' not found")

    try:
        day_start = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(422, "date must be YYYY-MM-DD")

    day_end = day_start + timedelta(days=1)

    seg_result = await db.execute(
        select(VideoSegment)
        .where(VideoSegment.camera_id == cam.id)
        .where(VideoSegment.segment_start >= day_start)
        .where(VideoSegment.segment_start <  day_end)
        .where(VideoSegment.deleted_at    == None)   # noqa: E711
        .order_by(VideoSegment.segment_start)
    )
    segments = seg_result.scalars().all()

    out: List[SegmentOut] = []
    for seg in segments:
        try:
            url = get_presigned_url(seg.object_key, seg.bucket)
        except Exception as e:
            log.warning(f"Presign failed for {seg.object_key}: {e}")
            url = ""
        out.append(SegmentOut(
            segment_id=seg.id,
            start=seg.segment_start,
            end=seg.segment_end,
            duration_seconds=seg.duration_seconds,
            playback_url=url,
        ))

    return TimelineOut(
        camera_id=cam_id,
        date=date,
        total_segments=len(out),
        segments=out,
    )


@router.get("/{cam_id}/download")
async def get_download_url(
    cam_id:     str,
    object_key: str = Query(..., description="MinIO object key of the segment"),
    db:         AsyncSession = Depends(get_db),
    user:       CurrentUser = Depends(require_permission("camera.download")),
):
    cam_result = await db.execute(select(Camera).where(Camera.cam_id == cam_id))
    cam = cam_result.scalar_one_or_none()
    if not cam:
        raise HTTPException(404, f"Camera '{cam_id}' not found")

    seg_result = await db.execute(
        select(VideoSegment)
        .where(VideoSegment.object_key == object_key)
        .where(VideoSegment.camera_id  == cam.id)
    )
    seg = seg_result.scalar_one_or_none()
    if not seg:
        raise HTTPException(404, "Segment not found for this camera")

    url = get_presigned_url(object_key, expires_in=3600)
    return {"download_url": url, "expires_in": 3600}
