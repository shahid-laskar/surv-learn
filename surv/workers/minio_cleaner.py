"""
workers/minio_cleaner.py
Enforces retention policies on recorded video segments.
Runs periodically to:
1. Read per-camera retention policies from the DB
2. Delete old segments from MinIO
3. Mark deleted rows in survapp_video_segment
4. Set a global MinIO lifecycle policy as a safety net
"""

import os
import time
import logging
from datetime import datetime, timezone, timedelta
import psycopg2
import psycopg2.extras
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log = logging.getLogger(__name__)

DB_URL = os.getenv("DATABASE_URL", "postgresql://surv:changeme@postgres:5432/sarvanetra")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_USER = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_PASS = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123")
BUCKET = os.getenv("MINIO_BUCKET_RECORDINGS", "recordings")
GLOBAL_RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "30"))
INTERVAL_HOURS = int(os.getenv("CLEANER_RUN_INTERVAL_HOURS", "6"))
# For motion_only cameras: how long to keep 'full'-typed (non-motion) segments
MOTION_FULL_RETENTION_DAYS = int(os.getenv("MOTION_FULL_RETENTION_DAYS", "2"))



def get_db_connection():
    return psycopg2.connect(DB_URL)


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_access_key_id=MINIO_USER,
        aws_secret_access_key=MINIO_PASS,
        region_name="us-east-1",
    )


def apply_minio_lifecycle_policy(s3):
    """Sets a global safety-net lifecycle policy on the bucket."""
    # MinIO lifecycle policy max retention. We use the global max + 5 days buffer.
    safety_days = GLOBAL_RETENTION_DAYS + 5
    rule = {
        'Rules': [
            {
                'ID': 'GlobalRetentionSafetyNet',
                'Filter': {'Prefix': ''},
                'Status': 'Enabled',
                'Expiration': {'Days': safety_days}
            }
        ]
    }
    try:
        s3.put_bucket_lifecycle_configuration(
            Bucket=BUCKET,
            LifecycleConfiguration=rule
        )
        log.info(f"Set MinIO bucket lifecycle safety net to {safety_days} days.")
    except ClientError as e:
        log.warning(f"Failed to set bucket lifecycle: {e}")


def clean_old_recordings(s3, conn):
    """Delete recordings older than each camera's configured retention."""
    log.info("Starting retention cleanup cycle...")

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Get retention settings per camera
        cur.execute("SELECT id, cam_id, retention_days FROM survapp_camera_master")
        cameras = cur.fetchall()

    total_deleted = 0
    now = datetime.now(timezone.utc)

    for cam in cameras:
        cam_db_id = cam["id"]
        cam_id_str = cam["cam_id"]
        retention = cam["retention_days"] if cam["retention_days"] is not None else GLOBAL_RETENTION_DAYS
        
        cutoff_date = now - timedelta(days=retention)

        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Find segments for this camera older than cutoff and not yet marked deleted
            cur.execute("""
                SELECT id, object_key 
                FROM survapp_video_segment
                WHERE camera_id = %s
                  AND segment_start < %s
                  AND deleted_at IS NULL
            """, (cam_db_id, cutoff_date))
            expired_segments = cur.fetchall()

        if not expired_segments:
            continue

        log.info(f"Found {len(expired_segments)} expired segments for camera {cam_id_str} (>{retention} days)")

        # Batch delete from S3
        objects_to_delete = [{'Key': row['object_key']} for row in expired_segments]
        
        # S3 delete_objects takes max 1000 at a time
        chunk_size = 1000
        for i in range(0, len(objects_to_delete), chunk_size):
            chunk = objects_to_delete[i:i + chunk_size]
            try:
                s3.delete_objects(
                    Bucket=BUCKET,
                    Delete={'Objects': chunk, 'Quiet': True}
                )
            except ClientError as e:
                log.error(f"Error deleting chunk from S3 for {cam_id_str}: {e}")
                continue
            
            # Mark deleted in DB
            deleted_ids = [row['id'] for row in expired_segments[i:i + chunk_size]]
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE survapp_video_segment
                    SET deleted_at = NOW()
                    WHERE id = ANY(%s)
                """, (deleted_ids,))
            conn.commit()
            total_deleted += len(chunk)

    log.info(f"Cleanup cycle complete. Deleted {total_deleted} segments globally.")


def clean_motion_only_full_segments(s3, conn):
    """
    For cameras in 'motion_only' mode, delete 'full'-typed segments older than
    MOTION_FULL_RETENTION_DAYS. Motion and guard segments keep their full retention.
    """
    log.info("Starting motion-only full-segment cleanup...")
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=MOTION_FULL_RETENTION_DAYS)
    total_deleted = 0

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            "SELECT id, cam_id FROM survapp_camera_master "
            "WHERE recording_mode = 'motion_only' AND is_active = true"
        )
        motion_cameras = cur.fetchall()

    for cam in motion_cameras:
        cam_db_id  = cam["id"]
        cam_id_str = cam["cam_id"]

        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                """SELECT id, object_key FROM survapp_video_segment
                   WHERE camera_id = %s
                     AND recording_type = 'full'
                     AND segment_start < %s
                     AND deleted_at IS NULL""",
                (cam_db_id, cutoff)
            )
            expired = cur.fetchall()

        if not expired:
            continue

        log.info(
            f"motion_only camera {cam_id_str}: {len(expired)} full segments "
            f"older than {MOTION_FULL_RETENTION_DAYS} days to delete"
        )

        objects_to_delete = [{"Key": row["object_key"]} for row in expired]
        chunk_size = 1000
        for i in range(0, len(objects_to_delete), chunk_size):
            chunk = objects_to_delete[i:i + chunk_size]
            try:
                s3.delete_objects(
                    Bucket=BUCKET,
                    Delete={"Objects": chunk, "Quiet": True}
                )
            except ClientError as e:
                log.error(f"Error deleting full-segment chunk for {cam_id_str}: {e}")
                continue

            deleted_ids = [row["id"] for row in expired[i:i + chunk_size]]
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE survapp_video_segment SET deleted_at = NOW() WHERE id = ANY(%s)",
                    (deleted_ids,)
                )
            conn.commit()
            total_deleted += len(chunk)

    log.info(f"Motion-only full-segment cleanup done. Deleted {total_deleted} segments.")


def main():
    log.info(f"MinIO cleaner starting. Interval: {INTERVAL_HOURS} hours.")

    while True:
        try:
            s3 = get_s3_client()
            apply_minio_lifecycle_policy(s3)

            with get_db_connection() as conn:
                clean_old_recordings(s3, conn)
                clean_motion_only_full_segments(s3, conn)

        except psycopg2.OperationalError as e:
            log.error(f"Database error: {e}")
        except ClientError as e:
            log.error(f"S3/MinIO error: {e}")
        except Exception as e:
            log.error(f"Unexpected error in cleaner: {e}")

        time.sleep(INTERVAL_HOURS * 3600)


if __name__ == "__main__":
    main()

