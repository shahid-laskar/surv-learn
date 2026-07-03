from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import boto3
import httpx

from app.database import get_db
from app.dependencies.auth import get_current_user, CurrentUser
from app.models.camera import Camera, CameraStatusLog, MotionEvent
from app.schemas.health import (
    HealthSummaryOut, CameraHealthOut, StatusLogEntry, StorageStats, StorageBucketStats
)
from app.config import settings
from app.services.access_service import get_accessible_camera_ids
from app.services.mediamtx_service import get_active_paths

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health():
    return {"status": "ok"}


@router.get("/services")
async def service_health():
    """Legacy service check (used by frontend /health check)"""
    checks = {}

    try:
        paths = await get_active_paths()
        checks["mediamtx"] = {"status": "healthy", "active_paths": len(paths)}
    except Exception as e:
        checks["mediamtx"] = {"status": "unreachable", "error": str(e)}

    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=f"http://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            region_name="us-east-1",
        )
        s3.list_buckets()
        checks["minio"] = {"status": "healthy"}
    except Exception as e:
        checks["minio"] = {"status": "unreachable", "error": str(e)}

    return checks


@router.get("/summary", response_model=HealthSummaryOut)
async def get_health_summary(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Overall dashboard summary."""
    allowed_ids = await get_accessible_camera_ids(user, db)
    
    # Base queries
    cam_q = select(Camera).where(Camera.is_active == True)
    motion_q = select(func.count(MotionEvent.id)).where(MotionEvent.is_active == True)
    
    if allowed_ids is not None:
        cam_q = cam_q.where(Camera.id.in_(allowed_ids))
        motion_q = motion_q.where(MotionEvent.camera_id.in_(allowed_ids))

    cams_result = await db.execute(cam_q)
    cameras = cams_result.scalars().all()

    total_cameras = len(cameras)
    online_cameras = sum(1 for c in cameras if c.is_online)
    offline_cameras = total_cameras - online_cameras

    motion_result = await db.execute(motion_q)
    active_motion = motion_result.scalar_one_or_none() or 0

    return HealthSummaryOut(
        total_cameras=total_cameras,
        online_cameras=online_cameras,
        offline_cameras=offline_cameras,
        active_motion=active_motion,
        worker_health={
            "kafka": "unknown",     # Can be pinged if needed, skipping for fast response
            "minio": "unknown",
            "mediamtx": "unknown",
            "postgres": "healthy"   # We're connected
        },
        checked_at=datetime.now(timezone.utc)
    )


@router.get("/cameras", response_model=List[CameraHealthOut])
async def get_camera_health(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Per-camera health list."""
    allowed_ids = await get_accessible_camera_ids(user, db)
    
    q = select(Camera).where(Camera.is_active == True)
    if allowed_ids is not None:
        q = q.where(Camera.id.in_(allowed_ids))

    result = await db.execute(q)
    cameras = result.scalars().all()

    out = []
    now = datetime.now(timezone.utc)
    for c in cameras:
        offline_minutes = None
        if not c.is_online and c.last_seen:
            offline_minutes = int((now - c.last_seen).total_seconds() / 60)
        
        # Calculate uptime_pct_24h (mock for now; requires complex query on status log)
        # We can implement a proper calculation by querying the log if needed.
        uptime_pct = 100.0 if c.is_online else 0.0

        out.append(CameraHealthOut(
            camera_id=c.cam_id,
            name=c.cam_name,
            is_online=c.is_online,
            last_seen=c.last_seen,
            offline_minutes=offline_minutes,
            uptime_pct_24h=uptime_pct
        ))
    
    return out


@router.get("/cameras/{cam_id}/history", response_model=List[StatusLogEntry])
async def get_camera_history(
    cam_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Recent status history for a camera."""
    allowed_ids = await get_accessible_camera_ids(user, db)
    
    cam_q = select(Camera.id).where(Camera.cam_id == cam_id).where(Camera.is_active == True)
    res = await db.execute(cam_q)
    c_id = res.scalar_one_or_none()

    if not c_id:
        raise HTTPException(status_code=404, detail="Camera not found")

    if allowed_ids is not None and c_id not in allowed_ids:
        raise HTTPException(status_code=403, detail="Not authorized to view this camera")

    log_q = (
        select(CameraStatusLog)
        .where(CameraStatusLog.camera_id == c_id)
        .order_by(CameraStatusLog.changed_at.desc())
        .limit(50)
    )
    result = await db.execute(log_q)
    return result.scalars().all()


@router.get("/storage", response_model=StorageStats)
async def get_storage_stats(
    user: CurrentUser = Depends(get_current_user),
):
    """Storage statistics."""
    # Enforce admin permission for storage stats
    if "SUPER_ADMIN" not in user.roles and "system.settings" not in user.permissions:
         raise HTTPException(status_code=403, detail="Admin access required")

    buckets_stats = []
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=f"http://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            region_name="us-east-1",
        )
        for b in [settings.minio_bucket_recordings, settings.minio_bucket_snapshots]:
            # Simple count/size check using list_objects_v2 (limited for speed)
            # In a real heavy prod scenario, use MinIO admin API or Prometheus metrics
            res = s3.list_objects_v2(Bucket=b, MaxKeys=1000)
            total_size = sum(obj['Size'] for obj in res.get('Contents', []))
            count = len(res.get('Contents', []))
            oldest = min((obj['LastModified'] for obj in res.get('Contents', [])), default=None)
            
            buckets_stats.append(StorageBucketStats(
                bucket=b,
                total_size_gb=total_size / (1024**3),
                object_count=count,
                oldest_object=oldest.isoformat() if oldest else None
            ))
    except Exception as e:
        print(f"S3 Error: {e}")
        # Return empty if S3 fails

    return StorageStats(
        buckets=buckets_stats,
        recordings_dir_gb=None,  # Could use os.statvfs but we are in a container
        checked_at=datetime.now(timezone.utc)
    )