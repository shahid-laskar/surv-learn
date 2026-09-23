"""
status_consumer.py
Kafka consumer for the `camera.status` topic.
Ingests camera status transitions from MediaMTX hooks (camera_ready.sh, camera_down.sh)
and status_monitor.py, updates PostgreSQL camera state, maintains camera_status_log,
and dispatches alert notifications when cameras go offline.
"""

import os
import json
import logging
import time
from datetime import datetime, timezone
import psycopg2
import psycopg2.extras
try:
    from kafka import KafkaConsumer
except ImportError:
    KafkaConsumer = None

try:
    from notifier import send_camera_offline_alert
except ImportError:
    def send_camera_offline_alert(*args, **kwargs):
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log = logging.getLogger("status_consumer")

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC     = os.getenv("KAFKA_TOPIC_STATUS",      "camera.status")
KAFKA_GROUP_ID  = os.getenv("KAFKA_GROUP_ID",          "camera-status-consumer-group")
DB_URL          = os.getenv("DATABASE_URL",             "postgresql://surv:changeme@postgres:5432/sarvanetra")


def get_db_connection():
    return psycopg2.connect(DB_URL)


def get_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=KAFKA_GROUP_ID,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
        max_poll_interval_ms=300000,
    )


def process_status_event(conn, event: dict) -> None:
    # Handle two formats:
    # 1. MediaMTX hook: {"event_type": "camera_status", "camera": "cam_id", "status": "ready"|"notReady", "timestamp": ...}
    # 2. status_monitor: {"event_type": "camera.online"|"camera.offline", "camera_id": 1, "camera_path": "cam_id", ...}

    cam_identifier = event.get("camera") or event.get("camera_path")
    camera_id = event.get("camera_id")

    raw_status = event.get("status") or event.get("current_status")
    if not raw_status and event.get("event_type"):
        if "online" in event["event_type"] or "ready" in event["event_type"]:
            raw_status = "online"
        elif "offline" in event["event_type"] or "notReady" in event["event_type"]:
            raw_status = "offline"

    is_online = raw_status in ("ready", "online", "active")
    normalized_status = "online" if is_online else "offline"

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Resolve camera if only cam_id string is known
        if not camera_id and cam_identifier:
            cur.execute("SELECT id, cam_id, cam_name, is_online FROM survapp_camera_master WHERE cam_id = %s", (cam_identifier,))
            row = cur.fetchone()
        elif camera_id:
            cur.execute("SELECT id, cam_id, cam_name, is_online FROM survapp_camera_master WHERE id = %s", (camera_id,))
            row = cur.fetchone()
        else:
            row = None

        if not row:
            log.debug(f"Camera '{cam_identifier or camera_id}' not found in database — skipping event")
            return

        db_camera_id = row["id"]
        cam_id_str = row["cam_id"]
        cam_name = row["cam_name"] or cam_id_str
        prev_online = row["is_online"]

        # Only process if state transition occurred or last_seen needs updating
        if is_online != prev_online:
            cur.execute("""
                UPDATE survapp_camera_master
                   SET is_online = %s,
                       last_seen = CASE WHEN %s THEN NOW() ELSE last_seen END
                 WHERE id = %s
            """, (is_online, is_online, db_camera_id))

            # Back-fill duration on previous status log row
            cur.execute("""
                SELECT id, changed_at
                  FROM camera_status_log
                 WHERE camera_id = %s
                 ORDER BY changed_at DESC
                 LIMIT 1
            """, (db_camera_id,))
            last_log = cur.fetchone()
            if last_log and last_log["changed_at"]:
                dur = int((datetime.now(timezone.utc) - last_log["changed_at"]).total_seconds())
                cur.execute("""
                    UPDATE camera_status_log
                       SET duration_seconds = %s
                     WHERE id = %s
                """, (max(0, dur), last_log["id"]))

            # Insert new status transition
            cur.execute("""
                INSERT INTO camera_status_log (camera_id, status, changed_at)
                VALUES (%s, %s, NOW())
            """, (db_camera_id, normalized_status))

            conn.commit()
            log.info(f"[{cam_id_str}] Camera transitioned: {'online' if prev_online else 'offline'} -> {normalized_status}")

            if not is_online:
                try:
                    send_camera_offline_alert(conn, db_camera_id, cam_id_str, cam_name)
                except Exception as alert_err:
                    log.warning(f"Failed to dispatch offline alert: {alert_err}")
        else:
            if is_online:
                cur.execute("UPDATE survapp_camera_master SET last_seen = NOW() WHERE id = %s", (db_camera_id,))
                conn.commit()


def main():
    log.info("Starting camera status Kafka consumer...")
    conn = None
    consumer = None

    while True:
        try:
            if not conn or conn.closed:
                conn = get_db_connection()
            if not consumer:
                consumer = get_consumer()
                log.info(f"Subscribed to topic '{KAFKA_TOPIC}' on {KAFKA_BOOTSTRAP}")

            for msg in consumer:
                try:
                    event = msg.value
                    if isinstance(event, dict):
                        process_status_event(conn, event)
                except Exception as proc_err:
                    log.error(f"Error processing message {msg.offset}: {proc_err}")
                    if conn:
                        conn.rollback()

        except Exception as e:
            log.error(f"Consumer loop error: {e}. Retrying in 5 seconds...")
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
                conn = None
            consumer = None
            time.sleep(5)


if __name__ == "__main__":
    main()
