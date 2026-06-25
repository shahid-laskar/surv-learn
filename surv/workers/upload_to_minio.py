from minio import Minio
from minio.error import S3Error
import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger(__name__)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "recordings")


def main():
    if len(sys.argv) < 2:
        logger.error("No file path supplied")
        sys.exit(1)

    filepath = sys.argv[1]

    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        sys.exit(1)

    object_name = os.path.relpath(
        filepath,
        "/recordings"
    )

    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )

    logger.info(f"Uploading {object_name}")

    client.fput_object(
        MINIO_BUCKET,
        object_name,
        filepath,
    )

    logger.info(f"Upload completed: {object_name}")


if __name__ == "__main__":
    try:
        main()
    except S3Error as e:
        logger.exception(e)
        sys.exit(1)
    except Exception as e:
        logger.exception(e)
        sys.exit(1)