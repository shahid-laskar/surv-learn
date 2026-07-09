"""Build RTSP source URLs for MediaMTX path configuration."""

from __future__ import annotations

import ipaddress
from urllib.parse import quote


def build_rtsp_source(camera: dict) -> str | None:
    """Return RTSP pull URL for a hub camera config dict."""
    if camera.get("rtsp_url"):
        url = camera["rtsp_url"].strip()
        # Sim cameras publish into local MediaMTX — no pull source needed
        if "127.0.0.1" in url or "mediamtx" in url:
            return None
        return url

    cam_ip = (camera.get("cam_ip") or "").strip()
    if not cam_ip:
        return None

    try:
        if ipaddress.ip_address(cam_ip).is_loopback:
            return None
    except ValueError:
        return None

    port = camera.get("cam_port") or 554
    user = camera.get("onvif_username") or ""
    password = camera.get("onvif_password") or ""

    # Common default path when hub has no explicit rtsp_url
    path = "/Streaming/Channels/101"
    if user or password:
        u = quote(user, safe="")
        p = quote(password, safe="")
        return f"rtsp://{u}:{p}@{cam_ip}:{port}{path}"
    return f"rtsp://{cam_ip}:{port}{path}"
