# workers/upload_to_minio.py

from minio import Minio
from minio.error import S3Error
import os
import sys
import io
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

MINIO_ENDPOINT        = os.getenv("MINIO_ENDPOINT",         "minio:9000")
MINIO_ACCESS_KEY      = os.getenv("MINIO_ACCESS_KEY",       "minioadmin")
MINIO_SECRET_KEY      = os.getenv("MINIO_SECRET_KEY",       "minioadmin123")
MINIO_BUCKET          = os.getenv("MINIO_BUCKET",           "recordings")
SEGMENT_DURATION_SECS = int(os.getenv("SEGMENT_DURATION_SECONDS", "60"))


def parse_segment_start(filepath: Path) -> datetime | None:
    """
    Parse segment start time from MediaMTX filename + parent dirs.

    recordPath format: /recordings/%path/%Y/%m/%d/%H-%M-%S-%f
    Example:           /recordings/CAMKRTVM00001/2026/06/25/14-30-00-286963.mp4

    Directory structure:
      filepath.parent      = .../25        (day)
      filepath.parent x2   = .../06        (month)
      filepath.parent x3   = .../2026      (year)
      filepath.parent x4   = .../CAMKRTVM00001  (camera path)
    """
    try:
        stem   = filepath.stem   # e.g. "14-30-00-286963"
        parts  = stem.split("-") # ['14', '30', '00', '286963']

        hour        = int(parts[0])
        minute      = int(parts[1])
        second      = int(parts[2])
        microsecond = int(parts[3])

        day_dir   = filepath.parent
        month_dir = day_dir.parent
        year_dir  = month_dir.parent

        year  = int(year_dir.name)
        month = int(month_dir.name)
        day   = int(day_dir.name)

        return datetime(year, month, day, hour, minute, second,
                        microsecond, tzinfo=timezone.utc)
    except Exception as e:
        logger.warning(f"Could not parse segment start from filename: {filepath} — {e}")
        return None


def upload_segment(client: Minio, filepath: Path) -> str:
    """Upload video segment and return the object key."""
    object_name = str(filepath.relative_to(Path("/recordings")))
    client.fput_object(MINIO_BUCKET, object_name, str(filepath))
    logger.info(f"Uploaded segment: {object_name}")
    return object_name


def upload_metadata(client: Minio, filepath: Path, object_name: str,
                    segment_start: datetime | None) -> None:
    """
    Build and upload a JSON sidecar alongside the video segment.
    This powers the timeline API in Phase 6.
    """
    segment_end = (
        segment_start + timedelta(seconds=SEGMENT_DURATION_SECS)
        if segment_start else None
    )

    # Camera path is 4 levels up from the file: .../CAMKRTVM00001/year/month/day/file
    camera_path = filepath.parent.parent.parent.parent.name

    meta = {
        "schema_version": "1.0",
        "object_key":         object_name,
        "bucket":             MINIO_BUCKET,
        "camera_path":        camera_path,
        "segment_start_utc":  segment_start.isoformat() if segment_start else None,
        "segment_end_utc":    segment_end.isoformat()   if segment_end   else None,
        "duration_seconds":   SEGMENT_DURATION_SECS,
        "file_size_bytes":    filepath.stat().st_size,
        "uploaded_at":        datetime.now(timezone.utc).isoformat(),
    }

    meta_key   = object_name.rsplit(".", 1)[0] + ".json"
    meta_bytes = json.dumps(meta, indent=2).encode()

    client.put_object(
        MINIO_BUCKET,
        meta_key,
        io.BytesIO(meta_bytes),
        length=len(meta_bytes),
        content_type="application/json",
    )
    logger.info(f"Metadata sidecar uploaded: {meta_key}")
    logger.info(f"  camera:  {camera_path}")
    logger.info(f"  start:   {meta['segment_start_utc']}")
    logger.info(f"  end:     {meta['segment_end_utc']}")
    logger.info(f"  size:    {meta['file_size_bytes']} bytes")


def main():
    if len(sys.argv) < 2:
        logger.error("Usage: upload_to_minio.py <filepath>")
        sys.exit(1)

    filepath = Path(sys.argv[1])

    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        sys.exit(1)

    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )

    segment_start = parse_segment_start(filepath)
    object_name   = upload_segment(client, filepath)
    upload_metadata(client, filepath, object_name, segment_start)


if __name__ == "__main__":
    try:
        main()
    except S3Error as e:
        logger.exception(e)
        sys.exit(1)
    except Exception as e:
        logger.exception(e)
        sys.exit(1)