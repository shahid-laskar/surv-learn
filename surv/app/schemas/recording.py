from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class SegmentOut(BaseModel):
    segment_id:       int
    start:            datetime
    end:              Optional[datetime]
    duration_seconds: Optional[int]
    file_size_bytes:  Optional[int] = None
    playback_url:     str
    object_key:       str
    recording_type:   str = "full"   # 'full' | 'motion' | 'guard'
    has_motion:       bool = False

class TimelineOut(BaseModel):
    camera_id:      str
    date:           str
    total_segments: int
    segments:       List[SegmentOut]