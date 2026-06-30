from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database — two URLs: async for FastAPI, sync for Alembic/workers
    database_url: str = "postgresql+asyncpg://surv:changeme@postgres:5432/sarvanetra"
    sync_database_url: str = "postgresql://surv:changeme@postgres:5432/sarvanetra"

    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket_recordings: str = "recordings"
    minio_bucket_snapshots: str = "snapshots"
    # Used for presigned URL generation — must be reachable from the browser
    minio_external_url: str = "http://localhost:9000"

    # MediaMTX
    mediamtx_api_url: str = "http://mediamtx:9997"
    mediamtx_hls_base: str = "http://localhost:8080/hls"
    mediamtx_webrtc_base: str = "http://localhost:8889"

    # Kafka — must match KAFKA_ADVERTISED_LISTENERS in docker-compose
    kafka_bootstrap_servers: str = "surv_kafka:9092"

    # Auth
    secret_key: str = "change-me-in-env"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    debug: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()