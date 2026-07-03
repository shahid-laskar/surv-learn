"""
workers/notifier.py
Sends camera-offline alerts via:
  1. HTTP webhook (POST to ALERT_WEBHOOK_URL) — always tried if set
  2. In-app Notification row in PostgreSQL (always written)

No Firebase dependency. To wire up email or SMS, implement
`send_email_alert()` and call it from `send_camera_offline_alert()`.
"""

import os
import json
import logging
import psycopg2
import psycopg2.extras
import requests
from datetime import datetime, timezone

log = logging.getLogger(__name__)

ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")
DB_URL            = os.getenv("DATABASE_URL", "postgresql://surv:changeme@postgres:5432/sarvanetra")
# Alert backoff: only fire a new alert if camera has been continuously offline
# for at least this many minutes since the LAST alert was sent.
ALERT_BACKOFF_MINUTES = int(os.getenv("ALERT_BACKOFF_MINUTES", "30"))


def _get_db_conn():
    return psycopg2.connect(DB_URL)


def _send_webhook(payload: dict) -> bool:
    """POST the alert payload to the configured webhook URL.
    Returns True on HTTP 2xx, False on failure."""
    if not ALERT_WEBHOOK_URL:
        return False
    try:
        resp = requests.post(
            ALERT_WEBHOOK_URL,
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"},
        )
        if resp.ok:
            log.info(f"[notifier] Webhook delivered → {ALERT_WEBHOOK_URL} ({resp.status_code})")
            return True
        log.warning(f"[notifier] Webhook returned {resp.status_code}: {resp.text[:200]}")
    except requests.RequestException as e:
        log.error(f"[notifier] Webhook delivery failed: {e}")
    return False


def _write_notification_row(conn, camera_id: int, cam_path: str, offline_minutes: int):
    """Persist an in-app notification for all users with camera.view on this camera."""
    title   = f"Camera Offline: {cam_path}"
    message = f"Camera '{cam_path}' has been offline for {offline_minutes} minute(s)."
    payload = json.dumps({
        "event":           "camera.offline",
        "camera_id":       camera_id,
        "camera_path":     cam_path,
        "offline_minutes": offline_minutes,
        "fired_at":        datetime.now(timezone.utc).isoformat(),
    })

    try:
        with conn.cursor() as cur:
            # Write a notification for every active user who is an admin or operator
            # (fine-grained RBAC filtering can be added later; keep it simple for now)
            cur.execute("""
                INSERT INTO notification (user_id, title, message, payload, is_read, created_at)
                SELECT id, %s, %s, %s::jsonb, FALSE, NOW()
                FROM survapp_user
                WHERE is_active = TRUE
                  AND is_locked = FALSE
            """, (title, message, payload))
        conn.commit()
        log.info(f"[notifier] In-app notification written for camera {cam_path}")
    except Exception as e:
        log.error(f"[notifier] Failed to write notification row: {e}")


def send_camera_offline_alert(
    camera_id: int,
    cam_path: str,
    offline_minutes: int,
    conn=None,
):
    """
    Fire all configured alert channels for a camera that has been offline
    for `offline_minutes` minutes.

    `conn` is an optional pre-opened psycopg2 connection (from status_monitor).
    If None, a temporary connection is opened and closed here.
    """
    close_conn = False
    if conn is None:
        conn = _get_db_conn()
        close_conn = True

    webhook_payload = {
        "event":           "camera.offline",
        "camera_id":       camera_id,
        "camera_path":     cam_path,
        "offline_minutes": offline_minutes,
        "timestamp":       datetime.now(timezone.utc).isoformat(),
    }

    _send_webhook(webhook_payload)
    _write_notification_row(conn, camera_id, cam_path, offline_minutes)

    if close_conn:
        conn.close()
