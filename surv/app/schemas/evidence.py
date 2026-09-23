"""
app/schemas/evidence.py
Pydantic v2 schemas for Tamper-Evident Evidence Package Creation & Cryptographic Verification.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EvidenceExportRequest(BaseModel):
    title:            str = Field(..., min_length=3, max_length=255, json_schema_extra={"example": "Nilakkal Entry ANPR Incident Clip"})
    description:      Optional[str] = Field(None, json_schema_extra={"example": "Exported for Kerala Police Pathanamthitta court proceedings"})
    incident_id:      Optional[int] = None
    camera_id:        Optional[int] = None
    customer_site_id: Optional[int] = None
    # Source clip keys or filesystem paths
    clip_files:       List[str] = Field(default_factory=list, json_schema_extra={"example": ["recordings/2026/09/23/cam01_1000.mp4"]})
    snapshot_files:   List[str] = Field(default_factory=list, json_schema_extra={"example": ["snapshots/anpr/KL07BH9999.jpg"]})


class EvidenceVerificationResult(BaseModel):
    package_number:           str
    is_valid:                 bool
    file_count:               int
    calculated_manifest_hash: str
    stored_manifest_hash:     str
    mismatched_files:         List[str] = []
    tamper_detected:          bool
    verified_at:              datetime


class EvidencePackageOut(BaseModel):
    id:                  int
    package_number:      str
    title:               str
    description:         Optional[str]
    incident_id:         Optional[int]
    camera_id:           Optional[int]
    customer_site_id:    Optional[int]
    file_path:           str
    sha256_hash:         str
    file_size_bytes:     int
    exported_by_user_id: Optional[int]
    is_sealed:           bool
    created_at:          datetime

    model_config = ConfigDict(from_attributes=True)
