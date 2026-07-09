import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path

import boto3
from botocore.client import Config

import httpx

from edge_db import fetch_pending_backups, mark_backup_uploaded
from hub_client import hub_post

log = logging.getLogger("backup_uploader")

SITE_CODE = os.environ.get("SITE_CODE", "UNKNOWN")
HUB_API_URL = os.environ.get("HUB_API_URL", "")
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET_BACKUP", "backup_clips")
MINIO_USE_SSL = os.environ.get("MINIO_USE_SSL", "false").lower() == "true"
BACKUP_ENABLED = os.environ.get("BACKUP_ENABLED", "true").lower() == "true"


def _s3_client():
    protocol = "https" if MINIO_USE_SSL else "http"
    return boto3.client(
        "s3",
        endpoint_url=f"{protocol}://{MINIO_ENDPOINT}",
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def _upload_file(local_path: str, object_key: str) -> None:
    s3 = _s3_client()
    s3.upload_file(local_path, MINIO_BUCKET, object_key)


async def backup_loop(site_code: str, hub_url: str) -> None:
    if not BACKUP_ENABLED or not MINIO_ENDPOINT:
        log.info("Backup upload disabled (BACKUP_ENABLED or MINIO_ENDPOINT unset)")
        while True:
            await asyncio.sleep(300)

    while True:
        try:
            pending = fetch_pending_backups()
            for item in pending:
                path = Path(item["file_path"])
                if not path.is_file():
                    mark_backup_uploaded(int(item["id"]), "")
                    continue

                object_key = f"{site_code}/{item['cam_id']}/{path.name}"
                try:
                    await asyncio.to_thread(_upload_file, str(path), object_key)
                    captured = datetime.fromisoformat(item["captured_at"])
                    async with httpx.AsyncClient() as client:
                        await hub_post(
                            client,
                            f"{hub_url}/fleet/{site_code}/backup-clip",
                            {
                                "cam_id": item["cam_id"],
                                "reason": item["reason"],
                                "captured_at": captured.isoformat(),
                                "object_key": object_key,
                            },
                        )
                    mark_backup_uploaded(int(item["id"]), object_key)
                    log.info("Uploaded backup %s", object_key)
                except Exception as e:
                    log.warning("Backup upload failed %s: %s", path, e)
        except Exception as e:
            log.error("Backup loop error: %s", e)

        await asyncio.sleep(60)
