from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MotionEventOut(BaseModel):
    id:           int
    camera_id:    int
    motion_start: datetime
    motion_end:   Optional[datetime]
    is_active:    bool
    created_at:   datetime

    model_config = {"from_attributes": True}


class EdgeMotionIn(BaseModel):
    site_code: str
    cam_id: str
    motion_start: datetime
    motion_end: Optional[datetime] = None
    is_active: bool = True