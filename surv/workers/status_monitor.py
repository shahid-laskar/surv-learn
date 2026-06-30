"""
status_monitor.py
Periodically checks all active cameras via MediaMTX API and/or TCP port ping.
Publishes camera.status events to Kafka on state transitions.
Updates survapp_camera_master.is_online and last_seen directly in PostgreSQL.
"""

import os
import time
import json
import socket
import logging
import requests
from datetime import datetime, timezone
from kafka import KafkaProducer
import psycopg2
import psycopg2.extras

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log = logging.getLogger(__name__)

MEDIAMTX_API    = os.getenv("MEDIAMTX_API_URL",            "http://mediamtx:9997")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS",     "kafka:9092")
DB_URL          = os.getenv("DATABASE_URL",                 "postgresql://surv:changeme@postgres:5432/sarvanetra")
PING_INTERVAL   = int(os.getenv("STATUS_PING_INTERVAL_SECONDS", "30"))
RTSP_PORT       = int(os.getenv("CAMERA_RTSP_PORT",        "554"))

# In-memory cache: {camera_id: "online" | "offline" | "unknown"}
_status_cache: dict[int, str] = {}


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

            for cam in cameras:
                cam_id   = cam["id"]
                cam_path = cam["cam_id"]
                cam_ip   = cam["cam_ip"]

                is_online = (
                    check_via_mediamtx(cam_path) or
                    check_via_tcp(cam_ip, RTSP_PORT)
                )
                current  = "online" if is_online else "offline"
                previous = _status_cache.get(cam_id, "unknown")

                if current != previous:
                    publish_status_event(producer, cam_id, cam_path, current, previous)
                    update_camera_db(conn, cam_id, is_online)
                    _status_cache[cam_id] = current
                elif is_online:
                    # Always keep last_seen fresh for online cameras
                    update_camera_db(conn, cam_id, True)

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