import asyncio
import logging
import os

import httpx

from edge_db import upsert_camera_configs, set_meta
from hub_client import hub_get
from rtsp_util import build_rtsp_source

log = logging.getLogger("config_sync")

MEDIAMTX_API_URL = os.environ.get("MEDIAMTX_API_URL", "http://mediamtx:9997")


async def _get_mediamtx_paths(client: httpx.AsyncClient) -> set[str]:
    try:
        resp = await client.get(f"{MEDIAMTX_API_URL}/v3/config/paths/list", timeout=5)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        return {item["name"] for item in items if "name" in item}
    except Exception as e:
        log.warning("Could not list MediaMTX paths: %s", e)
        return set()


async def _add_mediamtx_path(
    client: httpx.AsyncClient, cam_id: str, source: str | None
) -> bool:
    url = f"{MEDIAMTX_API_URL}/v3/config/paths/add/{cam_id}"
    body: dict = {}
    if source:
        body["source"] = source
    try:
        resp = await client.post(url, json=body, timeout=10)
        if resp.status_code in (200, 201):
            log.info("MediaMTX path added: %s source=%s", cam_id, bool(source))
            return True
        if resp.status_code == 400 and "already exists" in (resp.text or ""):
            # Update source on existing path
            patch_url = f"{MEDIAMTX_API_URL}/v3/config/paths/patch/{cam_id}"
            if source:
                await client.patch(patch_url, json={"source": source}, timeout=10)
            return True
        log.warning(
            "MediaMTX path add failed %s: %s %s",
            cam_id,
            resp.status_code,
            resp.text[:200],
        )
        return False
    except Exception as e:
        log.warning("MediaMTX path add error %s: %s", cam_id, e)
        return False


async def _remove_mediamtx_path(client: httpx.AsyncClient, cam_id: str) -> None:
    url = f"{MEDIAMTX_API_URL}/v3/config/paths/delete/{cam_id}"
    try:
        resp = await client.delete(url, timeout=5)
        if resp.status_code in (200, 204):
            log.info("MediaMTX path removed: %s", cam_id)
    except Exception as e:
        log.warning("MediaMTX path remove error %s: %s", cam_id, e)


async def _sync_mediamtx_paths(cameras: list[dict]) -> None:
    if not cameras:
        return

    hub_cam_ids = {c["cam_id"] for c in cameras}
    site_code = os.environ.get("SITE_CODE", "")

    async with httpx.AsyncClient() as client:
        current_paths = await _get_mediamtx_paths(client)
        added = 0
        for cam in cameras:
            cam_id = cam["cam_id"]
            source = build_rtsp_source(cam)
            if cam_id not in current_paths:
                if await _add_mediamtx_path(client, cam_id, source):
                    added += 1
            elif source:
                patch_url = f"{MEDIAMTX_API_URL}/v3/config/paths/patch/{cam_id}"
                try:
                    await client.patch(
                        patch_url, json={"source": source}, timeout=10
                    )
                except Exception as e:
                    log.debug("Path patch %s: %s", cam_id, e)

        stale = {
            p
            for p in current_paths
            if p not in hub_cam_ids and site_code and site_code in p
        }
        for cam_id in stale:
            await _remove_mediamtx_path(client, cam_id)

        if added or stale:
            log.info("MediaMTX sync: +%s -%s", added, len(stale))


async def config_sync_loop(site_code: str, hub_url: str) -> None:
    while True:
        try:
            async with httpx.AsyncClient() as client:
                data = await hub_get(client, f"{hub_url}/fleet/{site_code}/config")

            cameras = data.get("cameras", [])
            log.info("Config sync: %d cameras for %s", len(cameras), site_code)

            upsert_camera_configs(cameras)
            await _sync_mediamtx_paths(cameras)

            jwt_secret = data.get("kong_jwt_secret")
            if jwt_secret:
                set_meta("kong_jwt_secret", jwt_secret)

        except httpx.HTTPStatusError as e:
            log.error(
                "Config sync HTTP %s: %s",
                e.response.status_code,
                e.response.text[:200],
            )
        except Exception as e:
            log.error("Config sync failed: %s", e)

        await asyncio.sleep(300)
