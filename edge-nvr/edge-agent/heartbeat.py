import asyncio
import logging
import os
import shutil

import httpx

from hub_client import hub_post
from edge_db import init_db

log = logging.getLogger("heartbeat")

MEDIAMTX_API_URL = os.environ.get("MEDIAMTX_API_URL", "http://mediamtx:9997")
AGENT_VERSION = "1.1.0"


async def _overlay_ip() -> str | None:
    """Read Tailscale IPv4 when VPN profile is running (best-effort)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "tailscale", "ip", "-4",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0 and stdout:
            return stdout.decode().strip().split("\n")[0] or None
    except FileNotFoundError:
        pass
    return None


async def heartbeat_loop(site_code: str, hub_url: str) -> None:
    init_db()
    while True:
        try:
            total, used, _free = shutil.disk_usage("/")
            disk_used_pct = round((used / total) * 100, 2)

            online_cameras: list[str] = []
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        f"{MEDIAMTX_API_URL}/v3/paths/list", timeout=5
                    )
                    if resp.status_code == 200:
                        items = resp.json().get("items", [])
                        online_cameras = [
                            item["name"] for item in items if item.get("ready")
                        ]
            except Exception as e:
                log.warning("Could not check MediaMTX paths: %s", e)

            overlay = await _overlay_ip()
            payload = {
                "site_code": site_code,
                "agent_version": AGENT_VERSION,
                "disk_used_pct": disk_used_pct,
                "uptime_seconds": 0,
                "online_cameras": online_cameras,
                "overlay_ip": overlay,
            }

            async with httpx.AsyncClient() as client:
                await hub_post(client, f"{hub_url}/fleet/heartbeat", payload)

            log.info(
                "Heartbeat OK disk=%s%% online=%s overlay=%s",
                disk_used_pct,
                len(online_cameras),
                overlay or "n/a",
            )
        except httpx.HTTPStatusError as e:
            log.error(
                "Heartbeat HTTP %s: %s",
                e.response.status_code,
                e.response.text[:200],
            )
        except Exception as e:
            log.error("Heartbeat failed: %s", e)

        await asyncio.sleep(30)
