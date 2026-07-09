import asyncio
import logging
import os

import httpx

from edge_db import list_camera_configs, update_online_state

log = logging.getLogger("status_loop")

MEDIAMTX_API_URL = os.environ.get("MEDIAMTX_API_URL", "http://mediamtx:9997")


async def status_loop() -> None:
    while True:
        try:
            cameras = list_camera_configs()
            expected = {c["cam_id"] for c in cameras}

            ready: set[str] = set()
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{MEDIAMTX_API_URL}/v3/paths/list", timeout=5
                )
                if resp.status_code == 200:
                    for item in resp.json().get("items", []):
                        if item.get("ready"):
                            ready.add(item["name"])

            for cam_id in expected:
                is_online = cam_id in ready
                if update_online_state(cam_id, is_online):
                    log.info("Camera %s -> %s", cam_id, "online" if is_online else "offline")

        except Exception as e:
            log.error("Status loop error: %s", e)

        await asyncio.sleep(15)
