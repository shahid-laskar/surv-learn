import asyncio
import logging
import httpx
import os
import shutil

log = logging.getLogger("heartbeat")

async def heartbeat_loop(site_code: str, hub_url: str):
    agent_version = "1.0.0"
    while True:
        try:
            total, used, free = shutil.disk_usage("/")
            disk_used_pct = round((used / total) * 100, 2)
            
            online_cameras = []
            MEDIAMTX_API_URL = os.environ.get("MEDIAMTX_API_URL", "http://mediamtx-edge:9997")
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"{MEDIAMTX_API_URL}/v3/paths/list", timeout=5)
                    if resp.status_code == 200:
                        items = resp.json().get("items", [])
                        online_cameras = [item["name"] for item in items if item.get("ready")]
            except Exception as e:
                log.warning(f"Could not check online cameras from MediaMTX: {e}")

            payload = {
                "site_code": site_code,
                "agent_version": agent_version,
                "disk_used_pct": disk_used_pct,
                "uptime_seconds": 0, # Placeholder
                "online_cameras": online_cameras
            }
            
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{hub_url}/fleet/heartbeat", json=payload, timeout=10)
                resp.raise_for_status()
                
            log.info(f"Heartbeat sent successfully (Disk: {disk_used_pct}%)")
        except Exception as e:
            log.error(f"Failed to send heartbeat: {e}")
            
        await asyncio.sleep(30)
