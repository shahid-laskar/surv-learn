from datetime import datetime, timezone
from typing import List
import secrets

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.database import get_db
from app.dependencies.auth import get_current_user, CurrentUser
from app.dependencies.fleet_auth import verify_site_token
from app.models.nvr import NvrNode, NvrCameraMap, BackupClip
from app.models.camera import Camera
from app.schemas.fleet import (
    NvrNodeOut,
    HeartbeatIn,
    FleetConfigOut,
    BackupClipIn,
    NvrProvisionRequest,
    CameraConfigOut,
    NvrCameraAssignIn,
    NvrCameraOut,
)
from app.config import settings

router = APIRouter(prefix="/fleet", tags=["fleet"])


def _admin_required(user: CurrentUser) -> None:
    if "SUPER_ADMIN" not in user.roles and "system.settings" not in user.permissions:
        raise HTTPException(status_code=403, detail="Not authorized")


@router.get("/", response_model=List[NvrNodeOut])
async def list_nvrs(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _admin_required(user)
    q = select(NvrNode).order_by(NvrNode.created_at.desc())
    result = await db.execute(q)
    nodes = result.scalars().all()

    out = []
    for node in nodes:
        count_q = select(func.count(NvrCameraMap.camera_id)).where(
            NvrCameraMap.nvr_node_id == node.id
        )
        count = await db.scalar(count_q)
        node_dict = {k: v for k, v in node.__dict__.items() if not k.startswith("_")}
        node_dict["camera_count"] = count or 0
        node_dict["site_token"] = None
        out.append(NvrNodeOut(**node_dict))
    return out


@router.post("/", response_model=NvrNodeOut)
async def provision_nvr(
    req: NvrProvisionRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _admin_required(user)
    site_token = secrets.token_urlsafe(32)
    new_node = NvrNode(
        site_code=req.site_code,
        customer_site_id=req.customer_site_id,
        hardware_label=req.hardware_label,
        wg_node_key=secrets.token_hex(16),
        site_enrollment_secret=site_token,
        is_provisioned=False,
    )
    db.add(new_node)
    try:
        await db.commit()
        await db.refresh(new_node)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    node_dict = {k: v for k, v in new_node.__dict__.items() if not k.startswith("_")}
    node_dict["camera_count"] = 0
    node_dict["site_token"] = site_token
    return NvrNodeOut(**node_dict)


@router.get("/{site_code}", response_model=NvrNodeOut)
async def get_nvr(
    site_code: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _admin_required(user)
    node = await db.scalar(select(NvrNode).where(NvrNode.site_code == site_code))
    if not node:
        raise HTTPException(status_code=404, detail="NVR not found")

    count = await db.scalar(
        select(func.count(NvrCameraMap.camera_id)).where(
            NvrCameraMap.nvr_node_id == node.id
        )
    )
    node_dict = {k: v for k, v in node.__dict__.items() if not k.startswith("_")}
    node_dict["camera_count"] = count or 0
    node_dict["site_token"] = None
    return NvrNodeOut(**node_dict)


@router.delete("/{site_code}", status_code=status.HTTP_204_NO_CONTENT)
async def decommission_nvr(
    site_code: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _admin_required(user)
    node = await db.scalar(select(NvrNode).where(NvrNode.site_code == site_code))
    if not node:
        raise HTTPException(status_code=404, detail="NVR not found")

    await db.execute(
        update(Camera).where(Camera.nvr_node_id == node.id).values(nvr_node_id=None)
    )
    await db.delete(node)
    await db.commit()


@router.get("/{site_code}/cameras", response_model=List[NvrCameraOut])
async def list_nvr_cameras(
    site_code: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _admin_required(user)
    node = await db.scalar(select(NvrNode).where(NvrNode.site_code == site_code))
    if not node:
        raise HTTPException(status_code=404, detail="NVR not found")

    cam_q = select(Camera).join(NvrCameraMap).where(NvrCameraMap.nvr_node_id == node.id)
    cameras = (await db.scalars(cam_q)).all()
    return [
        NvrCameraOut(cam_id=c.cam_id, cam_ip=c.cam_ip, is_online=bool(c.is_online))
        for c in cameras
    ]


@router.post("/{site_code}/cameras", status_code=status.HTTP_201_CREATED)
async def assign_camera_to_nvr(
    site_code: str,
    body: NvrCameraAssignIn,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _admin_required(user)
    node = await db.scalar(select(NvrNode).where(NvrNode.site_code == site_code))
    if not node:
        raise HTTPException(status_code=404, detail="NVR not found")

    camera = await db.scalar(select(Camera).where(Camera.cam_id == body.cam_id))
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    existing = await db.scalar(
        select(NvrCameraMap).where(NvrCameraMap.camera_id == camera.id)
    )
    if existing and existing.nvr_node_id != node.id:
        raise HTTPException(status_code=409, detail="Camera already assigned to another NVR")

    if not existing:
        db.add(NvrCameraMap(nvr_node_id=node.id, camera_id=camera.id))

    camera.nvr_node_id = node.id
    await db.commit()
    return {"status": "ok", "cam_id": body.cam_id}


@router.delete("/{site_code}/cameras/{cam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unassign_camera_from_nvr(
    site_code: str,
    cam_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _admin_required(user)
    node = await db.scalar(select(NvrNode).where(NvrNode.site_code == site_code))
    if not node:
        raise HTTPException(status_code=404, detail="NVR not found")

    camera = await db.scalar(select(Camera).where(Camera.cam_id == cam_id))
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    mapping = await db.scalar(
        select(NvrCameraMap).where(
            NvrCameraMap.nvr_node_id == node.id,
            NvrCameraMap.camera_id == camera.id,
        )
    )
    if mapping:
        await db.delete(mapping)
    camera.nvr_node_id = None
    await db.commit()


# --- Edge agent endpoints (X-Site-Token required) ---


@router.post("/heartbeat")
async def heartbeat(
    hb: HeartbeatIn,
    db: AsyncSession = Depends(get_db),
    x_site_token: str | None = Header(None, alias="X-Site-Token"),
):
    node = await db.scalar(select(NvrNode).where(NvrNode.site_code == hb.site_code))
    if not node:
        raise HTTPException(status_code=404, detail="NVR not provisioned on hub")

    if not node.site_enrollment_secret or not x_site_token:
        raise HTTPException(status_code=401, detail="Missing site credentials")
    if not secrets.compare_digest(x_site_token, node.site_enrollment_secret):
        raise HTTPException(status_code=401, detail="Invalid site credentials")

    node.agent_version = hb.agent_version
    node.disk_used_pct = hb.disk_used_pct
    node.last_heartbeat = datetime.now(timezone.utc)
    node.is_provisioned = True
    if hb.overlay_ip:
        node.overlay_ip = hb.overlay_ip

    now = datetime.now(timezone.utc)
    if node.id is not None:
        if hb.online_cameras:
            await db.execute(
                update(Camera)
                .where(Camera.cam_id.in_(hb.online_cameras))
                .where(
                    Camera.id.in_(
                        select(NvrCameraMap.camera_id).where(
                            NvrCameraMap.nvr_node_id == node.id
                        )
                    )
                )
                .values(is_online=True, last_seen=now)
            )
        await db.execute(
            update(Camera)
            .where(~Camera.cam_id.in_(hb.online_cameras or []))
            .where(
                Camera.id.in_(
                    select(NvrCameraMap.camera_id).where(
                        NvrCameraMap.nvr_node_id == node.id
                    )
                )
            )
            .values(is_online=False)
        )

    await db.commit()
    return {"status": "ok"}


@router.get("/{site_code}/config", response_model=FleetConfigOut)
async def get_config(
    site_code: str,
    db: AsyncSession = Depends(get_db),
    node: NvrNode = Depends(verify_site_token),
):
    if node.site_code != site_code:
        raise HTTPException(status_code=403, detail="Site code mismatch")

    cam_q = select(Camera).join(NvrCameraMap).where(NvrCameraMap.nvr_node_id == node.id)
    cameras = await db.scalars(cam_q)

    cam_configs = [
        CameraConfigOut(
            cam_id=c.cam_id,
            cam_ip=c.cam_ip,
            cam_port=c.cam_port,
            onvif_port=c.onvif_port,
            rtsp_url=c.rtsp_url,
            onvif_username=c.onvif_username,
            onvif_password=c.onvif_password,
            motion_active=c.motion_active,
            retention_days=c.retention_days,
        )
        for c in cameras
    ]

    return FleetConfigOut(
        site_code=site_code,
        kong_jwt_secret=settings.kong_jwt_secret,
        cameras=cam_configs,
    )


@router.post("/{site_code}/backup-clip")
async def upload_backup_clip(
    site_code: str,
    clip: BackupClipIn,
    db: AsyncSession = Depends(get_db),
    node: NvrNode = Depends(verify_site_token),
):
    if node.site_code != site_code:
        raise HTTPException(status_code=403, detail="Site code mismatch")

    camera = await db.scalar(select(Camera).where(Camera.cam_id == clip.cam_id))
    backup = BackupClip(
        nvr_node_id=node.id,
        camera_id=camera.id if camera else None,
        object_key=clip.object_key,
        reason=clip.reason,
        captured_at=clip.captured_at,
    )
    db.add(backup)
    await db.commit()
    return {"status": "ok"}
