# workers/snapshot_worker.py

import os
import io
import time
import logging
import subprocess
import boto3
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

MINIO_ENDPOINT       = os.getenv("MINIO_ENDPOINT",          "minio:9000")
MINIO_ACCESS_KEY     = os.getenv("MINIO_ACCESS_KEY",        "minioadmin")
MINIO_SECRET_KEY     = os.getenv("MINIO_SECRET_KEY",        "minioadmin123")
BUCKET_SNAPSHOTS     = os.getenv("MINIO_BUCKET_SNAPSHOTS",  "snapshots")
MEDIAMTX_RTSP        = os.getenv("MEDIAMTX_RTSP_URL",       "rtsp://mediamtx:8554")
SNAPSHOT_INTERVAL    = int(os.getenv("SNAPSHOT_INTERVAL_SECONDS", "30"))
CAMERA_PATHS         = [c.strip() for c in
                        os.getenv("CAMERA_PATHS", "CAMKRTVM00001").split(",")]


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
    """Upload JPEG to MinIO snapshots bucket. Returns the object key."""
    ts  = datetime.now(timezone.utc)
    key = f"{camera_path}/{ts.strftime('%Y/%m/%d/%H-%M-%S')}.jpg"

    s3.put_object(
        Body=data,
        Bucket=BUCKET_SNAPSHOTS,
        Key=key,
        ContentType="image/jpeg",
    )
    logger.info(f"Snapshot uploaded: {key} ({len(data)} bytes)")
    return key


def main():
    s3 = boto3.client(
        "s3",
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1",
    )
    logger.info(f"Snapshot worker started — cameras: {CAMERA_PATHS}, interval: {SNAPSHOT_INTERVAL}s")

    while True:
        for cam in CAMERA_PATHS:
            data = capture_snapshot(cam)
            if data:
                upload_snapshot(s3, cam, data)
        time.sleep(SNAPSHOT_INTERVAL)


if __name__ == "__main__":
    main()