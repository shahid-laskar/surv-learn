"""
app/schemas/health.py
Pydantic response schemas for the health monitoring endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class CameraHealthOut(BaseModel):
    """Per-camera health summary for the dashboard."""
    camera_id:       str
    name:            Optional[str]
    is_online:       bool
    last_seen:       Optional[datetime]
    offline_minutes: Optional[int]    # None if online; minutes since last_seen if offline
    uptime_pct_24h:  Optional[float]  # 0–100, computed from status_log; None if no history

    model_config = {"from_attributes": True}


class StatusLogEntry(BaseModel):
    """One row from camera_status_log — a single status period."""
    id:               int
    status:           str         # 'online' | 'offline'
    changed_at:       datetime
    duration_seconds: Optional[int]  # None for the current (open) period

    model_config = {"from_attributes": True}


class StorageBucketStats(BaseModel):
    """Storage statistics for a single MinIO bucket."""
    bucket:        str
    total_size_gb: float
    object_count:  int
    oldest_object: Optional[str]  # ISO datetime string or None


class StorageStats(BaseModel):
    """Full storage health payload."""
    buckets:          List[StorageBucketStats]
    recordings_dir_gb: Optional[float]  # disk usage of the local bind-mount /recordings
    checked_at:       datetime


class WorkerHealthOut(BaseModel):
    """Connectivity checks for dependent services."""
    kafka:   str   # 'healthy' | 'unreachable'
    minio:   str
    mediamtx: str
    postgres: str


class HealthSummaryOut(BaseModel):
    """Top-level health aggregate returned by GET /health/summary."""
    total_cameras:    int
    online_cameras:   int
    offline_cameras:  int
    active_motion:    int
    worker_health:    WorkerHealthOut
    checked_at:       datetime
