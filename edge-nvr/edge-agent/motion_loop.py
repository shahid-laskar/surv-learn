import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from edge_db import (
    close_motion_event,
    insert_motion_event,
    list_camera_configs,
    queue_backup,
)
from onvif_motion import OnvifMotionManager

log = logging.getLogger("motion_loop")

RECORDINGS_DIR = Path(__import__("os").environ.get("RECORDINGS_DIR", "/recordings"))
BACKUP_ENABLED = __import__("os").environ.get("BACKUP_ENABLED", "true").lower() == "true"
BACKUP_TRIGGER = __import__("os").environ.get("BACKUP_TRIGGER", "motion")


def _latest_recording(cam_id: str) -> Path | None:
    base = RECORDINGS_DIR / cam_id
    if not base.is_dir():
        return None
    files = sorted(base.rglob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        files = sorted(base.rglob("*.fmp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def _on_motion_start(cam_id: str, when: datetime) -> None:
    insert_motion_event(cam_id, when, is_active=True)
    log.info("Motion start: %s", cam_id)
    if BACKUP_ENABLED and BACKUP_TRIGGER in ("motion", "all"):
        clip = _latest_recording(cam_id)
        if clip:
            queue_backup(cam_id, str(clip), "motion", when)


def _on_motion_end(cam_id: str, when: datetime) -> None:
    close_motion_event(cam_id, when)
    log.info("Motion end: %s", cam_id)


_manager = OnvifMotionManager(_on_motion_start, _on_motion_end)


async def motion_loop() -> None:
    while True:
        try:
            cameras = list_camera_configs()
            _manager.sync_cameras(cameras)
        except Exception as e:
            log.error("Motion loop error: %s", e)
        await asyncio.sleep(60)
