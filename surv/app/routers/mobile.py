"""
app/routers/mobile.py
Phase 15 -- device registration + dashboard summary.
Phase 16 -- VPN session endpoints (stubbed until Headscale/acl_sync exist).
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import CurrentUser, get_current_user  # UNVERIFIED: file not seen directly,
                                                                   # inferred from access_service.py's import
from app.services.access_service import get_accessible_camera_ids
from app.models.mobile import MobileDevice
from app.models.camera import Camera, MotionEvent
from app.schemas.mobile import (
    RegisterDeviceIn,
    RegisterDeviceOut,
    DashboardSummaryOut,
    CameraSummary,
    VpnSessionRequest,
    VpnSessionResponse,
    VpnSessionRevoke,
)

router = APIRouter(prefix="/api/v1/mobile", tags=["mobile"])


# ---------------------------------------------------------------------------
# Phase 15 -- device registration
# ---------------------------------------------------------------------------

@router.post("/register-device", response_model=RegisterDeviceOut)
async def register_device(
    payload: RegisterDeviceIn,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Register (or refresh) an FCM/APNs push token for the current user's device.

    Upsert on (user_id, device_token) so repeated app launches don't create
    duplicate rows.
    """
    existing = await db.scalar(
        select(MobileDevice).where(
            MobileDevice.user_id == current_user.user_id,
            MobileDevice.device_token == payload.device_token,
        )
    )
    if existing:
        existing.platform = payload.platform
        existing.device_name = payload.device_name
        existing.app_version = payload.app_version
        existing.is_active = True
        existing.last_active = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(existing)
        return existing

    device = MobileDevice(
        user_id=current_user.user_id,
        device_token=payload.device_token,
        platform=payload.platform,
        device_name=payload.device_name,
        app_version=payload.app_version,
        is_active=True,
        last_active=datetime.now(timezone.utc),
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


# ---------------------------------------------------------------------------
# Phase 15 -- lightweight dashboard aggregate
# ---------------------------------------------------------------------------

@router.get("/dashboard-summary", response_model=DashboardSummaryOut)
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Single round-trip summary for the mobile home screen.

    Uses get_accessible_camera_ids() -- same RBAC scoping as the web app --
    NOT a raw unscoped select(Camera). Returns None for unrestricted roles
    (SUPER_ADMIN/NATIONAL_NOC/no-roles-set-yet), a list otherwise (which may
    be empty, meaning zero accessible cameras).
    """
    camera_ids = await get_accessible_camera_ids(current_user, db)

    if camera_ids is not None and len(camera_ids) == 0:
        return DashboardSummaryOut(
            total_cameras=0,
            online_cameras=0,
            offline_cameras=0,
            recent_motion_count_24h=0,
            cameras=[],
        )

    query = select(Camera).where(Camera.is_active == True)  # noqa: E712
    if camera_ids is not None:
        query = query.where(Camera.id.in_(camera_ids))

    result = await db.execute(query)
    cameras = result.scalars().all()
    ids = [c.id for c in cameras]

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    motion_count = 0
    last_motion_by_camera: dict[int, datetime] = {}

    if ids:
        motion_count = await db.scalar(
            select(func.count(MotionEvent.id)).where(
                MotionEvent.camera_id.in_(ids),
                MotionEvent.motion_start >= since,
            )
        ) or 0

        result = await db.execute(
            select(MotionEvent.camera_id, func.max(MotionEvent.motion_start))
            .where(MotionEvent.camera_id.in_(ids))
            .group_by(MotionEvent.camera_id)
        )
        last_motion_by_camera = dict(result.all())

    online = [c for c in cameras if c.is_online]
    offline = [c for c in cameras if not c.is_online]

    return DashboardSummaryOut(
        total_cameras=len(cameras),
        online_cameras=len(online),
        offline_cameras=len(offline),
        recent_motion_count_24h=motion_count,
        cameras=[
            CameraSummary(
                camera_id=c.id,
                name=c.cam_name or c.cam_id,
                is_online=c.is_online,
                last_motion_at=last_motion_by_camera.get(c.id),
            )
            for c in cameras
        ],
    )


# ---------------------------------------------------------------------------
# Phase 16 -- VPN session (embedded WireGuard). STUBBED until Headscale
# (Phase 14) is confirmed deployed and acl_sync_service exists. Returns 501
# rather than a fake response so the mobile client fails loudly instead of
# silently treating a stub as a real tunnel config.
# ---------------------------------------------------------------------------

@router.post("/vpn-session", response_model=VpnSessionResponse)
async def create_vpn_session(
    payload: VpnSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "VPN session issuance depends on Phase 14 (Headscale) and "
            "acl_sync_service, which are not yet wired. Implement "
            "app/services/headscale_client.py and replace this stub."
        ),
    )


@router.delete("/vpn-session", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_vpn_session(
    payload: VpnSessionRevoke,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="VPN session revocation depends on Phase 14 (Headscale) integration.",
    )