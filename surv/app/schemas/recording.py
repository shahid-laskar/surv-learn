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

class TimelineOut(BaseModel):
    camera_id:      str
    date:           str
    total_segments: int
    segments:       List[SegmentOut]