import logging
import httpx
from typing import List
from urllib.parse import quote, urlparse, urlunparse

from app.config import settings
from app.models.camera import Camera

log = logging.getLogger(__name__)

# Default RTSP stream path used when rtsp_url is not set.
# The rtsp_url field should NEVER contain credentials — store only the
# bare URL (e.g. rtsp://192.168.1.10:554/stream1). Credentials are
# always taken from onvif_username / onvif_password and injected here.
_DEFAULT_RTSP_PATH = "/stream1"

class MediaMTXClient:
    def __init__(self):
        self.api_url = settings.mediamtx_api_url.rstrip("/")

    def _get_rtsp_url(self, cam: Camera) -> str:
        """
        Build the RTSP source URL for MediaMTX.

        Credentials (onvif_username / onvif_password) are ALWAYS injected
        from the DB fields and URL-encoded so special characters (e.g. '@',
        ':', '#') don't break URL parsing.

        rtsp_url (optional) should be a credential-free URL, e.g.:
            rtsp://192.168.1.10:554/stream1
        If omitted, the URL is built from cam_ip + cam_port + _DEFAULT_RTSP_PATH.
        """
        user = quote(cam.onvif_username or "", safe="")
        pwd  = quote(cam.onvif_password or "", safe="")

        if cam.rtsp_url:
            # Parse the stored URL (which must NOT contain credentials).
            # Strip any credentials the user may have accidentally included,
            # then re-inject the encoded ones from the DB.
            parsed = urlparse(cam.rtsp_url)
            # netloc without credentials: host:port (or just host)
            host = parsed.hostname or cam.cam_ip
            port = parsed.port or cam.cam_port
            path = parsed.path or _DEFAULT_RTSP_PATH
            netloc = f"{user}:{pwd}@{host}:{port}"
            return urlunparse(("rtsp", netloc, path, "", "", ""))

        # Fallback: build from DB fields
        return f"rtsp://{user}:{pwd}@{cam.cam_ip}:{cam.cam_port}{_DEFAULT_RTSP_PATH}"

    async def add_camera(self, cam: Camera):
        """Add or update a camera path in MediaMTX."""
        # Use 'replace' to dynamically add or update an existing path
        url = f"{self.api_url}/v3/config/paths/replace/{cam.cam_id}"
        payload = {
            "source": self._get_rtsp_url(cam),
            "sourceProtocol": "tcp"
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=5.0)
                if resp.status_code in (200, 204):
                    log.info(f"Successfully registered {cam.cam_id} in MediaMTX.")
                else:
                    log.warning(f"Failed to register {cam.cam_id} in MediaMTX: {resp.status_code} - {resp.text}")
        except Exception as e:
            log.error(f"Error communicating with MediaMTX for add_camera: {e}")

    async def remove_camera(self, cam_id: str):
        """Remove a camera path from MediaMTX."""
        url = f"{self.api_url}/v3/config/paths/delete/{cam_id}"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.delete(url, timeout=5.0)
                if resp.status_code in (200, 204):
                    log.info(f"Successfully removed {cam_id} from MediaMTX.")
                elif resp.status_code == 404:
                    log.info(f"Camera {cam_id} not found in MediaMTX (already removed).")
                else:
                    log.warning(f"Failed to remove {cam_id} from MediaMTX: {resp.status_code} - {resp.text}")
        except Exception as e:
            log.error(f"Error communicating with MediaMTX for remove_camera: {e}")

    async def sync_cameras(self, cameras: List[Camera]):
        """Sync a list of active cameras to MediaMTX. Usually called on startup."""
        log.info(f"Syncing {len(cameras)} active cameras to MediaMTX...")
        
        # We don't remove existing ones here because MediaMTX is usually freshly started,
        # but if needed, we could fetch /v3/config/paths/list and compare.
        # For now, simply adding them is sufficient as it overrides if already present.
        for cam in cameras:
            await self.add_camera(cam)

mediamtx_client = MediaMTXClient()
