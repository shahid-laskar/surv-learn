import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

from edge_db import get_retention_by_cam

log = logging.getLogger("local_retention")

RECORDINGS_DIR = Path(os.environ.get("RECORDINGS_DIR", "/recordings"))
INTERVAL_SEC = int(os.environ.get("RETENTION_INTERVAL_SEC", "3600"))


def _cleanup_once() -> int:
    retention_map = get_retention_by_cam()
    if not retention_map:
        return 0

    deleted = 0
    now = datetime.now(timezone.utc)

    for cam_id, days in retention_map.items():
        cam_dir = RECORDINGS_DIR / cam_id
        if not cam_dir.is_dir():
            continue
        cutoff = now - timedelta(days=max(int(days), 1))
        for f in cam_dir.rglob("*"):
            if not f.is_file():
                continue
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                try:
                    f.unlink()
                    deleted += 1
                except OSError as e:
                    log.warning("Could not delete %s: %s", f, e)

    if deleted:
        log.info("Retention cleanup removed %d file(s)", deleted)
    return deleted


async def retention_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(_cleanup_once)
        except Exception as e:
            log.error("Retention loop error: %s", e)
        await asyncio.sleep(INTERVAL_SEC)
