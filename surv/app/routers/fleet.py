from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies.auth import get_current_user, require_permission, CurrentUser
from app.models.nvr import NvrNode, NvrCameraMap, BackupClip
from app.models.camera import Camera
from app.schemas.fleet import (
    NvrNodeOut, HeartbeatIn, FleetConfigOut, BackupClipIn, NvrProvisionRequest, CameraConfigOut
)
from app.config import settings
import secrets

router = APIRouter(prefix="/fleet", tags=["fleet"])


@router.get("/", response_model=List[NvrNodeOut])
async def list_nvrs(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: list all NVR nodes."""
    if "SUPER_ADMIN" not in user.roles and "system.settings" not in user.permissions:
        raise HTTPException(status_code=403, detail="Not authorized")

    q = select(NvrNode).order_by(NvrNode.created_at.desc())
    result = await db.execute(q)
    nodes = result.scalars().all()

    # Get camera counts
    out = []
    for node in nodes:
        count_q = select(func.count(NvrCameraMap.camera_id)).where(NvrCameraMap.nvr_node_id == node.id)
        count = await db.scalar(count_q)
        node_dict = node.__dict__.copy()
        node_dict["camera_count"] = count or 0
        out.append(NvrNodeOut(**node_dict))
    
    return out


@router.post("/", response_model=NvrNodeOut)
async def provision_nvr(
    req: NvrProvisionRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: provision new NVR."""
    if "SUPER_ADMIN" not in user.roles and "system.settings" not in user.permissions:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Generate a random wg_node_key mock since Headscale is not fully integrated in Phase 12 alone
    new_node = NvrNode(
        site_code=req.site_code,
        customer_site_id=req.customer_site_id,
        hardware_label=req.hardware_label,
        wg_node_key=secrets.token_hex(16),
        is_provisioned=False
    )
    db.add(new_node)
    try:
        await db.commit()
        await db.refresh(new_node)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
    node_dict = new_node.__dict__.copy()
    node_dict["camera_count"] = 0
    return NvrNodeOut(**node_dict)


@router.get("/{site_code}", response_model=NvrNodeOut)
async def get_nvr(
    site_code: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: NVR detail."""
    q = select(NvrNode).where(NvrNode.site_code == site_code)
    node = await db.scalar(q)
    if not node:
        raise HTTPException(status_code=404, detail="NVR not found")
        
    count_q = select(func.count(NvrCameraMap.camera_id)).where(NvrCameraMap.nvr_node_id == node.id)
    count = await db.scalar(count_q)
    
    node_dict = node.__dict__.copy()
    node_dict["camera_count"] = count or 0
    return NvrNodeOut(**node_dict)


@router.delete("/{site_code}", status_code=status.HTTP_204_NO_CONTENT)
async def decommission_nvr(
    site_code: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: decommission NVR."""
    if "SUPER_ADMIN" not in user.roles and "system.settings" not in user.permissions:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    q = select(NvrNode).where(NvrNode.site_code == site_code)
    node = await db.scalar(q)
    if not node:
        raise HTTPException(status_code=404, detail="NVR not found")
        
    await db.delete(node)
    await db.commit()
    return


# --- Edge Agent Endpoints (In a real system, these would authenticate via WireGuard IP or mTLS) ---

@router.post("/heartbeat")
async def heartbeat(
    hb: HeartbeatIn,
    db: AsyncSession = Depends(get_db)
):
    """edge-agent calls every 30s"""
    q = select(NvrNode).where(NvrNode.site_code == hb.site_code)
    node = await db.scalar(q)
    if not node:
        # Auto-register if not exists (Zero-touch provisioning)
        node = NvrNode(site_code=hb.site_code)
        db.add(node)
    
    node.agent_version = hb.agent_version
    node.disk_used_pct = hb.disk_used_pct
    node.last_heartbeat = datetime.now(timezone.utc)
    node.is_provisioned = True
    
    # Sync camera online states
    if node.id is not None:
        from sqlalchemy import update
        from app.models.camera import Camera
        from app.models.nvr import NvrCameraMap
        
        now = datetime.now(timezone.utc)
        
        # Set online cameras
        if hb.online_cameras:
            await db.execute(
                update(Camera)
                .where(Camera.cam_id.in_(hb.online_cameras))
                .where(Camera.id.in_(
                    select(NvrCameraMap.camera_id).where(NvrCameraMap.nvr_node_id == node.id)
                ))
                .values(is_online=True, last_seen=now)
            )
        
        # Set offline cameras
        await db.execute(
            update(Camera)
            .where(~Camera.cam_id.in_(hb.online_cameras))
            .where(Camera.id.in_(
                select(NvrCameraMap.camera_id).where(NvrCameraMap.nvr_node_id == node.id)
            ))
            .values(is_online=False)
        )
    await db.commit()
    return {"status": "ok"}


@router.get("/{site_code}/config", response_model=FleetConfigOut)
async def get_config(
    site_code: str,
    db: AsyncSession = Depends(get_db)
):
    """edge-agent pulls camera list + retention"""
    q = select(NvrNode).where(NvrNode.site_code == site_code)
    node = await db.scalar(q)
    if not node:
        raise HTTPException(status_code=404, detail="NVR not found")
        
    # Get cameras mapped to this NVR
    cam_q = select(Camera).join(NvrCameraMap).where(NvrCameraMap.nvr_node_id == node.id)
    cameras = await db.scalars(cam_q)
    
    cam_configs = []
    for c in cameras:
        cam_configs.append(CameraConfigOut(
            cam_id=c.cam_id,
            cam_ip=c.cam_ip,
            cam_port=c.cam_port,
            onvif_port=c.onvif_port,
            rtsp_url=c.rtsp_url,
            onvif_username=c.onvif_username,
            onvif_password=c.onvif_password,
            motion_active=c.motion_active,
            retention_days=c.retention_days
        ))
        
    return FleetConfigOut(
        site_code=site_code,
        kong_jwt_secret=settings.kong_jwt_secret,  # Sent encrypted via WireGuard
        cameras=cam_configs
    )


@router.post("/{site_code}/backup-clip")
async def upload_backup_clip(
    site_code: str,
    clip: BackupClipIn,
    db: AsyncSession = Depends(get_db)
):
    """edge-agent uploads critical clips"""
    q = select(NvrNode).where(NvrNode.site_code == site_code)
    node = await db.scalar(q)
    if not node:
        raise HTTPException(status_code=404, detail="NVR not found")
        
    cam_q = select(Camera).where(Camera.cam_id == clip.cam_id)
    camera = await db.scalar(cam_q)
    
    backup = BackupClip(
        nvr_node_id=node.id,
        camera_id=camera.id if camera else None,
        object_key=clip.object_key,
        reason=clip.reason,
        captured_at=clip.captured_at
    )
    db.add(backup)
    await db.commit()
    return {"status": "ok"}
