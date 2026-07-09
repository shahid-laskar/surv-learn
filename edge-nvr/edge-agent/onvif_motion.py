"""
ONVIF motion detection for edge cameras (runs in background threads).
Simulated RTSP-only cameras (no ONVIF) are skipped.
"""

from __future__ import annotations

import ipaddress
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Callable

from onvif import ONVIFCamera
from zeep.exceptions import Fault

log = logging.getLogger("onvif_motion")

NS = {
    "tt": "http://www.onvif.org/ver10/schema",
}


def _is_onvif_target(camera: dict) -> bool:
    ip_str = (camera.get("cam_ip") or "").strip()
    if not ip_str:
        return False
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    if addr.is_loopback:
        return False
    return bool(camera.get("onvif_username"))


def _parse_motion_state(msg) -> bool | None:
    try:
        elem = msg.Message._value_1
        items = elem.findall(".//tt:SimpleItem", NS)
        item_data = {item.get("Name"): item.get("Value") for item in items}
        rule = item_data.get("Rule", "")
        if rule and rule != "MotionInDefinedCells":
            return None
        val = item_data.get("IsMotion") or item_data.get("State")
        if val is None:
            return None
        return str(val).lower() == "true"
    except Exception:
        return None


def _camera_thread(
    camera: dict,
    on_start: Callable[[str, datetime], None],
    on_end: Callable[[str, datetime], None],
    stop_event: threading.Event,
) -> None:
    cam_id = camera["cam_id"]
    host = camera["cam_ip"]
    port = int(camera.get("onvif_port") or 80)
    user = camera.get("onvif_username") or "admin"
    password = camera.get("onvif_password") or "admin"

    while not stop_event.is_set():
        try:
            cam = ONVIFCamera(host, port, user, password)
            events = cam.create_events_service()
            pullpoint = events.CreatePullPointSubscription()
            mgr = cam.create_pullpoint_service()
            mgr_url = pullpoint.SubscriptionReference.Address._value_1
            mgr = cam.create_pullpoint_service(mgr_url)

            active = False
            while not stop_event.is_set():
                try:
                    result = mgr.PullMessages({"Timeout": "PT5S", "MessageLimit": 10})
                except Fault:
                    break
                for msg in result.NotificationMessage:
                    state = _parse_motion_state(msg)
                    if state is None:
                        continue
                    now = datetime.now(timezone.utc)
                    if state and not active:
                        active = True
                        on_start(cam_id, now)
                    elif not state and active:
                        active = False
                        on_end(cam_id, now)
        except Exception as e:
            log.warning("[%s] ONVIF loop error: %s — retry in 30s", cam_id, e)
            stop_event.wait(30)


class OnvifMotionManager:
    def __init__(
        self,
        on_start: Callable[[str, datetime], None],
        on_end: Callable[[str, datetime], None],
    ):
        self._on_start = on_start
        self._on_end = on_end
        self._stop = threading.Event()
        self._threads: dict[str, threading.Thread] = {}

    def sync_cameras(self, cameras: list[dict]) -> None:
        targets = {
            c["cam_id"]: c
            for c in cameras
            if c.get("motion_active") and _is_onvif_target(c)
        }
        for cam_id in list(self._threads):
            if cam_id not in targets:
                log.info("Stopping ONVIF worker for %s", cam_id)
                # Threads check stop_event globally — restart on next sync cycle
                del self._threads[cam_id]

        for cam_id, cam in targets.items():
            if cam_id in self._threads and self._threads[cam_id].is_alive():
                continue
            t = threading.Thread(
                target=_camera_thread,
                args=(cam, self._on_start, self._on_end, self._stop),
                daemon=True,
                name=f"onvif-{cam_id}",
            )
            self._threads[cam_id] = t
            t.start()
            log.info("Started ONVIF motion worker for %s", cam_id)

    def stop(self) -> None:
        self._stop.set()
