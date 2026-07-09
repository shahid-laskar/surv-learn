import asyncio
import logging
import os
import httpx

log = logging.getLogger("config_sync")

MEDIAMTX_API_URL = os.environ.get("MEDIAMTX_API_URL", "http://mediamtx-edge:9997")


async def _get_mediamtx_paths(client: httpx.AsyncClient) -> set[str]:
    """Return the set of path names currently configured in MediaMTX."""
    try:
        resp = await client.get(f"{MEDIAMTX_API_URL}/v3/config/paths/list", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        # Response: {"items": [{"name": "path-name", ...}, ...]}
        items = data.get("items", [])
        return {item["name"] for item in items if "name" in item}
    except Exception as e:
        log.warning(f"Could not list MediaMTX paths: {e}")
        return set()


async def _add_mediamtx_path(client: httpx.AsyncClient, cam_id: str) -> bool:
    """
    Register a single RTSP publish path in MediaMTX via the v3 config API.
    Uses /v3/config/paths/add/{name} — adds without touching other paths.
    Path config inherits pathDefaults (record: true, etc.) from mediamtx.yml.
    """
    url = f"{MEDIAMTX_API_URL}/v3/config/paths/add/{cam_id}"
    try:
        resp = await client.post(url, json={}, timeout=5)
        if resp.status_code in (200, 201):
            log.info(f"  ✓ MediaMTX path added: {cam_id}")
            return True
        elif resp.status_code == 400 and "already exists" in (resp.text or ""):
            log.debug(f"  ~ MediaMTX path already exists: {cam_id}")
            return True
        else:
            log.warning(f"  ✗ MediaMTX path add failed for {cam_id}: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        log.warning(f"  ✗ MediaMTX path add error for {cam_id}: {e}")
        return False


async def _remove_mediamtx_path(client: httpx.AsyncClient, cam_id: str) -> None:
    """Remove a path from MediaMTX that is no longer in the hub config."""
    url = f"{MEDIAMTX_API_URL}/v3/config/paths/delete/{cam_id}"
    try:
        resp = await client.delete(url, timeout=5)
        if resp.status_code in (200, 204):
            log.info(f"  ✓ MediaMTX path removed: {cam_id} (no longer in hub config)")
        else:
            log.debug(f"  ~ MediaMTX path remove: {cam_id} → {resp.status_code}")
    except Exception as e:
        log.warning(f"  ✗ MediaMTX path remove error for {cam_id}: {e}")


async def _sync_mediamtx_paths(cameras: list[dict]) -> None:
    """
    Reconcile MediaMTX configured paths against the hub camera list.
    - Adds paths for cameras in hub config that MediaMTX doesn't know about.
    - Removes stale paths for cameras no longer in hub config (cam_id starts with
      'SIMCAM-' or matches our site code pattern to avoid removing manual paths).
    """
    if not cameras:
        log.debug("No cameras in hub config — skipping MediaMTX path sync.")
        return

    hub_cam_ids = {c["cam_id"] for c in cameras}
    site_code = os.environ.get("SITE_CODE", "")

    async with httpx.AsyncClient() as client:
        current_paths = await _get_mediamtx_paths(client)

        # Add missing paths
        added = 0
        for cam_id in hub_cam_ids:
            if cam_id not in current_paths:
                ok = await _add_mediamtx_path(client, cam_id)
                if ok:
                    added += 1

        # Remove paths that belong to this site but are no longer in hub config
        # Only remove paths that look like camera IDs for this site (safe guard)
        stale = {
            p for p in current_paths
            if p not in hub_cam_ids
            and site_code
            and site_code in p
        }
        for cam_id in stale:
            await _remove_mediamtx_path(client, cam_id)

        if added or stale:
            log.info(f"MediaMTX path sync: +{added} added, -{len(stale)} removed")
        else:
            log.debug("MediaMTX paths already in sync.")


async def config_sync_loop(site_code: str, hub_url: str):
    while True:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{hub_url}/fleet/{site_code}/config",
                    timeout=10
                )
                resp.raise_for_status()
                data = resp.json()

            cameras = data.get("cameras", [])
            log.info(f"Config sync: {len(cameras)} cameras from hub for {site_code}")

            # Register/reconcile MediaMTX RTSP paths for each camera
            await _sync_mediamtx_paths(cameras)

            # Store kong_jwt_secret for stream validation (future: write to local auth)
            jwt_secret = data.get("kong_jwt_secret")
            if jwt_secret:
                log.debug("Received JWT secret for edge stream validation.")

        except httpx.HTTPStatusError as e:
            log.error(f"Config sync HTTP error: {e.response.status_code} {e.response.text[:200]}")
        except Exception as e:
            log.error(f"Config sync failed: {e}")

        await asyncio.sleep(300)  # Sync every 5 minutes
