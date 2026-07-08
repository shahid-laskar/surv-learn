from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class CameraConfigOut(BaseModel):
    cam_id: str
    cam_ip: str
    cam_port: int
    onvif_port: Optional[int] = None
    rtsp_url: Optional[str] = None
    onvif_username: Optional[str] = None
    onvif_password: Optional[str] = None
    motion_active: bool
    retention_days: Optional[int] = None
    
    model_config = {"from_attributes": True}


class NvrNodeBase(BaseModel):
    site_code: str
    hardware_label: Optional[str] = None


class NvrProvisionRequest(NvrNodeBase):
    customer_site_id: int


class NvrNodeOut(NvrNodeBase):
    id: int
    customer_site_id: Optional[int] = None
    overlay_ip: Optional[str] = None
    wg_node_key: Optional[str] = None
    agent_version: Optional[str] = None
    last_heartbeat: Optional[datetime] = None
    disk_used_pct: Optional[float] = None
    is_provisioned: bool
    created_at: datetime
    
    camera_count: Optional[int] = 0

    model_config = {"from_attributes": True}


class HeartbeatIn(BaseModel):
    site_code: str
    agent_version: str
    disk_used_pct: float
    uptime_seconds: Optional[int] = None
    online_cameras: List[str]  # cam_ids


class FleetConfigOut(BaseModel):
    site_code: str
    kong_jwt_secret: str
    cameras: List[CameraConfigOut]


class BackupClipIn(BaseModel):
    cam_id: str
    reason: str
    captured_at: datetime
    object_key: str
