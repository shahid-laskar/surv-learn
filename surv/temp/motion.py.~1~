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

    class Config:
        from_attributes = True