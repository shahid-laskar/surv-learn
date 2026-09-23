"""
ai-platform/schemas/events.py
Canonical Versioned AI Perception Event Schemas.
Conforms strictly to SARVANETRA AI Event Contract v1.0 (Section 39).
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict


class BaseAiEvent(BaseModel):
    """Universal envelope for all AI events streamed to Kafka."""
    model_config = ConfigDict(extra="ignore")

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    event_version: str = "1.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    camera_id: str
    site_id: Optional[int] = 1
    model_name: str
    model_version: str = "1.0"
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    source: str = "ai-worker"
    evidence_references: Dict[str, Any] = Field(default_factory=dict)
    payload: Dict[str, Any] = Field(default_factory=dict)


# ── Specific Payload Schemas ──────────────────────────────────────────────────

class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class ObjectDetectionPayload(BaseModel):
    track_id: Optional[int] = None
    class_name: str
    confidence: float
    bbox: BoundingBox


class SpatialRuleEventPayload(BaseModel):
    rule_type: str  # "intrusion", "line_crossing", "loitering"
    zone_id: str
    track_id: int
    object_class: str
    confidence: float
    dwell_time_seconds: Optional[float] = None
    direction: Optional[str] = None  # e.g., "A_TO_B", "ENTRY", "EXIT"
    bbox: Optional[BoundingBox] = None


class AnprEventPayload(BaseModel):
    plate: str
    normalized_plate: str
    confidence: float
    vehicle_type: Optional[str] = "CAR"
    vehicle_color: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    speed_kmh: Optional[float] = None
    direction: Optional[str] = None
    snapshot_key: Optional[str] = None
    video_reference: Optional[str] = None


class PeopleCountingPayload(BaseModel):
    gate_id: str
    direction: str  # "IN", "OUT", "BIDIRECTIONAL"
    count_increment: int = 1
    total_in: int = 0
    total_out: int = 0
    current_occupancy: int = 0


class CrowdDensityPayload(BaseModel):
    zone_id: str
    estimated_count: int
    persons_per_square_meter: float
    congestion_level: str  # "NORMAL", "MODERATE", "HIGH", "CRITICAL"
    density_map_reference: Optional[str] = None


class QueueAnalyticsPayload(BaseModel):
    queue_id: str
    queue_length: int
    estimated_wait_time_seconds: float
    service_rate_per_minute: Optional[float] = None
    congestion_risk: str = "LOW"


class FallDetectionPayload(BaseModel):
    track_id: int
    confidence: float
    body_orientation: str  # "HORIZONTAL", "PRONE", "COLLAPSED"
    duration_on_ground_seconds: float
    bbox: BoundingBox


class FaceMatchPayload(BaseModel):
    candidate_id: str
    person_name: str
    category: str  # "MISSING_PERSON", "WANTED", "VIP", "STAFF"
    match_similarity: float
    gallery_id: str
    last_seen_camera_id: str
    face_snapshot_key: Optional[str] = None
