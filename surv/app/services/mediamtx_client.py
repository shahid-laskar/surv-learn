import logging
import httpx
from typing import List
from urllib.parse import quote, urlparse, urlunparse

from app.config import settings
from app.models.camera import Camera

log = logging.getLogger(__name__)

# Default stream path used when rtsp_url is not set (pull protocols only).
# The rtsp_url field should NEVER contain credentials — store only the
# bare URL (e.g. rtsp://192.168.1.10:554/stream1 or rtsps://...).
# Credentials are always taken from onvif_username / onvif_password.
_DEFAULT_RTSP_PATH = "/stream1"
_DEFAULT_PORTS = {
    "rtsp": 554,
    "rtsps": 322,
}
_PULL_PROTOCOLS = frozenset({"rtsp", "rtsps"})


class MediaMTXClient:
    def __init__(self):
        self.api_url = settings.mediamtx_api_url.rstrip("/")

    def _normalize_protocol(self, cam: Camera) -> str:
        proto = (getattr(cam, "stream_protocol", None) or "rtsp").lower().strip()
        if proto not in ("rtsp", "rtsps", "rtmp"):
            log.warning(
                f"[{cam.cam_id}] Unknown stream_protocol={proto!r} — treating as rtsp"
            )
            return "rtsp"
        return proto

    def _get_pull_source_url(self, cam: Camera, protocol: str) -> str:
        """
        Build an RTSP/RTSPS source URL for MediaMTX pull ingest.

        Credentials (onvif_username / onvif_password) are ALWAYS injected
        from the DB fields and URL-encoded so special characters (e.g. '@',
        ':', '#') don't break URL parsing.

        rtsp_url (optional) should be a credential-free URL, e.g.:
            rtsp://192.168.1.10:554/stream1
            rtsps://192.168.1.10:322/stream1
        If omitted, the URL is built from cam_ip + cam_port + default path.
        """
        user = quote(cam.onvif_username or "", safe="")
        pwd  = quote(cam.onvif_password or "", safe="")
        default_port = _DEFAULT_PORTS.get(protocol, 554)

        if cam.rtsp_url:
            parsed = urlparse(cam.rtsp_url)
            # Prefer explicit stream_protocol; fall back to URL scheme if valid.
            scheme = protocol
            if parsed.scheme in _PULL_PROTOCOLS:
                scheme = parsed.scheme
            host = parsed.hostname or cam.cam_ip
            port = parsed.port or cam.cam_port or default_port
            path = parsed.path or _DEFAULT_RTSP_PATH
            netloc = f"{user}:{pwd}@{host}:{port}"
            return urlunparse((scheme, netloc, path, "", "", ""))

        port = cam.cam_port or default_port
        return f"{protocol}://{user}:{pwd}@{cam.cam_ip}:{port}{_DEFAULT_RTSP_PATH}"

    def _path_payload(self, cam: Camera) -> dict:
        protocol = self._normalize_protocol(cam)
        if protocol == "rtmp":
            # Camera/encoder publishes into MediaMTX (rtmp://hub:1935/<cam_id>).
            return {"source": "publisher"}
        return {
            "source": self._get_pull_source_url(cam, protocol),
            "sourceProtocol": "tcp",
        }

    async def add_camera(self, cam: Camera):
        """Add or update a camera path in MediaMTX."""
        url = f"{self.api_url}/v3/config/paths/replace/{cam.cam_id}"
        payload = self._path_payload(cam)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=5.0)
                if resp.status_code in (200, 204):
                    log.info(
                        f"Successfully registered {cam.cam_id} in MediaMTX "
                        f"(protocol={self._normalize_protocol(cam)}, "
                        f"source={payload.get('source')})."
                    )
                else:
                    log.warning(
                        f"Failed to register {cam.cam_id} in MediaMTX: "
                        f"{resp.status_code} - {resp.text}"
                    )
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
                    log.warning(
                        f"Failed to remove {cam_id} from MediaMTX: "
                        f"{resp.status_code} - {resp.text}"
                    )
        except Exception as e:
            log.error(f"Error communicating with MediaMTX for remove_camera: {e}")

    async def sync_cameras(self, cameras: List[Camera]):
        """Sync a list of active cameras to MediaMTX. Usually called on startup."""
        log.info(f"Syncing {len(cameras)} active cameras to MediaMTX...")
        for cam in cameras:
            await self.add_camera(cam)


mediamtx_client = MediaMTXClient()
