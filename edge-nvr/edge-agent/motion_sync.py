import asyncio
import logging
import os

import httpx

from edge_db import fetch_unsynced_motion_events, mark_motion_synced, init_db
from hub_client import hub_post

log = logging.getLogger("motion_sync")

HUB_API_URL = os.environ.get("HUB_API_URL", "")


async def motion_sync_loop(site_code: str, hub_url: str) -> None:
    init_db()
    while True:
        try:
            events = fetch_unsynced_motion_events()
            if not events:
                await asyncio.sleep(15)
                continue

            async with httpx.AsyncClient() as client:
                for ev in events:
                    payload = {
                        "site_code": site_code,
                        "cam_id": ev["cam_id"],
                        "motion_start": ev["motion_start"],
                        "motion_end": ev["motion_end"],
                        "is_active": bool(ev["is_active"]),
                    }
                    try:
                        await hub_post(client, f"{hub_url}/motion/edge", payload)
                        mark_motion_synced(int(ev["id"]))
                    except Exception as e:
                        log.warning("Motion sync failed id=%s: %s", ev["id"], e)
        except Exception as e:
            log.error("Motion sync loop error: %s", e)

        await asyncio.sleep(15)
