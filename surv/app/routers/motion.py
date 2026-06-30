from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timezone
from typing import List, Optional
from app.database import get_db
from app.models.camera import MotionEvent
from app.schemas.motion import MotionEventOut

router = APIRouter(prefix="/motion", tags=["motion"])


@router.get("/", response_model=List[MotionEventOut])
async def list_motion_events(
    camera_id: Optional[int] = Query(None),
    active:    Optional[bool] = Query(None),
    limit:     int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(MotionEvent).order_by(desc(MotionEvent.motion_start)).limit(limit)
    if camera_id is not None:
        q = q.where(MotionEvent.camera_id == camera_id)
    if active is not None:
        q = q.where(MotionEvent.is_active == active)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/active", response_model=List[MotionEventOut])
async def active_motion_events(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MotionEvent)
        .where(MotionEvent.is_active == True)
        .order_by(desc(MotionEvent.motion_start))
    )
    return result.scalars().all()


@router.get("/{event_id}", response_model=MotionEventOut)
async def get_motion_event(event_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MotionEvent).where(MotionEvent.id == event_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        from fastapi import HTTPException
        raise HTTPException(404, f"Event {event_id} not found")
    return event