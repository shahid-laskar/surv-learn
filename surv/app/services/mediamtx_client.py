import logging
import httpx
from typing import List

from app.config import settings
from app.models.camera import Camera

log = logging.getLogger(__name__)

class MediaMTXClient:
    def __init__(self):
        self.api_url = settings.mediamtx_api_url.rstrip("/")

    def _get_rtsp_url(self, cam: Camera) -> str:
        if cam.rtsp_url:
            return cam.rtsp_url
        # Fallback to substream 2 for H.264 browser compatibility if not explicitly set
        return f"rtsp://{cam.onvif_username}:{cam.onvif_password}@{cam.cam_ip}:{cam.cam_port}/unicaststream/2"

    async def add_camera(self, cam: Camera):
        """Add or update a camera path in MediaMTX."""
        url = f"{self.api_url}/v3/config/paths/add/{cam.cam_id}"
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
