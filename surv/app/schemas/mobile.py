from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ---- Phase 15: device registration ----

class RegisterDeviceIn(BaseModel):
    device_token: str = Field(..., max_length=500)
    platform: Literal["ios", "android"]
    device_name: str | None = Field(None, max_length=200)
    app_version: str | None = Field(None, max_length=20)


class RegisterDeviceOut(BaseModel):
    id: int
    platform: str
    is_active: bool
    created_at: datetime
    last_active: datetime

    class Config:
        from_attributes = True


# ---- Phase 15: dashboard summary ----

class CameraSummary(BaseModel):
    camera_id: int
    name: str
    is_online: bool
    last_motion_at: datetime | None = None


class DashboardSummaryOut(BaseModel):
    total_cameras: int
    online_cameras: int
    offline_cameras: int
    recent_motion_count_24h: int
    cameras: list[CameraSummary]


# ---- Phase 16: VPN session (embedded WireGuard) ----

class VpnSessionRequest(BaseModel):
    public_key: str = Field(..., description="On-device generated WireGuard public key")
    device_name: str = Field(..., max_length=200)
    platform: Literal["ios", "android"]


class VpnSessionResponse(BaseModel):
    hub_endpoint: str
    hub_public_key: str
    allowed_ips: str
    keepalive: int
    peer_ttl_hours: int
    assigned_overlay_ip: str | None = None


class VpnSessionRevoke(BaseModel):
    public_key: str