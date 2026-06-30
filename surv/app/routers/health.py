from fastapi import APIRouter
from app.services.mediamtx_service import get_active_paths
from app.config import settings
import boto3, httpx

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health():
    return {"status": "ok"}


@router.get("/services")
async def service_health():
    checks = {}

    # MediaMTX
    try:
        paths = await get_active_paths()
        checks["mediamtx"] = {"status": "healthy", "active_paths": len(paths)}
    except Exception as e:
        checks["mediamtx"] = {"status": "unreachable", "error": str(e)}

    # MinIO
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=f"http://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            region_name="us-east-1",
        )
        s3.list_buckets()
        checks["minio"] = {"status": "healthy"}
    except Exception as e:
        checks["minio"] = {"status": "unreachable", "error": str(e)}

    return checks