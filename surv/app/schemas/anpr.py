"""
app/schemas/anpr.py
Pydantic v2 validation models for ANPR Management Plane, Watchlists, and Real-Time Alerts.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AnprEventIn(BaseModel):
    """
    Ingest payload for ANPR events from Edge LPUs or Hub AI pipelines.
    """
    plate:              str = Field(..., min_length=2, max_length=50, json_schema_extra={"example": "KL01AB1234"})
    confidence:         float = Field(1.0, ge=0.0, le=1.0, json_schema_extra={"example": 0.96})
    vehicle_type:       Optional[str] = Field("CAR", json_schema_extra={"example": "CAR"})
    vehicle_color:      Optional[str] = Field(None, json_schema_extra={"example": "white"})
    camera_id:          Optional[int] = Field(None, json_schema_extra={"example": 1})
    customer_site_id:   Optional[int] = Field(None, json_schema_extra={"example": 1})
    lane_id:            Optional[int] = None
    timestamp:          Optional[datetime] = None
    speed_kmh:          Optional[float] = None
    direction:          Optional[str] = Field(None, json_schema_extra={"example": "IN"})
    snapshot_key:       Optional[str] = None
    video_reference:    Optional[str] = None
    processing_source:  str = Field("edge_lpu", json_schema_extra={"example": "edge_lpu"})


class PlateCorrectionIn(BaseModel):
    """
    Manual human-in-the-loop correction of an ANPR reading.
    """
    corrected_plate:    str = Field(..., min_length=2, max_length=50)
    correction_notes:   Optional[str] = None


class AnprTransactionOut(BaseModel):
    id:                 int
    customer_site_id:   Optional[int]
    camera_id:          Optional[int]
    lane_id:            Optional[int]
    plate_number:       str
    normalized_plate:   str
    confidence:         float
    vehicle_type:       Optional[str]
    vehicle_color:      Optional[str]
    speed_kmh:          Optional[float]
    direction:          Optional[str]
    snapshot_key:       Optional[str]
    video_reference:    Optional[str]
    processing_source:  str
    is_corrected:       bool
    original_plate:     Optional[str]
    corrected_by_user_id: Optional[int]
    correction_notes:   Optional[str]
    captured_at:        datetime
    created_at:         datetime

    model_config = ConfigDict(from_attributes=True)


class WatchlistCreate(BaseModel):
    plate_number:        str = Field(..., min_length=2, max_length=50, json_schema_extra={"example": "KL07BH9999"})
    category:            str = Field("WANTED", json_schema_extra={"example": "WANTED"})
    severity:            str = Field("HIGH", json_schema_extra={"example": "HIGH"})
    reason:              str = Field(..., json_schema_extra={"example": "Vehicle involved in Sabarimala robbery incident"})
    case_number:         Optional[str] = Field(None, json_schema_extra={"example": "FIR-432/2026/PTA"})
    reporting_authority: Optional[str] = Field("Kerala Police", json_schema_extra={"example": "Kerala Police Pathanamthitta"})
    is_active:           bool = True


class WatchlistUpdate(BaseModel):
    category:            Optional[str] = None
    severity:            Optional[str] = None
    reason:              Optional[str] = None
    case_number:         Optional[str] = None
    reporting_authority: Optional[str] = None
    is_active:           Optional[bool] = None


class WatchlistOut(BaseModel):
    id:                  int
    plate_number:        str
    normalized_plate:    str
    category:            str
    severity:            str
    reason:              str
    case_number:         Optional[str]
    reporting_authority: Optional[str]
    is_active:           bool
    created_by_user_id:  Optional[int]
    created_at:          datetime
    updated_at:          datetime

    model_config = ConfigDict(from_attributes=True)


class WatchlistAlertOut(BaseModel):
    id:                      int
    watchlist_id:            int
    anpr_transaction_id:     int
    plate_number:            str
    camera_id:               Optional[int]
    customer_site_id:        Optional[int]
    severity:                str
    status:                  str
    notes:                   Optional[str]
    acknowledged_by_user_id: Optional[int]
    acknowledged_at:         Optional[datetime]
    created_at:              datetime

    model_config = ConfigDict(from_attributes=True)


class AlertAcknowledgeIn(BaseModel):
    notes: Optional[str] = Field(None, json_schema_extra={"example": "Vehicle intercepted at Nilakkal Main Gate."})
