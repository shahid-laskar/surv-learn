"""
motion_event_consumer.py
Reads camera.motion events from Kafka and writes
motion_event rows to PostgreSQL.
"""

import os
import json
import logging
from datetime import datetime, timezone
from kafka import KafkaConsumer
import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_GROUP_ID  = os.getenv("KAFKA_GROUP_ID",          "motion-consumer-group")
DB_URL          = os.getenv("DATABASE_URL",             "postgresql://surv:changeme@postgres:5432/sarvanetra")


def get_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=KAFKA_GROUP_ID,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest", 
        enable_auto_commit=True,
        api_version=(3, 7, 0),
        max_poll_interval_ms=300000,
    )


def handle_motion_started(conn, camera_id: int, timestamp: str):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO survapp_motion_event
              (camera_id, motion_start, is_active, created_at)
            VALUES (%s, %s, true, NOW())
        """, (camera_id, timestamp))
    conn.commit()
    log.info(f"Motion STARTED — camera_id={camera_id} at {timestamp}")


def handle_motion_ended(conn, camera_id: int, timestamp: str):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE survapp_motion_event
            SET motion_end = %s,
                is_active  = false
            WHERE camera_id = %s
              AND is_active  = true
            RETURNING id
        """, (timestamp, camera_id))
        row = cur.fetchone()
    conn.commit()
    if row:
        log.info(f"Motion ENDED — camera_id={camera_id}, event_id={row[0]}")
    else:
        log.warning(f"Motion ended but no active event found for camera_id={camera_id}")


def main():
    log.info("Motion event consumer starting...")
    conn     = psycopg2.connect(DB_URL)
    consumer = get_consumer()
    
    # Log partition assignment
    consumer.subscribe(
        ["camera.motion"],
        on_assign=lambda c, ps: log.info(f"Partitions assigned: {[p.partition for p in ps]}"),
        on_revoke=lambda c, ps: log.info(f"Partitions revoked: {[p.partition for p in ps]}"),
    )

    log.info("Waiting for messages...")
    for msg in consumer:
        log.info(f"Received message partition={msg.partition} offset={msg.offset}")
        event = msg.value
    
        try:
            camera_id  = event.get("camera_id")
            event_type = event.get("event_type")
            timestamp  = event.get("timestamp_utc")

            if not camera_id or not event_type:
                log.warning(f"Invalid event skipped: {event}")
                continue

            if event_type == "motion.started":
                handle_motion_started(conn, camera_id, timestamp)
            elif event_type == "motion.ended":
                handle_motion_ended(conn, camera_id, timestamp)
            else:
                log.debug(f"Ignored event_type={event_type}")

        except psycopg2.OperationalError:
            log.error("DB connection lost — reconnecting...")
            conn = psycopg2.connect(DB_URL)
        except Exception as e:
            log.error(f"Error processing event: {e} | raw={event}")


if __name__ == "__main__":
    main()