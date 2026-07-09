import os
from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update, func
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.database import get_db
from app.models.camera import MotionEvent, Camera
from app.models.nvr import NvrNode, NvrCameraMap
from app.schemas.motion import MotionEventOut, EdgeMotionIn
from app.dependencies.auth import get_current_user, CurrentUser
from app.dependencies.fleet_auth import verify_site_token
from app.services.access_service import get_accessible_camera_ids, ensure_camera_accessible

router = APIRouter(prefix="/motion", tags=["motion"])

STALE_ACTIVE_SECONDS = int(os.getenv("MOTION_ACTIVE_STALE_SECONDS", "1800"))  # 30 minutes


async def _verify_edge_site(
    payload: EdgeMotionIn,
    db: AsyncSession = Depends(get_db),
    x_site_token: str | None = Header(None, alias="X-Site-Token"),
) -> NvrNode:
    return await verify_site_token(payload.site_code, db, x_site_token)


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


@router.post("/edge", status_code=status.HTTP_201_CREATED)
async def ingest_edge_motion(
    payload: EdgeMotionIn,
    db: AsyncSession = Depends(get_db),
    node: NvrNode = Depends(_verify_edge_site),
):
    """Edge-agent pushes motion events (authenticated via X-Site-Token)."""
    if node.site_code != payload.site_code:
        raise HTTPException(status_code=403, detail="Site code mismatch")

    camera = await db.scalar(
        select(Camera)
        .join(NvrCameraMap, NvrCameraMap.camera_id == Camera.id)
        .where(NvrCameraMap.nvr_node_id == node.id)
        .where(Camera.cam_id == payload.cam_id)
    )
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not on this NVR")

    if payload.is_active and not payload.motion_end:
        event = MotionEvent(
            camera_id=camera.id,
            motion_start=payload.motion_start,
            motion_end=None,
            is_active=True,
        )
        db.add(event)
    else:
        # Close or record ended event
        if payload.motion_end:
            event = MotionEvent(
                camera_id=camera.id,
                motion_start=payload.motion_start,
                motion_end=payload.motion_end,
                is_active=False,
            )
            db.add(event)
        else:
            await db.execute(
                update(MotionEvent)
                .where(
                    MotionEvent.camera_id == camera.id,
                    MotionEvent.is_active == True,  # noqa: E712
                )
                .values(motion_end=payload.motion_start, is_active=False)
            )

    await db.commit()
    return {"status": "ok"}
