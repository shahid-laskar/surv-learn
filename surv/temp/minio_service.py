import boto3
from app.config import settings


def _client(external: bool = False):
    endpoint = (
        settings.minio_external_url if external
        else f"http://{settings.minio_endpoint}"
    )
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        region_name="us-east-1",
    )


def get_presigned_url(object_key: str, bucket: str = None,
                       expires_in: int = 3600) -> str:
    bucket = bucket or settings.minio_bucket_recordings
    s3 = _client(external=True)
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": object_key},
        ExpiresIn=expires_in,
    )