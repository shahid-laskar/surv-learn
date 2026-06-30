import os
import json
import logging
import time
import psycopg2
import psycopg2.extras
from kafka import KafkaConsumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log = logging.getLogger(__name__)

# segment_db_consumer uses the plain postgresql:// URL (sync psycopg2)
# The DATABASE_URL env var in its compose service is set to the sync URL
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "surv_kafka:9092")
KAFKA_GROUP_ID  = os.getenv("KAFKA_GROUP_SEGMENT_CONSUMER", "segment-db-consumer-group")
DB_URL          = os.getenv("DATABASE_URL",
                             "postgresql://surv:changeme@postgres:5432/sarvanetra")


def get_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        "recording.segments",
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=KAFKA_GROUP_ID,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        max_poll_interval_ms=300000,
    )


def get_db_connection():
    return psycopg2.connect(DB_URL)


def get_camera_id(conn, camera_path: str) -> int | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM survapp_camera_master WHERE cam_id = %s AND is_active = true",
            (camera_path,)
        )
        row = cur.fetchone()
    return row[0] if row else None


def insert_segment(conn, camera_id: int, event: dict) -> bool:
    """
    Insert a VideoSegment row. Returns True if inserted, False if duplicate.
    ON CONFLICT DO NOTHING handles the case where the same segment file
    triggers the hook twice (e.g. after a container restart).
    """
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO survapp_video_segment
              (camera_id, object_key, bucket,
               segment_start, segment_end,
               duration_seconds, file_size_bytes,
               created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (object_key) DO NOTHING
        """, (
            camera_id,
            event.get("object_key"),
            event.get("bucket", "recordings"),
            event.get("segment_start_utc"),
            event.get("segment_end_utc"),
            event.get("duration_seconds"),
            event.get("file_size_bytes"),
        ))
        inserted = cur.rowcount > 0
    conn.commit()
    return inserted


def wait_for_db(max_retries: int = 10, delay: int = 5) -> psycopg2.extensions.connection:
    """Retry DB connection on startup — postgres may not be ready yet."""
    for attempt in range(1, max_retries + 1):
        try:
            conn = get_db_connection()
            log.info("DB connection established")
            return conn
        except psycopg2.OperationalError as e:
            log.warning(f"DB not ready (attempt {attempt}/{max_retries}): {e}")
            time.sleep(delay)
    raise RuntimeError("Could not connect to PostgreSQL after retries")


def main():
    log.info("Segment DB consumer starting...")
    conn     = wait_for_db()
    consumer = get_consumer()

    log.info("Subscribed to recording.segments — waiting for events...")

    for msg in consumer:
        event = msg.value
        log.info(f"Received segment event partition={msg.partition} offset={msg.offset}")

        try:
            camera_path = event.get("camera_path")
            object_key  = event.get("object_key")

            if not camera_path or not object_key:
                log.warning(f"Invalid segment event (missing camera_path or object_key): {event}")
                continue

            camera_id = get_camera_id(conn, camera_path)
            if camera_id is None:
                log.warning(
                    f"No active camera found for path '{camera_path}' — "
                    f"register the camera via POST /api/v1/cameras/ first"
                )
                continue

            inserted = insert_segment(conn, camera_id, event)
            if inserted:
                log.info(
                    f"Segment inserted: {object_key} "
                    f"(camera_id={camera_id}, "
                    f"start={event.get('segment_start_utc')})"
                )
            else:
                log.debug(f"Duplicate segment skipped: {object_key}")

        except psycopg2.OperationalError:
            log.error("DB connection lost — reconnecting...")
            try:
                conn = wait_for_db(max_retries=5, delay=3)
            except RuntimeError:
                log.error("Could not reconnect to DB — skipping message")
        except Exception as e:
            log.error(f"Error processing segment event: {e} | event={event}")


if __name__ == "__main__":
    main()