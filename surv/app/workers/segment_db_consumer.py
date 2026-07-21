import os
import json
import logging
import time
from datetime import datetime, timezone, timedelta
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


def get_camera_info(conn, camera_path: str) -> dict | None:
    """Return camera id, recording_mode, and guard secs (None if not found)."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            """SELECT id, recording_mode, motion_pre_guard_secs, motion_post_guard_secs
               FROM survapp_camera_master
               WHERE cam_id = %s AND is_active = true""",
            (camera_path,)
        )
        row = cur.fetchone()
    return dict(row) if row else None


def classify_segment(
    conn,
    camera_id: int,
    seg_start: datetime,
    seg_end: datetime,
    pre_guard_secs: int,
    post_guard_secs: int,
) -> tuple[str, bool]:
    """
    Return (recording_type, has_motion) by checking overlap with motion events.

    recording_type:
      'motion' -- segment overlaps a motion event
      'guard'  -- segment is within pre/post guard window of a motion event
      'full'   -- no relation to motion
    """
    # Expand window by guard secs to find adjacent motion events too
    guard_window_start = seg_start - timedelta(seconds=pre_guard_secs)
    guard_window_end   = seg_end   + timedelta(seconds=post_guard_secs)

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            """SELECT motion_start, motion_end FROM survapp_motion_event
               WHERE camera_id = %s
                 AND is_active = false
                 AND motion_start < %s
                 AND (motion_end IS NULL OR motion_end > %s)""",
            (camera_id, guard_window_end, guard_window_start)
        )
        events = cur.fetchall()

    if not events:
        return "full", False

    for ev in events:
        m_start = ev["motion_start"]
        m_end   = ev["motion_end"] or (m_start + timedelta(minutes=1))

        # Ensure timezone-aware comparison
        if m_start.tzinfo is None:
            m_start = m_start.replace(tzinfo=timezone.utc)
        if m_end.tzinfo is None:
            m_end = m_end.replace(tzinfo=timezone.utc)

        # Direct overlap -> motion segment
        if seg_start < m_end and seg_end > m_start:
            return "motion", True

    # No direct overlap but within guard window -> guard segment
    return "guard", False


def insert_segment(conn, camera_id: int, event: dict,
                   recording_mode: str = "full",
                   pre_guard_secs: int = 60,
                   post_guard_secs: int = 60) -> bool:
    """
    Insert a VideoSegment row with motion-tagging. Returns True if inserted.
    ON CONFLICT updates recording_type/has_motion so re-deliveries self-correct.
    """
    seg_start_str = event.get("segment_start_utc")
    seg_end_str   = event.get("segment_end_utc")

    # Parse timestamps for motion classification
    try:
        seg_start = datetime.fromisoformat(seg_start_str).replace(tzinfo=timezone.utc) \
            if seg_start_str else None
        seg_end   = datetime.fromisoformat(seg_end_str).replace(tzinfo=timezone.utc) \
            if seg_end_str else None
    except (ValueError, TypeError):
        seg_start = seg_end = None

    # Classify segment type
    recording_type = "full"
    has_motion     = False

    if seg_start and seg_end:
        recording_type, has_motion = classify_segment(
            conn, camera_id, seg_start, seg_end,
            pre_guard_secs, post_guard_secs
        )
        log.info(
            f"Segment {event.get('object_key')} classified as "
            f"'{recording_type}' (has_motion={has_motion})"
        )

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO survapp_video_segment
              (camera_id, object_key, bucket,
               segment_start, segment_end,
               duration_seconds, file_size_bytes,
               recording_type, has_motion,
               created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (object_key) DO UPDATE
              SET recording_type = EXCLUDED.recording_type,
                  has_motion     = EXCLUDED.has_motion
            RETURNING (xmax = 0) AS was_inserted
        """, (
            camera_id,
            event.get("object_key"),
            event.get("bucket", "recordings"),
            seg_start_str,
            seg_end_str,
            event.get("duration_seconds"),
            event.get("file_size_bytes"),
            recording_type,
            has_motion,
        ))
        row = cur.fetchone()
        inserted = row[0] if row else False
    conn.commit()
    return inserted


def wait_for_db(max_retries: int = 10, delay: int = 5) -> psycopg2.extensions.connection:
    """Retry DB connection on startup -- postgres may not be ready yet."""
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

    log.info("Subscribed to recording.segments -- waiting for events...")

    for msg in consumer:
        event = msg.value
        log.info(f"Received segment event partition={msg.partition} offset={msg.offset}")

        try:
            camera_path = event.get("camera_path")
            object_key  = event.get("object_key")

            if not camera_path or not object_key:
                log.warning(f"Invalid segment event (missing camera_path or object_key): {event}")
                continue

            cam_info = get_camera_info(conn, camera_path)
            if cam_info is None:
                log.warning(
                    f"No active camera found for path '{camera_path}' -- "
                    f"register the camera via POST /api/v1/cameras/ first"
                )
                continue

            inserted = insert_segment(
                conn,
                cam_info["id"],
                event,
                recording_mode=cam_info.get("recording_mode", "full"),
                pre_guard_secs=cam_info.get("motion_pre_guard_secs", 60),
                post_guard_secs=cam_info.get("motion_post_guard_secs", 60),
            )
            action = "inserted" if inserted else "re-tagged"
            log.info(
                f"Segment {action}: {object_key} "
                f"(camera_id={cam_info['id']}, "
                f"start={event.get('segment_start_utc')})"
            )

        except psycopg2.OperationalError:
            log.error("DB connection lost -- reconnecting...")
            try:
                conn = wait_for_db(max_retries=5, delay=3)
            except RuntimeError:
                log.error("Could not reconnect to DB -- skipping message")
        except Exception as e:
            log.error(f"Error processing segment event: {e} | event={event}")


if __name__ == "__main__":
    main()