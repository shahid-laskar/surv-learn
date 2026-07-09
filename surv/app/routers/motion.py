import os
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update, func
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.database import get_db
from app.models.camera import MotionEvent
from app.schemas.motion import MotionEventOut
from app.dependencies.auth import get_current_user, CurrentUser
from app.services.access_service import get_accessible_camera_ids, ensure_camera_accessible

router = APIRouter(prefix="/motion", tags=["motion"])

STALE_ACTIVE_SECONDS = int(os.getenv("MOTION_ACTIVE_STALE_SECONDS", "1800"))  # 30 minutes


async def close_stale_motion_events(db: AsyncSession) -> None:
    """
    If we miss a `motion_end` (e.g. edge/network disconnect), a row can remain
    stuck as `is_active=true` with `motion_end=NULL`. Close it on read so the
    UI self-recovers.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=STALE_ACTIVE_SECONDS)
    await db.execute(
        update(MotionEvent)
        .where(
            MotionEvent.is_active == True,  # noqa: E712
            MotionEvent.motion_end.is_(None),
            MotionEvent.motion_start < cutoff,
        )
        .values(motion_end=func.now(), is_active=False)
    )
    await db.commit()


@router.get("/active", response_model=List[MotionEventOut])
async def active_motion_events(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    await close_stale_motion_events(db)
    q = (
        select(MotionEvent)
        .where(MotionEvent.is_active == True)   # noqa: E712
        .order_by(desc(MotionEvent.motion_start))
    )
    accessible_ids = await get_accessible_camera_ids(user, db)
    if accessible_ids is not None:
        if not accessible_ids:
            return []
        q = q.where(MotionEvent.camera_id.in_(accessible_ids))
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/", response_model=List[MotionEventOut])
async def list_motion_events(
    camera_id: Optional[int] = Query(None),
    active:    Optional[bool] = Query(None),
    limit:     int = Query(50, le=500),
    db:        AsyncSession = Depends(get_db),
    user:      CurrentUser = Depends(get_current_user),
):
    await close_stale_motion_events(db)
    accessible_ids = await get_accessible_camera_ids(user, db)
    if accessible_ids is not None and not accessible_ids:
        return []

    q = (
        select(MotionEvent)
        .order_by(desc(MotionEvent.motion_start))
        .limit(limit)
    )
    if accessible_ids is not None:
        q = q.where(MotionEvent.camera_id.in_(accessible_ids))
    if camera_id is not None:
        if accessible_ids is not None and camera_id not in accessible_ids:
            raise HTTPException(status_code=403, detail="Access to this camera is not permitted")
        q = q.where(MotionEvent.camera_id == camera_id)
    if active is not None:
        q = q.where(MotionEvent.is_active == active)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{event_id}", response_model=MotionEventOut)
async def get_motion_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        select(MotionEvent).where(MotionEvent.id == event_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(404, f"Motion event {event_id} not found")
    await ensure_camera_accessible(user, db, event.camera_id)
    return event
