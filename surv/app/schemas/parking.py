"""
app/schemas/parking.py
Pydantic v2 validation models for Parking Management System.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ParkingZoneCreate(BaseModel):
    zone_code:        str = Field(..., json_schema_extra={"example": "G01"})
    name:             str = Field(..., json_schema_extra={"example": "Nilakkal Ground 1 - KSRTC"})
    customer_site_id: Optional[int] = None
    vehicle_type:     str = Field("ALL", json_schema_extra={"example": "BUS"})
    total_capacity:   int = Field(100, ge=1)
    display_order:    int = 0


class ParkingZoneUpdate(BaseModel):
    name:              Optional[str] = None
    vehicle_type:      Optional[str] = None
    total_capacity:    Optional[int] = Field(None, ge=1)
    current_occupancy: Optional[int] = Field(None, ge=0)
    is_active:         Optional[bool] = None
    display_order:     Optional[int] = None


class ParkingZoneOut(BaseModel):
    id:                int
    customer_site_id:  Optional[int]
    zone_code:         str
    name:              str
    vehicle_type:      str
    total_capacity:    int
    current_occupancy: int
    available_slots:   int
    occupancy_pct:     float
    is_active:         bool
    display_order:     int
    created_at:        datetime
    updated_at:        datetime

    model_config = ConfigDict(from_attributes=True)


class ParkingOccupancySummary(BaseModel):
    total_zones:       int
    total_capacity:    int
    total_occupied:    int
    total_available:   int
    overall_occupancy_pct: float
    zones:             List[ParkingZoneOut]


class ParkingEntryRequest(BaseModel):
    vehicle_number:    str = Field(..., json_schema_extra={"example": "KL01AB1234"})
    customer_site_id:  Optional[int] = None
    lane_id:           Optional[int] = None
    vehicle_type:      str = Field("LMV", json_schema_extra={"example": "LMV"})
    preferred_zone_id: Optional[int] = None
    anpr_transaction_id: Optional[int] = None


class ParkingExitRequest(BaseModel):
    vehicle_number:    Optional[str] = None
    entry_slip_number: Optional[str] = None
    customer_site_id:  Optional[int] = None
    exit_lane_id:      Optional[int] = None


class ParkingSlipOut(BaseModel):
    session_id:        int
    slip_number:       str
    vehicle_number:    str
    vehicle_type:      str
    zone_code:         str
    zone_name:         str
    entry_time:        datetime
    exit_time:         Optional[datetime] = None
    duration_minutes:  Optional[int] = None
    status:            str
    fee_amount:        float = 0.0

    model_config = ConfigDict(from_attributes=True)
