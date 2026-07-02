from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class CameraCreate(BaseModel):
    cam_id:         str = Field(..., example="cam_001")
    cam_name:       Optional[str] = None
    cam_ip:         str
    cam_port:       int = 554
    onvif_port:     int = 80
    rtsp_url:       Optional[str] = None
    onvif_username: str = "admin"
    onvif_password: str = "admin"
    customer_id:    Optional[int] = None
    customer_site_id: Optional[int] = None
    organization_id: Optional[int] = None
    circle_id:      Optional[int] = None
    ba_id:          Optional[int] = None
    camera_model:   Optional[str] = None
    manufacturer:   Optional[str] = None
    motion_active:  bool = True

class CameraUpdate(BaseModel):
    cam_name:       Optional[str] = None
    cam_ip:         Optional[str] = None
    cam_port:       Optional[int] = None
    rtsp_url:       Optional[str] = None
    customer_id:    Optional[int] = None
    customer_site_id: Optional[int] = None
    organization_id: Optional[int] = None
    circle_id:      Optional[int] = None
    ba_id:          Optional[int] = None
    camera_model:   Optional[str] = None
    manufacturer:   Optional[str] = None
    motion_active:  Optional[bool] = None
    is_active:      Optional[bool] = None

class CameraOut(BaseModel):
    id:           int
    cam_id:       str
    cam_name:     Optional[str]
    cam_ip:       str
    customer_id:    Optional[int]
    customer_site_id: Optional[int]
    organization_id: Optional[int]
    circle_id:      Optional[int]
    ba_id:          Optional[int]
    camera_model:   Optional[str]
    manufacturer:   Optional[str]
    is_active:    bool
    is_online:    bool
    motion_active: bool
    last_seen:    Optional[datetime]
    created_at:   datetime

    class Config:
        from_attributes = True