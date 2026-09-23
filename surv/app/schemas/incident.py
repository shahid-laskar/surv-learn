"""
app/schemas/incident.py
Pydantic v2 schemas for ICCC Incident Management & State Transition Auditing.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class IncidentCreate(BaseModel):
    title:               str = Field(..., min_length=3, max_length=255, json_schema_extra={"example": "Wanted Vehicle Interception at Nilakkal Ground 1"})
    description:         Optional[str] = Field(None, json_schema_extra={"example": "ANPR alert triggered for stolen cash van KL07BH9999"})
    severity:            str = Field("MEDIUM", json_schema_extra={"example": "HIGH"})
    source_type:         str = Field("manual", json_schema_extra={"example": "anpr_alert"})
    source_id:           Optional[int] = None
    camera_id:           Optional[int] = None
    customer_site_id:    Optional[int] = None
    assigned_to_user_id: Optional[int] = None


class IncidentUpdate(BaseModel):
    title:               Optional[str] = None
    description:         Optional[str] = None
    severity:            Optional[str] = None
    assigned_to_user_id: Optional[int] = None


class IncidentTransitionIn(BaseModel):
    to_status: str = Field(..., json_schema_extra={"example": "ASSIGNED"})
    notes:     Optional[str] = Field(None, json_schema_extra={"example": "Patrol dispatched to intercept vehicle"})


class IncidentTimelineOut(BaseModel):
    id:                 int
    incident_id:        int
    from_status:        Optional[str]
    to_status:          str
    changed_by_user_id: Optional[int]
    notes:              Optional[str]
    created_at:         datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentOut(BaseModel):
    id:                  int
    incident_number:     str
    title:               str
    description:         Optional[str]
    status:              str
    severity:            str
    source_type:         str
    source_id:           Optional[int]
    camera_id:           Optional[int]
    customer_site_id:    Optional[int]
    assigned_to_user_id: Optional[int]
    created_by_user_id:  Optional[int]
    evidence_package_id: Optional[int]
    created_at:          datetime
    updated_at:          datetime
    timeline:            List[IncidentTimelineOut] = []

    model_config = ConfigDict(from_attributes=True)
