from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://surv:changeme@postgres:5432/sarvanetra"
    sync_database_url: str = "postgresql://surv:changeme@postgres:5432/sarvanetra"

    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket_recordings: str = "recordings"
    minio_bucket_snapshots: str = "snapshots"
    minio_external_url: str = "http://localhost:9000"

    # MediaMTX
    mediamtx_api_url: str = "http://mediamtx:9997"
    mediamtx_hls_base: str = "http://localhost:8080/hls"
    mediamtx_webrtc_base: str = "http://localhost:8889"

    # Kafka
    kafka_bootstrap_servers: str = "surv_kafka:9092"

    # ── Kong JWT ──────────────────────────────────────────────────────────
    # These MUST match the Kong consumer's JWT credential exactly.
    # kong_jwt_issuer  → the consumer credential's "key" field (iss claim)
    # kong_jwt_secret  → the consumer credential's "secret" field
    # Provisioned together by kong/setup-kong-jwt.sh — see that script.
    kong_jwt_issuer: str = "sarvanetra-app"
    kong_jwt_secret: str = "change-me-to-a-long-random-string-matching-kong-consumer"

    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 hours

    debug: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
