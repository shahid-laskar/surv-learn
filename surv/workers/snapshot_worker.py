# workers/snapshot_worker.py

import os
import io
import time
import logging
import subprocess
import boto3
from datetime import datetime, timezone
import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

DATABASE_URL         = os.getenv("DATABASE_URL",            "")
MINIO_ENDPOINT       = os.getenv("MINIO_ENDPOINT",          "minio:9000")
MINIO_ACCESS_KEY     = os.getenv("MINIO_ACCESS_KEY",        "minioadmin")
MINIO_SECRET_KEY     = os.getenv("MINIO_SECRET_KEY",        "minioadmin123")
BUCKET_SNAPSHOTS     = os.getenv("MINIO_BUCKET_SNAPSHOTS",  "snapshots")
MEDIAMTX_RTSP        = os.getenv("MEDIAMTX_RTSP_URL",       "rtsp://mediamtx:8554")
SNAPSHOT_INTERVAL    = int(os.getenv("SNAPSHOT_INTERVAL_SECONDS", "30"))
DEFAULT_CAMERA_PATHS = [c.strip() for c in
                        os.getenv("CAMERA_PATHS", "CAMKRTVM0001").split(",") if c.strip()]


def get_db_connection():
    if not DATABASE_URL:
        return None
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        logger.warning(f"Could not connect to database ({e}), using default camera paths")
        return None


def get_active_cameras(conn) -> list[str]:
    """Query active cameras from database or fallback to DEFAULT_CAMERA_PATHS."""
    if not conn:
        return DEFAULT_CAMERA_PATHS
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT cam_id
                  FROM survapp_camera_master
                 WHERE is_active = true
            """)
            rows = cur.fetchall()
            if rows:
                return [r[0] for r in rows]
    except Exception as e:
        logger.error(f"Error querying active cameras: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
    return DEFAULT_CAMERA_PATHS


def capture_snapshot(camera_path: str) -> bytes | None:
    """Grab a single JPEG frame from the RTSP stream via ffmpeg."""
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-rtsp_transport", "tcp",
                "-i", f"{MEDIAMTX_RTSP}/{camera_path}",
                "-vframes", "1",
                "-f", "image2",
                "pipe:1",
            ],
            capture_output=True,
            timeout=15,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout
        logger.warning(f"ffmpeg failed for {camera_path}: {result.stderr.decode()[:200]}")
        return None
    except subprocess.TimeoutExpired:
        logger.warning(f"ffmpeg timed out for {camera_path}")
        return None
    except Exception as e:
        logger.error(f"Snapshot error for {camera_path}: {e}")
        return None


def upload_snapshot(s3, camera_path: str, data: bytes) -> str:
    """Upload JPEG to MinIO snapshots bucket. Writes timestamped key and latest.jpg."""
    ts  = datetime.now(timezone.utc)
    key = f"{camera_path}/{ts.strftime('%Y/%m/%d/%H-%M-%S')}.jpg"

    s3.put_object(
        Body=data,
        Bucket=BUCKET_SNAPSHOTS,
        Key=key,
        ContentType="image/jpeg",
    )
    latest_key = f"{camera_path}/latest.jpg"
    s3.put_object(
        Body=data,
        Bucket=BUCKET_SNAPSHOTS,
        Key=latest_key,
        ContentType="image/jpeg",
    )
    logger.info(f"Snapshot uploaded: {key} and {latest_key} ({len(data)} bytes)")
    return key


def main():
    s3 = boto3.client(
        "s3",
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1",
    )
    conn = get_db_connection()
    logger.info(f"Snapshot worker started — interval: {SNAPSHOT_INTERVAL}s")

    while True:
        if not conn and DATABASE_URL:
            conn = get_db_connection()
        elif conn and conn.closed:
            conn = get_db_connection()

        camera_paths = get_active_cameras(conn)
        for cam in camera_paths:
            data = capture_snapshot(cam)
            if data:
                upload_snapshot(s3, cam, data)
        time.sleep(SNAPSHOT_INTERVAL)


if __name__ == "__main__":
    main()