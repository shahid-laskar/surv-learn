"""
status_monitor.py
Periodically checks all active cameras via MediaMTX API and/or TCP port ping.
Publishes camera.status events to Kafka on state transitions.
Updates survapp_camera_master.is_online and last_seen directly in PostgreSQL.

Phase 9 additions:
  - Writes a row to camera_status_log on every online/offline transition
  - Back-fills duration_seconds on the previous log row
  - Fires camera-offline alerts via workers/notifier.py if a camera has been
    continuously offline for >= ALERT_THRESHOLD_MINUTES
"""

import os
import time
import json
import socket
import logging
import requests
from datetime import datetime, timezone, timedelta
from kafka import KafkaProducer
import psycopg2
import psycopg2.extras

# Import alert sender — graceful fallback if module not found
try:
    from notifier import send_camera_offline_alert
except ImportError:
    def send_camera_offline_alert(*args, **kwargs):
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log = logging.getLogger(__name__)

MEDIAMTX_API           = os.getenv("MEDIAMTX_API_URL",               "http://mediamtx:9997")
KAFKA_BOOTSTRAP        = os.getenv("KAFKA_BOOTSTRAP_SERVERS",         "kafka:9092")
DB_URL                 = os.getenv("DATABASE_URL",                     "postgresql://surv:changeme@postgres:5432/sarvanetra")
PING_INTERVAL          = int(os.getenv("STATUS_PING_INTERVAL_SECONDS", "30"))
RTSP_PORT              = int(os.getenv("CAMERA_RTSP_PORT",             "554"))
ALERT_THRESHOLD_MINUTES = int(os.getenv("ALERT_THRESHOLD_MINUTES",    "5"))

# In-memory state: {camera_id: {"status": "online"|"offline", "since": datetime, "alerted": bool}}
_state: dict[int, dict] = {}


def get_db_connection():
    return psycopg2.connect(DB_URL)


def get_kafka_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: str(k).encode("utf-8"),
        retries=3,
    )


def check_via_mediamtx(cam_path: str) -> bool:
    """Returns True if MediaMTX considers this path ready (stream active)."""
    try:
        resp = requests.get(
            f"{MEDIAMTX_API}/v3/paths/get/{cam_path}",
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json().get("ready", False)
    except Exception:
        pass
    return False


def check_via_tcp(ip: str, port: int = 554) -> bool:
    """TCP reachability check as RTSP proxy."""
    try:
        with socket.create_connection((ip, port), timeout=3):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def publish_status_event(producer: KafkaProducer, camera_id: int,
                          cam_path: str, current: str, previous: str):
    event = {
        "schema_version":  "1.0",
        "event_type":      f"camera.{current}",
        "camera_id":       camera_id,
        "camera_path":     cam_path,
        "timestamp_utc":   datetime.now(timezone.utc).isoformat(),
        "previous_status": previous,
        "current_status":  current,
    }
    producer.send("camera.status", key=str(camera_id), value=event)
    producer.flush()
    log.info(f"[{cam_path}] Status transition: {previous} → {current}")


def update_camera_db(conn, camera_id: int, is_online: bool):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE survapp_camera_master
               SET is_online = %s,
                   last_seen = CASE WHEN %s THEN NOW() ELSE last_seen END
             WHERE id = %s
        """, (is_online, is_online, camera_id))
    conn.commit()


def insert_status_log(conn, camera_id: int, status: str) -> int | None:
    """Insert a new camera_status_log row. Returns the new row ID."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO camera_status_log (camera_id, status, changed_at)
                VALUES (%s, %s, NOW())
                RETURNING id
            """, (camera_id, status))
            row_id = cur.fetchone()[0]
        conn.commit()
        return row_id
    except Exception as e:
        log.error(f"Failed to insert status log for camera {camera_id}: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return None


def backfill_duration(conn, camera_id: int, current_time: datetime):
    """
    Back-fill duration_seconds on the previous log row for this camera.
    Finds the most recent row with NULL duration_seconds and fills it.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE camera_status_log
                   SET duration_seconds = EXTRACT(EPOCH FROM (%s - changed_at))::INTEGER
                 WHERE id = (
                     SELECT id FROM camera_status_log
                      WHERE camera_id = %s
                        AND duration_seconds IS NULL
                      ORDER BY changed_at DESC
                      LIMIT 1 OFFSET 1   -- skip the row we just inserted
                 )
            """, (current_time, camera_id))
        conn.commit()
    except Exception as e:
        log.error(f"Failed to backfill duration for camera {camera_id}: {e}")
        try:
            conn.rollback()
        except Exception:
            pass


def check_and_alert(conn, camera_id: int, cam_path: str):
    """
    If the camera has been continuously offline for >= ALERT_THRESHOLD_MINUTES
    and an alert hasn't been fired in this offline streak, send an alert.
    """
    cam_state = _state.get(camera_id)
    if not cam_state or cam_state["status"] != "offline":
        return

    offline_since  = cam_state["since"]
    alerted        = cam_state.get("alerted", False)
    offline_minutes = int((datetime.now(timezone.utc) - offline_since).total_seconds() / 60)

    if offline_minutes >= ALERT_THRESHOLD_MINUTES and not alerted:
        log.warning(f"[{cam_path}] ALERT: offline for {offline_minutes} minutes")
        send_camera_offline_alert(camera_id, cam_path, offline_minutes, conn=conn)
        _state[camera_id]["alerted"] = True


def main():
    log.info("Camera status monitor starting...")
    conn     = get_db_connection()
    producer = get_kafka_producer()

    while True:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT id, cam_id, cam_ip
                      FROM survapp_camera_master
                     WHERE is_active = true
                """)
                cameras = [dict(row) for row in cur.fetchall()]

            now = datetime.now(timezone.utc)

            for cam in cameras:
                cam_id   = cam["id"]
                cam_path = cam["cam_id"]
                cam_ip   = cam["cam_ip"]

                is_online = (
                    check_via_mediamtx(cam_path) or
                    check_via_tcp(cam_ip, RTSP_PORT)
                )
                current  = "online" if is_online else "offline"
                previous_state = _state.get(cam_id)
                previous = previous_state["status"] if previous_state else "unknown"

                if current != previous:
                    # State transition — publish event, update DB, write log row
                    publish_status_event(producer, cam_id, cam_path, current, previous)
                    update_camera_db(conn, cam_id, is_online)
                    backfill_duration(conn, cam_id, now)
                    insert_status_log(conn, cam_id, current)

                    _state[cam_id] = {
                        "status":  current,
                        "since":   now,
                        "alerted": False,
                    }
                    log.info(f"[{cam_path}] → {current}")
                else:
                    # No transition
                    if is_online:
                        # Keep last_seen fresh
                        update_camera_db(conn, cam_id, True)
                    else:
                        # Check if we need to fire an offline alert
                        check_and_alert(conn, cam_id, cam_path)

                    if cam_id not in _state:
                        # First run — seed the state
                        _state[cam_id] = {
                            "status":  current,
                            "since":   now,
                            "alerted": False,
                        }

        except psycopg2.OperationalError:
            log.error("DB connection lost — reconnecting...")
            try:
                conn = get_db_connection()
            except Exception as e:
                log.error(f"DB reconnect failed: {e}")
        except Exception as e:
            log.error(f"Status monitor error: {e}")

        time.sleep(PING_INTERVAL)


if __name__ == "__main__":
    main()