# Sarvanetra — Ground-Up Build Plan
### From Bare Metal to Commercial-Grade Surveillance Platform

> **How to use this document**  
> Work through phases in order. Each phase ends with a "Definition of Done" checklist — do not move to the next phase until every item is checked. Every phase is self-contained and independently testable. Django/FastAPI integration is introduced in Phase 6; everything before that is pure infrastructure.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Phase 0 — Environment Bootstrap](#phase-0--environment-bootstrap)
3. [Phase 1 — Camera Ingestion with MediaMTX](#phase-1--camera-ingestion-with-mediamtx)
4. [Phase 2 — Object Storage with MinIO](#phase-2--object-storage-with-minio)
5. [Phase 3 — Recording Pipeline](#phase-3--recording-pipeline)
6. [Phase 4 — Kafka Event Bus](#phase-4--kafka-event-bus)
7. [Phase 5 — Motion Detection Pipeline (ONVIF)](#phase-5--motion-detection-pipeline-onvif)
8. [Phase 6 — FastAPI / Django Integration Layer](#phase-6--fastapi--django-integration-layer)
9. [Phase 7 — Authentication & API Gateway (Kong + JWT)](#phase-7--authentication--api-gateway-kong--jwt)
10. [Phase 8 — Frontend & Live Playback UI](#phase-8--frontend--live-playback-ui)
11. [Phase 9 — Camera Health Monitoring](#phase-9--camera-health-monitoring)
12. [Phase 10 — Retention, Cleanup & Storage Governance](#phase-10--retention-cleanup--storage-governance)
13. [Phase 11 — Hardening, Security & Production Readiness](#phase-11--hardening-security--production-readiness)
14. [Known Risks & Pitfalls](#known-risks--pitfalls)
15. [Quick Reference: Port Map & Service Inventory](#quick-reference-port-map--service-inventory)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                   │
│     Browser / Mobile App / API Consumer                                 │
└────────────────────────────┬────────────────────────────────────────────┘
                             │ HTTPS / WS
┌────────────────────────────▼────────────────────────────────────────────┐
│                     KONG API GATEWAY (:8000 / :8443)                   │
│            JWT Auth  ·  Rate Limiting  ·  Route Proxying                │
└──────┬──────────────────────┬──────────────────────────┬────────────────┘
       │                      │                          │
┌──────▼──────┐   ┌───────────▼─────────┐   ┌──────────▼──────────────┐
│  FastAPI /  │   │   Nginx HLS Proxy   │   │   MinIO Object Store    │
│  Django API │   │   (:80 / :8080)     │   │   (:9000 / :9001 UI)    │
│  (:8000)    │   └───────────┬─────────┘   └──────────┬──────────────┘
└──────┬──────┘               │                        │
       │              ┌───────▼──────┐        ┌────────▼──────┐
       │              │   MediaMTX   │        │  Recordings   │
       │              │ (:8554 RTSP) │        │  Snapshots    │
       │              │ (:8888 HLS)  │        │  Buckets      │
       │              │ (:8889 WebRTC│        └───────────────┘
       │              └───────┬──────┘
       │                      │ pulls RTSP
       │              ┌───────▼──────┐
       │              │  IP Cameras  │
       │              │  (RTSP/ONVIF)│
       │              └──────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────────────┐
│                        KAFKA EVENT BUS (:9092)                          │
│     camera.motion  ·  camera.status  ·  recording.segments             │
└──────┬──────────────────┬────────────────────┬───────────────────────┘
       │                  │                    │
┌──────▼──────┐  ┌────────▼────────┐  ┌───────▼───────────┐
│ ONVIF       │  │ Motion Consumer │  │ Upload Worker     │
│ Producers   │  │ (→ PostgreSQL)  │  │ (→ MinIO)         │
└─────────────┘  └─────────────────┘  └───────────────────┘
       │
┌──────▼───────────────────────┐
│  PostgreSQL (:5432)          │
│  Redis (:6379)               │
└──────────────────────────────┘
```

**Core Data Flows:**
- **Live Stream**: Camera → MediaMTX (RTSP) → HLS segments → Nginx → Browser
- **Recording**: MediaMTX → local disk → Upload Worker → MinIO bucket
- **Motion Event**: Camera ONVIF → Producer → Kafka → Consumer → PostgreSQL → API → UI
- **Camera Status**: Status Monitor → Kafka → Consumer → PostgreSQL / Notifications

---

## Phase 0 — Environment Bootstrap

**Goal:** A clean, reproducible working directory with Docker Compose, consistent env vars, and a verified network stack. Every subsequent phase adds services on top of this skeleton.

### 0.1 Directory Structure

```
surv/
├── docker-compose.yml          # single compose file, grows phase by phase
├── .env                        # all secrets and config — never committed
├── .env.example                # template, committed
├── mediamtx/
│   └── mediamtx.yml
├── nginx/
│   ├── nginx.conf
│   └── conf.d/
│       └── hls.conf
├── kong/
│   ├── setup-kong-jwt.sh
│   └── kong.yml                # declarative config (optional)
├── workers/
│   ├── upload_worker.py
│   ├── status_monitor.py
│   ├── minio_cleaner.py
│   └── requirements.txt
├── onvif_producer/
│   ├── onvif_motion_producer.py
│   └── requirements.txt
├── motion_consumer/
│   ├── motion_event_consumer.py
│   └── requirements.txt
├── app/                        # Django or FastAPI app root
│   └── ...
├── recordings/                 # local bind mount for MediaMTX recordings
├── hls/                        # local bind mount for HLS segments
└── snapshots/                  # local bind mount for camera snapshots
```

### 0.2 Base `.env` File

```ini
# Infrastructure
POSTGRES_USER=surv
POSTGRES_PASSWORD=changeme
POSTGRES_DB=sarvanetra
POSTGRES_PORT=5432

REDIS_PORT=6379

MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=changeme123
MINIO_PORT=9000
MINIO_UI_PORT=9001
MINIO_BUCKET_RECORDINGS=recordings
MINIO_BUCKET_SNAPSHOTS=snapshots

KAFKA_PORT=9092

# MediaMTX
MEDIAMTX_RTSP_PORT=8554
MEDIAMTX_HLS_PORT=8888
MEDIAMTX_WEBRTC_PORT=8889
MEDIAMTX_API_PORT=9997

# Kong
KONG_PROXY_PORT=8000
KONG_PROXY_SSL_PORT=8443
KONG_ADMIN_PORT=8001
KONG_ADMIN_SSL_PORT=8444

# App
SECRET_KEY=replace-with-50-char-random-string
DEBUG=True
ALLOWED_HOSTS=*
RETENTION_DAYS=30
```

### 0.3 Starter `docker-compose.yml` Skeleton

```yaml
version: "3.9"

networks:
  surv_net:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  minio_data:
  hls_segments:
  recordings:

services:
  postgres:
    image: postgres:15
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "${POSTGRES_PORT}:5432"
    networks: [surv_net]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "${REDIS_PORT}:6379"
    volumes:
      - redis_data:/data

    networks: [surv_net]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      retries: 5
```

### 0.4 Verification Commands

```bash
docker compose up -d postgres redis
docker compose ps
docker compose exec postgres pg_isready -U surv
docker compose exec redis redis-cli ping   # should return PONG
```

### Phase 0 — Definition of Done

- [ ] `surv/` directory created with all subdirectory stubs
- [ ] `.env` populated with valid values (all `changeme` values replaced)
- [ ] `docker-compose.yml` starts postgres and redis without errors

- [ ] `pg_isready` returns `accepting connections`

- [ ] `redis-cli ping` returns `PONG`

- [ ] No port conflicts on host machine

- [ ] `.env` is in `.gitignore`


---

## Phase 1 — Camera Ingestion with MediaMTX

**Goal:** A real (or simulated) camera RTSP stream is ingested by MediaMTX and accessible via HLS, RTMP, and WebRTC. Nginx proxies HLS to clients. You can watch a live stream in a browser.

### 1.1 What MediaMTX Does

MediaMTX is a zero-dependency media server that:
- Accepts RTSP from IP cameras (push or pull mode)
- Re-publishes as HLS (`.m3u8` + `.ts` segments), RTMP, WebRTC, SRT
- Records streams to disk with configurable paths and segment duration
- Exposes a management REST API on port `9997`
- Supports authentication hooks (useful when integrating with Django later)

### 1.2 `mediamtx/mediamtx.yml` — Full Config


```yaml

# MediaMTX configuration

# Docs: https://github.com/bluenviron/mediamtx

###############################################
# General
###############################################
logLevel: info
logDestinations: [stdout]
logFile: ""

readTimeout: 10s
writeTimeout: 10s
writeQueueSize: 512
udpMaxPayloadSize: 1472

# API (used by upload workers, health checks, Django)
api: yes
apiAddress: :9997
apiEncryption: no

metrics: no
pprof: no

###############################################
# RTSP
###############################################
rtsp: yes
rtspAddress: :8554
rtspEncryption: no  # set to 'optional' in production with certs
rtspAuthMethods: [basic]  # or 'digest'

###############################################
# HLS
###############################################
hls: yes
hlsAddress: :8888
hlsEncryption: no
hlsVariant: lowLatency
hlsSegmentCount: 7           # number of segments in playlist
hlsSegmentDuration: 1s       # segment duration — lower = less latency
hlsPartDuration: 200ms       # LL-HLS part duration
hlsSegmentMaxSize: 50MB
hlsAllowOrigin: "*"          # restrict in production
hlsDirectory: /var/hls       # mapped to hls_segments volume

###############################################
# WebRTC
###############################################
webrtc: yes
webrtcAddress: :8889
webrtcEncryption: no
webrtcLocalUDPAddress: :8189
webrtcLocalTCPAddress: ""
webrtcIPsFromInterfaces: yes
webrtcAllowOrigin: "*"

###############################################
# Recording
###############################################
# NOTE: per-path overrides can also be set here
# Global defaults — recording enabled per-path below

###############################################
# Paths
###############################################
paths:
  # Catch-all: any camera publishing to any path gets recorded
  all_others:
    # Recording
    record: yes
    recordPath: /recordings/%path/%Y-%m-%d_%H-%M-%S-%f
    recordFormat: fmp4          # or 'mpegts' — fmp4 is more universal
    recordSegmentDuration: 60s  # 1-minute segments for manageability
    recordDeleteAfter: 0s       # 0 = keep forever (cleaner handles this)

    # Source: blank means any publisher can push
    source: publisher

    # Optional: pull from camera instead of camera pushing
    # source: rtsp://admin:password@192.168.1.100:554/stream
    # sourceProtocol: tcp
    # sourceOnDemand: yes

  # Example named path for a specific camera (uncomment and replicate per camera)
  # cam_001:
  #   source: rtsp://admin:password@192.168.1.101:554/h264/ch1/main/av_stream
  #   record: yes
  #   recordPath: /recordings/cam_001/%Y-%m-%d_%H-%M-%S
  #   recordSegmentDuration: 60s
```

### 1.3 Nginx HLS Proxy — `nginx/conf.d/hls.conf`

```nginx
server {
    listen 80;
    server_name _;

    # Health check endpoint
    location /health {
        return 200 "ok";
        add_header Content-Type text/plain;
    }

    # HLS stream proxy — clients request /hls/<path>/index.m3u8
    location /hls/ {
        # Proxy to MediaMTX HLS server
        proxy_pass http://mediamtx:8888/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;

        # CORS for browser players
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, OPTIONS";
        add_header Cache-Control "no-cache, no-store";

        # HLS-specific MIME types
        types {
            application/vnd.apple.mpegurl m3u8;
            video/mp2t ts;
            video/mp4  mp4;
            text/plain m3u8;
        }
    }

    # Snapshot serving from MinIO (proxied)
    location /snapshots/ {
        proxy_pass http://minio:9000/snapshots/;
        proxy_set_header Host $host;
    }
}
```

### 1.4 Docker Compose Addition (append to `docker-compose.yml`)

```yaml
  mediamtx:
    image: bluenviron/mediamtx:latest
    restart: unless-stopped
    networks: [surv_net]
    ports:
      - "${MEDIAMTX_RTSP_PORT}:8554"         # RTSP ingest
      - "${MEDIAMTX_HLS_PORT}:8888"           # HLS playback (direct)
      - "${MEDIAMTX_WEBRTC_PORT}:8889"        # WebRTC playback
      - "8189:8189/udp"                        # WebRTC ICE UDP
      - "${MEDIAMTX_API_PORT}:9997"           # Management API
    volumes:
      - ./mediamtx/mediamtx.yml:/mediamtx.yml:ro
      - hls_segments:/var/hls
      - recordings:/recordings
    environment:
      MTX_LOGLEVEL: info

  nginx_hls:
    image: nginx:1.25-alpine
    restart: unless-stopped
    networks: [surv_net]
    ports:
      - "8080:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d/:/etc/nginx/conf.d/:ro
      - hls_segments:/var/hls:ro
    depends_on:
      - mediamtx
```

### 1.5 Testing Without a Physical Camera (FFmpeg Simulator)

```bash
# Push a test RTSP stream to MediaMTX using FFmpeg
# This simulates a camera pushing a stream to the path "cam_test"
docker run --rm --network surv_net \
  jrottenberg/ffmpeg:4.4-alpine \
  -re -f lavfi -i "testsrc2=size=1280x720:rate=25,format=yuv420p" \
  -f lavfi -i "sine=frequency=440:sample_rate=44100" \
  -c:v libx264 -preset ultrafast -tune zerolatency -b:v 500k \
  -c:a aac -b:a 64k \
  -f rtsp rtsp://mediamtx:8554/cam_test
```

After running this, the HLS stream is at:
- Direct MediaMTX: `http://localhost:8888/cam_test/index.m3u8`
- Via Nginx proxy: `http://localhost:8080/hls/cam_test/index.m3u8`
- WebRTC: `http://localhost:8889/cam_test`

Test in browser using [hls.js demo](https://hlsjs.video-dev.org/demo/) or VLC.

### 1.6 Real IP Camera Connection Patterns

**Pattern A — Camera pushes RTSP to MediaMTX (recommended for ONVIF cameras):**
```
Camera → (push RTSP) → MediaMTX
Camera RTSP URL: rtsp://admin:pass@192.168.1.100:554/stream1
Configure camera's "server push" / "RTSP publish" to: rtsp://<server-ip>:8554/cam_001
```

**Pattern B — MediaMTX pulls from camera (simpler setup):**
```yaml
# In mediamtx.yml paths section:
  cam_001:
    source: rtsp://admin:pass@192.168.1.100:554/stream1
    sourceProtocol: tcp
    sourceOnDemand: yes   # only connect when someone is watching
```

**Pattern C — RTMP from encoder/NVR:**
```
NVR → (RTMP) → MediaMTX port 1935
```

### 1.7 MediaMTX API — Key Endpoints

```bash
# List all active paths
curl http://localhost:9997/v3/paths/list

# Get details of a specific path
curl http://localhost:9997/v3/paths/get/cam_test

# List active HLS muxers (confirms HLS is working)
curl http://localhost:9997/v3/hlsmuxers/list

# List recordings
curl http://localhost:9997/v3/recordings/list
```

### Phase 1 — Definition of Done

- [ ] MediaMTX container starts and logs `listener opened on :8554 (RTSP)`
- [ ] Nginx container starts and `curl http://localhost:8080/health` returns `ok`
- [ ] FFmpeg test stream pushes successfully — MediaMTX logs show `[path cam_test] [session ...] is publishing`
- [ ] HLS playlist accessible: `curl http://localhost:8080/hls/cam_test/index.m3u8` returns a valid M3U8
- [ ] Stream plays in VLC or browser HLS player without buffering errors
- [ ] WebRTC endpoint `http://localhost:8889/cam_test` loads in Chromium
- [ ] MediaMTX API `GET /v3/paths/list` returns the active path with status `ready`
- [ ] (If real camera available) Physical camera stream ingested and plays back
- [ ] Recordings directory receives `.mp4` or `.ts` files (confirms recording is working)

---

## Phase 2 — Object Storage with MinIO

**Goal:** MinIO is running, buckets are provisioned, credentials are working, and you can PUT/GET objects via SDK and via the web UI. Upload worker structure is validated with a test file.

### 2.1 What MinIO Does

MinIO is an S3-compatible object store. Sarvanetra uses it to store:
- `recordings/` bucket: video segment files from MediaMTX
- `snapshots/` bucket: JPEG frames captured on motion or on schedule

This gives you practically unlimited scalable storage, a clean REST API (S3 SDK), presigned URLs for secure time-limited downloads, and a lifecycle/retention policy engine.

### 2.2 Docker Compose Addition

```yaml
  minio:
    image: minio/minio:latest
    restart: unless-stopped
    networks: [surv_net]
    ports:
      - "${MINIO_PORT}:9000"
      - "${MINIO_UI_PORT}:9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 15s
      retries: 5

  minio_init:
    image: minio/mc:latest
    networks: [surv_net]
    depends_on:
      minio:
        condition: service_healthy
    restart: on-failure
    entrypoint: >
      /bin/sh -c "
      mc alias set local http://minio:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD};
      mc mb --ignore-existing local/${MINIO_BUCKET_RECORDINGS};
      mc mb --ignore-existing local/${MINIO_BUCKET_SNAPSHOTS};
      mc anonymous set download local/${MINIO_BUCKET_SNAPSHOTS};
      echo 'MinIO buckets initialized';
      "
```

### 2.3 Python Upload Worker — `workers/upload_worker.py`

This is the canonical upload worker. It watches for new recording files and pushes them to MinIO.

```python
"""
upload_worker.py
Watches the /recordings directory for completed segments and uploads to MinIO.
Publishes metadata to Kafka topic recording.segments for downstream consumers.
"""

import os
import time
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError
from kafka import KafkaProducer
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "changeme123")
MINIO_BUCKET = os.getenv("MINIO_BUCKET_RECORDINGS", "recordings")

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
RECORDINGS_DIR = Path(os.getenv("RECORDINGS_DIR", "/recordings"))

# Wait this many seconds after last modification before uploading
# (ensures the segment is fully written)
STABILITY_WAIT = int(os.getenv("STABILITY_WAIT", "5"))

UPLOADED_MARKER = ".uploaded"


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1",
    )


def get_kafka_producer():
    try:
        return KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            retries=3,
        )
    except Exception as e:
        log.warning(f"Kafka unavailable, running without event publishing: {e}")
        return None


def is_stable(path: Path) -> bool:
    """File is stable if it hasn't been modified in STABILITY_WAIT seconds."""
    try:
        mtime = path.stat().st_mtime
        return (time.time() - mtime) > STABILITY_WAIT
    except FileNotFoundError:
        return False


def upload_file(s3, local_path: Path) -> str:
    """Upload file to MinIO and return the object key."""
    # Object key preserves the relative path under recordings/
    relative = local_path.relative_to(RECORDINGS_DIR)
    object_key = str(relative)

    content_type = "video/mp4" if local_path.suffix == ".mp4" else "video/MP2T"

    s3.upload_file(
        str(local_path),
        MINIO_BUCKET,
        object_key,
        ExtraArgs={"ContentType": content_type},
    )
    return object_key


def publish_segment_event(producer, camera_path: str, object_key: str, file_size: int):
    if producer is None:
        return
    event = {
        "event": "recording.segment.uploaded",
        "camera_path": camera_path,
        "object_key": object_key,
        "bucket": MINIO_BUCKET,
        "file_size_bytes": file_size,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    producer.send("recording.segments", event)
    producer.flush()
    log.info(f"Published segment event for {object_key}")


def mark_uploaded(path: Path):
    marker = path.with_suffix(UPLOADED_MARKER)
    marker.touch()


def is_uploaded(path: Path) -> bool:
    return path.with_suffix(UPLOADED_MARKER).exists()


def scan_and_upload(s3, producer):
    extensions = {".mp4", ".ts", ".fmp4"}
    for file_path in RECORDINGS_DIR.rglob("*"):
        if file_path.suffix not in extensions:
            continue
        if is_uploaded(file_path):
            continue
        if not is_stable(file_path):
            continue

        try:
            file_size = file_path.stat().st_size
            # Derive camera path from directory structure
            camera_path = file_path.parent.name
            log.info(f"Uploading {file_path} ({file_size} bytes)")
            object_key = upload_file(s3, file_path)
            publish_segment_event(producer, camera_path, object_key, file_size)
            mark_uploaded(file_path)
            log.info(f"Uploaded → minio://{MINIO_BUCKET}/{object_key}")
        except ClientError as e:
            log.error(f"MinIO upload failed for {file_path}: {e}")
        except Exception as e:
            log.error(f"Unexpected error for {file_path}: {e}")


def main():
    log.info(f"Upload worker starting. Watching: {RECORDINGS_DIR}")
    s3 = get_s3_client()
    producer = get_kafka_producer()

    while True:
        scan_and_upload(s3, producer)
        time.sleep(10)


if __name__ == "__main__":
    main()
```

### 2.4 Workers `requirements.txt`

```
boto3>=1.34
kafka-python>=2.0.2
python-dotenv>=1.0
requests>=2.31
```

### 2.5 Verification

```bash
# Access MinIO web console
open http://localhost:9001
# Login: minioadmin / changeme123

# Check buckets via CLI (inside container)
docker compose exec minio_init mc ls local/

# Test upload from host using AWS CLI (or mc)
docker run --rm --network surv_net --entrypoint mc minio/mc:latest \
  alias set local http://minio:9000 minioadmin changeme123 \
  && mc cp /dev/stdin local/recordings/test.txt <<< "hello minio"

# Verify object exists
docker run --rm --network surv_net --entrypoint mc minio/mc:latest \
  alias set local http://minio:9000 minioadmin changeme123 \
  && mc ls local/recordings/
```

### Phase 2 — Definition of Done

- [ ] MinIO container healthy: `curl http://localhost:9000/minio/health/live` returns HTTP 200
- [ ] MinIO console accessible at `http://localhost:9001`
- [ ] `recordings` and `snapshots` buckets created by `minio_init`
- [ ] Can upload a test file via `mc cp` and see it in the console
- [ ] Can download/presign that file via Python boto3
- [ ] Upload worker starts without errors (run manually: `python workers/upload_worker.py`)
- [ ] After FFmpeg pushes a stream, `.mp4` segments appear in `recordings/` and get uploaded to MinIO within ~15s

---

## Phase 3 — Recording Pipeline

**Goal:** End-to-end validated recording. Camera streams → MediaMTX records segments to disk → Upload Worker uploads to MinIO → object is queryable by segment metadata. This is the foundation of the DVR/NVR feature.

### 3.1 Recording Segment Naming Strategy

MediaMTX uses this format (configured in `mediamtx.yml`):
```
/recordings/<camera_path>/<YYYY-MM-DD>/<HH-MM-SS-ffffff>.mp4
```

Example: `/recordings/cam_001/2024-01-15/14-30-00-000000.mp4`

This naming lets you:
- Query all recordings for a camera on a given date
- Build a timeline by parsing timestamps from filenames
- Implement server-side range queries (e.g., "recordings between 14:00 and 15:00")

### 3.2 Enhanced `mediamtx.yml` Path Recording Config

```yaml
paths:
  all_others:
    record: yes
    recordPath: /recordings/%path/%Y-%m-%d/%H-%M-%S-%f
    recordFormat: fmp4
    recordSegmentDuration: 60s
    recordDeleteAfter: 0s

  # Example for a camera pulling from NVR
  cam_001:
    source: rtsp://admin:pass@192.168.1.100:554/stream1
    sourceProtocol: tcp
    sourceOnDemand: no        # always connected for 24/7 recording
    record: yes
    recordPath: /recordings/cam_001/%Y-%m-%d/%H-%M-%S-%f
    recordSegmentDuration: 60s

  # Low-bandwidth camera (motion-only recording example)
  cam_002:
    source: rtsp://admin:pass@192.168.1.101:554/stream1
    record: yes
    recordPath: /recordings/cam_002/%Y-%m-%d/%H-%M-%S-%f
    recordSegmentDuration: 30s   # shorter segments for motion clips
```

### 3.3 Segment Metadata Tracker

The upload worker should also write a lightweight metadata JSON alongside (or embedded in the database). This enables the timeline API later.

```python
# Extended segment event payload published to Kafka
segment_event = {
    "event": "recording.segment.uploaded",
    "camera_path": "cam_001",            # matches MediaMTX path name
    "camera_id": None,                   # filled in by Django consumer
    "object_key": "cam_001/2024-01-15/14-30-00.mp4",
    "bucket": "recordings",
    "file_size_bytes": 8388608,
    "segment_start_utc": "2024-01-15T14:30:00Z",
    "segment_end_utc": "2024-01-15T14:31:00Z",
    "duration_seconds": 60,
    "uploaded_at": "2024-01-15T14:31:05Z",
}
```

### 3.4 Generating Presigned URLs for Playback

When a user requests a recording clip, the backend generates a time-limited presigned URL directly from MinIO — the video data never passes through Django/FastAPI:

```python
def get_presigned_url(object_key: str, expires_in: int = 3600) -> str:
    """Generate a presigned URL for recording download/playback."""
    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1",
    )
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": MINIO_BUCKET, "Key": object_key},
        ExpiresIn=expires_in,
    )
    return url
```

### 3.5 Snapshot Capture Worker

Periodic snapshots are useful for thumbnail previews and motion event evidence. Add to `workers/snapshot_worker.py`:

```python
"""
snapshot_worker.py
Captures JPEG snapshots from MediaMTX at configurable intervals.
Uses MediaMTX's built-in snapshot API (v3) or ffmpeg.
"""

import os
import time
import logging
import requests
import boto3
from datetime import datetime, timezone

log = logging.getLogger(__name__)
MEDIAMTX_API = os.getenv("MEDIAMTX_API_URL", "http://mediamtx:9997")
SNAPSHOT_INTERVAL = int(os.getenv("SNAPSHOT_INTERVAL_SECONDS", "30"))
MINIO_BUCKET_SNAPSHOTS = os.getenv("MINIO_BUCKET_SNAPSHOTS", "snapshots")


def capture_snapshot(camera_path: str) -> bytes | None:
    """Capture a JPEG snapshot using MediaMTX API."""
    try:
        # MediaMTX v1.6+ supports direct snapshot extraction
        resp = requests.get(
            f"{MEDIAMTX_API}/v3/paths/get/{camera_path}",
            timeout=5,
        )
        if resp.status_code != 200:
            return None
        # Use ffmpeg fallback if API doesn't support snapshot extraction
        import subprocess
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-rtsp_transport", "tcp",
                "-i", f"rtsp://mediamtx:8554/{camera_path}",
                "-vframes", "1",
                "-f", "image2",
                "pipe:1"
            ],
            capture_output=True,
            timeout=10,
        )
        return result.stdout if result.returncode == 0 else None
    except Exception as e:
        log.error(f"Snapshot capture failed for {camera_path}: {e}")
        return None
```

### Phase 3 — Definition of Done

- [ ] MediaMTX creates segment files in `/recordings/<path>/<date>/` structure
- [ ] Upload worker detects new segments within `STABILITY_WAIT` seconds
- [ ] Segments upload to MinIO `recordings` bucket preserving directory structure
- [ ] Presigned URL for an uploaded segment returns a valid MP4 that plays in VLC
- [ ] Segment metadata event published to Kafka `recording.segments` topic
- [ ] Running 10 minutes of continuous stream produces correct segment count (`10 * 60 / segment_duration` files)
- [ ] Upload worker handles restart without re-uploading already-uploaded files (marker mechanism works)
- [ ] No segment files are lost between MediaMTX writing and MinIO upload

---

## Phase 4 — Kafka Event Bus

**Goal:** Kafka is running in KRaft mode (no Zookeeper). All three core topics are created. You can produce and consume test messages. All workers connect to Kafka without errors.

### 4.1 Why Kafka for Surveillance

A surveillance platform generates a constant stream of events: motion triggers, camera online/offline, segment boundaries, health alerts. Kafka decouples these:
- **Producers** (ONVIF workers, status monitors) write events and don't care who reads them
- **Consumers** (DB writers, notification senders, upload trackers) read at their own pace
- **Replay**: If the motion consumer crashes, it resumes from where it left off — no events lost
- **Fan-out**: Multiple consumers can independently process the same event

### 4.2 Docker Compose Addition — Kafka (KRaft Mode)

```yaml
  kafka:
    image: bitnami/kafka:3.7
    restart: unless-stopped
    networks: [surv_net]
    ports:
      - "${KAFKA_PORT}:9092"
      - "9093:9093"   # controller port
    environment:
      # KRaft mode (no Zookeeper)
      KAFKA_CFG_NODE_ID: 1
      KAFKA_CFG_PROCESS_ROLES: controller,broker
      KAFKA_CFG_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_CFG_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093
      KAFKA_CFG_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT
      KAFKA_CFG_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_CFG_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_CFG_AUTO_CREATE_TOPICS_ENABLE: "true"
      KAFKA_CFG_LOG_RETENTION_HOURS: 168       # 7 days
      KAFKA_CFG_LOG_SEGMENT_BYTES: 1073741824  # 1GB segments
      KAFKA_CFG_NUM_PARTITIONS: 3
      KAFKA_CFG_DEFAULT_REPLICATION_FACTOR: 1
      ALLOW_PLAINTEXT_LISTENER: "yes"
    healthcheck:
      test: ["CMD-SHELL", "kafka-topics.sh --bootstrap-server localhost:9092 --list"]
      interval: 20s
      timeout: 10s
      retries: 5

  kafka_init:
    image: bitnami/kafka:3.7
    networks: [surv_net]
    depends_on:
      kafka:
        condition: service_healthy
    restart: on-failure
    entrypoint: >
      /bin/sh -c "
      kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists
        --topic camera.motion --partitions 3 --replication-factor 1;
      kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists
        --topic camera.status --partitions 3 --replication-factor 1;
      kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists
        --topic recording.segments --partitions 3 --replication-factor 1;
      echo 'Kafka topics created';
      "
```

### 4.3 Topic Design

| Topic | Key | Value | Producers | Consumers |
|---|---|---|---|---|
| `camera.motion` | `camera_id` | JSON motion event | ONVIF producers | Motion consumer, alert notifier |
| `camera.status` | `camera_id` | JSON status event | Status monitor | DB writer, FCM notifier |
| `recording.segments` | `camera_path` | JSON segment metadata | Upload worker | Django API consumer, timeline builder |

### 4.4 Standard Event Schemas

**`camera.motion` event:**
```json
{
  "schema_version": "1.0",
  "event_type": "motion.started",
  "camera_id": 42,
  "camera_path": "cam_001",
  "timestamp_utc": "2024-01-15T14:30:00.123Z",
  "source_topic": "VideoSource/VideoAnalytics/Motion",
  "is_motion": true,
  "confidence": null
}
```

**`camera.status` event:**
```json
{
  "schema_version": "1.0",
  "event_type": "camera.online",
  "camera_id": 42,
  "camera_path": "cam_001",
  "timestamp_utc": "2024-01-15T14:00:00Z",
  "previous_status": "offline",
  "current_status": "online",
  "latency_ms": 23
}
```

**`recording.segments` event:**
```json
{
  "schema_version": "1.0",
  "event_type": "recording.segment.uploaded",
  "camera_path": "cam_001",
  "object_key": "cam_001/2024-01-15/14-30-00.mp4",
  "bucket": "recordings",
  "segment_start_utc": "2024-01-15T14:30:00Z",
  "segment_end_utc": "2024-01-15T14:31:00Z",
  "duration_seconds": 60,
  "file_size_bytes": 8388608,
  "uploaded_at": "2024-01-15T14:31:05Z"
}
```

### 4.5 Verification

```bash
# List topics
docker compose exec kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 --list

# Produce a test message
echo '{"test": "hello"}' | docker compose exec -T kafka \
  kafka-console-producer.sh --bootstrap-server localhost:9092 \
  --topic camera.motion --property "key.serializer=org.apache.kafka.common.serialization.StringSerializer"

# Consume from the beginning
docker compose exec kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic camera.motion \
  --from-beginning \
  --max-messages 5

# Check consumer group lag (important for monitoring)
docker compose exec kafka kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --describe --all-groups
```

### Phase 4 — Definition of Done

- [ ] Kafka container healthy: topic list command returns without error
- [ ] Topics `camera.motion`, `camera.status`, `recording.segments` exist
- [ ] Can produce and consume a test JSON message on each topic
- [ ] Upload worker publishes to `recording.segments` after uploading a file
- [ ] Consumer group offset tracking works (consumer picks up where it left off after restart)
- [ ] Kafka web UI (optional: add Kafdrop or Redpanda Console) shows topic details

---

## Phase 5 — Motion Detection Pipeline (ONVIF)

**Goal:** ONVIF-capable cameras are subscribed to, motion events flow from camera → Kafka → PostgreSQL. Motion events are queryable via a simple API. Status monitoring is active.

### 5.1 What ONVIF Does

ONVIF is the standard protocol for IP camera interoperability. Every commercial IP camera supports it. For motion detection, Sarvanetra uses the **Event Service** subset:

1. `CreatePullPointSubscription` — tells the camera "send me events"
2. `PullMessages` — long-poll loop to receive events as they happen
3. Subscription renewal every 60 minutes (cameras expire subscriptions)

Motion events arrive as XML (SOAP) and are parsed into structured JSON for Kafka.

### 5.2 ONVIF Producer — `onvif_producer/onvif_motion_producer.py`

```python
"""
onvif_motion_producer.py
Discovers active cameras from the database, subscribes to ONVIF motion events,
and publishes them to Kafka camera.motion topic.
"""

import os
import time
import json
import logging
import threading
from datetime import datetime, timezone
from typing import Optional

from onvif import ONVIFCamera
from zeep.exceptions import Fault
from kafka import KafkaProducer
import psycopg2
import psycopg2.extras

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

DB_URL = os.getenv("DATABASE_URL", "postgresql://surv:changeme@postgres:5432/sarvanetra")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
ONVIF_USERNAME = os.getenv("ONVIF_DEFAULT_USERNAME", "admin")
ONVIF_PASSWORD = os.getenv("ONVIF_DEFAULT_PASSWORD", "admin")
PULL_TIMEOUT = int(os.getenv("ONVIF_PULL_TIMEOUT_SECONDS", "10"))
SUBSCRIPTION_DURATION = os.getenv("ONVIF_SUBSCRIPTION_DURATION", "PT60M")
DISCOVERY_INTERVAL = int(os.getenv("CAMERA_DISCOVERY_INTERVAL_SECONDS", "60"))


def get_db_connection():
    return psycopg2.connect(DB_URL)


def get_kafka_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: str(k).encode("utf-8"),
        retries=5,
        acks="all",
    )


def get_active_cameras(conn) -> list[dict]:
    """Query cameras that are active and have motion detection enabled."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT id, cam_id, cam_ip, cam_port, onvif_username, onvif_password
            FROM survapp_camera_master
            WHERE is_active = true
              AND motion_active = true
        """)
        return [dict(row) for row in cur.fetchall()]


class ONVIFEventProducer:
    """Manages a single camera's ONVIF subscription and event loop."""

    def __init__(self, camera: dict, kafka_producer: KafkaProducer):
        self.camera = camera
        self.producer = kafka_producer
        self.camera_id = camera["id"]
        self.camera_path = camera["cam_id"]
        self._stop_event = threading.Event()

    def start(self):
        self._thread = threading.Thread(
            target=self._run, name=f"onvif-{self.camera_path}", daemon=True
        )
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _run(self):
        while not self._stop_event.is_set():
            try:
                self._subscribe_and_pull()
            except Exception as e:
                log.error(f"[{self.camera_path}] Error in ONVIF loop: {e}")
                time.sleep(30)  # back off before retry

    def _subscribe_and_pull(self):
        cam = ONVIFCamera(
            self.camera["cam_ip"],
            int(self.camera.get("cam_port", 80)),
            self.camera.get("onvif_username", ONVIF_USERNAME),
            self.camera.get("onvif_password", ONVIF_PASSWORD),
        )
        event_service = cam.create_events_service()
        pullpoint = event_service.CreatePullPointSubscription({
            "InitialTerminationTime": SUBSCRIPTION_DURATION,
        })
        log.info(f"[{self.camera_path}] ONVIF subscription created")

        pullpoint_service = cam.create_pullpoint_service()
        while not self._stop_event.is_set():
            try:
                response = pullpoint_service.PullMessages({
                    "MessageLimit": 100,
                    "Timeout": f"PT{PULL_TIMEOUT}S",
                })
                for msg in (response.NotificationMessage or []):
                    self._process_message(msg)
            except Fault as e:
                log.warning(f"[{self.camera_path}] SOAP fault — resubscribing: {e}")
                break
            except Exception as e:
                log.error(f"[{self.camera_path}] PullMessages error: {e}")
                time.sleep(5)

    def _process_message(self, msg):
        try:
            topic = str(msg.Topic._value_1)
            if "Motion" not in topic and "VideoAnalytics" not in topic:
                return

            # Parse the IsMotion value from SOAP payload
            is_motion = False
            for item in (msg.Message.Message.Data.SimpleItem or []):
                if item.Name in ("IsMotion", "State"):
                    is_motion = str(item.Value).lower() in ("true", "1")

            event_type = "motion.started" if is_motion else "motion.ended"
            event = {
                "schema_version": "1.0",
                "event_type": event_type,
                "camera_id": self.camera_id,
                "camera_path": self.camera_path,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "source_topic": topic,
                "is_motion": is_motion,
            }
            self.producer.send(
                "camera.motion",
                key=str(self.camera_id),
                value=event,
            )
            log.info(f"[{self.camera_path}] Published: {event_type}")
        except Exception as e:
            log.error(f"[{self.camera_path}] Failed to process message: {e}")


class MotionEventProducerWorker:
    """Manages discovery and lifecycle of all camera producers."""

    def __init__(self):
        self.producers: dict[int, ONVIFEventProducer] = {}
        self.kafka = get_kafka_producer()

    def run(self):
        log.info("ONVIF producer worker starting...")
        conn = get_db_connection()
        while True:
            try:
                cameras = get_active_cameras(conn)
                active_ids = {c["id"] for c in cameras}

                # Start new producers for newly active cameras
                for cam in cameras:
                    if cam["id"] not in self.producers:
                        p = ONVIFEventProducer(cam, self.kafka)
                        p.start()
                        self.producers[cam["id"]] = p
                        log.info(f"Started producer for camera {cam['cam_id']}")

                # Stop producers for deactivated cameras
                for cam_id in list(self.producers):
                    if cam_id not in active_ids:
                        self.producers[cam_id].stop()
                        del self.producers[cam_id]
                        log.info(f"Stopped producer for camera_id={cam_id}")

            except Exception as e:
                log.error(f"Discovery error: {e}")
                try:
                    conn = get_db_connection()  # reconnect
                except Exception:
                    pass

            time.sleep(DISCOVERY_INTERVAL)


if __name__ == "__main__":
    worker = MotionEventProducerWorker()
    worker.run()
```

### 5.3 Motion Event Consumer — `motion_consumer/motion_event_consumer.py`

```python
"""
motion_event_consumer.py
Consumes camera.motion events from Kafka and persists them to PostgreSQL.
Maintains motion_event records with start/end timestamps.
"""

import os
import json
import logging
from datetime import datetime, timezone
from kafka import KafkaConsumer
import psycopg2
import psycopg2.extras

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_MOTION_CONSUMER", "motion-consumer-group")
DB_URL = os.getenv("DATABASE_URL", "postgresql://surv:changeme@postgres:5432/sarvanetra")


def get_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        "camera.motion",
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=KAFKA_GROUP_ID,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
        max_poll_interval_ms=300000,
    )


def handle_motion_started(conn, camera_id: int, timestamp_utc: str):
    """Create a new motion_event record."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO survapp_motion_event
              (camera_id, motion_start, is_active, created_at)
            VALUES (%s, %s, true, NOW())
            ON CONFLICT DO NOTHING
        """, (camera_id, timestamp_utc))
    conn.commit()
    log.info(f"Motion STARTED for camera_id={camera_id}")


def handle_motion_ended(conn, camera_id: int, timestamp_utc: str):
    """Close the active motion_event record."""
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE survapp_motion_event
            SET motion_end = %s, is_active = false
            WHERE camera_id = %s AND is_active = true
            RETURNING id
        """, (timestamp_utc, camera_id))
        updated = cur.fetchone()
    conn.commit()
    if updated:
        log.info(f"Motion ENDED for camera_id={camera_id}, event_id={updated[0]}")
    else:
        log.warning(f"Motion ended but no active event found for camera_id={camera_id}")


def main():
    log.info("Motion event consumer starting...")
    conn = psycopg2.connect(DB_URL)
    consumer = get_consumer()

    for msg in consumer:
        event = msg.value
        try:
            camera_id = event.get("camera_id")
            event_type = event.get("event_type")
            timestamp = event.get("timestamp_utc")

            if not camera_id or not event_type:
                log.warning(f"Invalid event: {event}")
                continue

            if event_type == "motion.started":
                handle_motion_started(conn, camera_id, timestamp)
            elif event_type == "motion.ended":
                handle_motion_ended(conn, camera_id, timestamp)
            else:
                log.debug(f"Ignored event_type={event_type}")

        except psycopg2.OperationalError:
            log.error("DB connection lost, reconnecting...")
            conn = psycopg2.connect(DB_URL)
        except Exception as e:
            log.error(f"Error processing event: {e} | event={event}")


if __name__ == "__main__":
    main()
```

### 5.4 Camera Status Monitor — `workers/status_monitor.py`

```python
"""
status_monitor.py
Periodically pings cameras (RTSP + ONVIF) and publishes status events to Kafka.
"""

import os
import time
import json
import socket
import logging
import requests
from datetime import datetime, timezone
from kafka import KafkaProducer
import psycopg2

log = logging.getLogger(__name__)

MEDIAMTX_API = os.getenv("MEDIAMTX_API_URL", "http://mediamtx:9997")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
DB_URL = os.getenv("DATABASE_URL", "postgresql://surv:changeme@postgres:5432/sarvanetra")
PING_INTERVAL = int(os.getenv("STATUS_PING_INTERVAL_SECONDS", "30"))

camera_status_cache = {}  # {camera_id: "online"|"offline"}


def check_camera_via_mediamtx(camera_path: str) -> bool:
    """Check if camera path is active in MediaMTX."""
    try:
        resp = requests.get(
            f"{MEDIAMTX_API}/v3/paths/get/{camera_path}",
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("ready", False)
    except Exception:
        pass
    return False


def check_rtsp_port(ip: str, port: int = 554) -> bool:
    """TCP port check as RTSP availability proxy."""
    try:
        with socket.create_connection((ip, port), timeout=3):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def publish_status_event(producer: KafkaProducer, camera_id: int, camera_path: str,
                          current: str, previous: str):
    event = {
        "schema_version": "1.0",
        "event_type": f"camera.{current}",
        "camera_id": camera_id,
        "camera_path": camera_path,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "previous_status": previous,
        "current_status": current,
    }
    producer.send("camera.status", key=str(camera_id), value=event)
    producer.flush()
    log.info(f"Status: camera_id={camera_id} → {previous} → {current}")


def main():
    log.info("Status monitor starting...")
    conn = psycopg2.connect(DB_URL)
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: str(k).encode("utf-8"),
    )

    while True:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, cam_id, cam_ip FROM survapp_camera_master
                    WHERE is_active = true
                """)
                cameras = cur.fetchall()

            for cam_id, cam_path, cam_ip in cameras:
                is_online = check_camera_via_mediamtx(cam_path) or check_rtsp_port(cam_ip)
                current_status = "online" if is_online else "offline"
                previous_status = camera_status_cache.get(cam_id, "unknown")

                if current_status != previous_status:
                    publish_status_event(producer, cam_id, cam_path,
                                          current_status, previous_status)
                    camera_status_cache[cam_id] = current_status

                    # Update DB directly for fast API response
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE survapp_camera_master
                            SET is_online = %s, last_seen = NOW()
                            WHERE id = %s
                        """, (is_online, cam_id))
                    conn.commit()

        except Exception as e:
            log.error(f"Status monitor error: {e}")
            try:
                conn = psycopg2.connect(DB_URL)
            except Exception:
                pass

        time.sleep(PING_INTERVAL)


if __name__ == "__main__":
    main()
```

### 5.5 Docker Compose Additions

```yaml
  onvif_producer_1:
    build:
      context: ./onvif_producer
      dockerfile: Dockerfile
    restart: unless-stopped
    networks: [surv_net]
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
    depends_on:
      kafka:
        condition: service_healthy
      postgres:
        condition: service_healthy

  motion_consumer_1:
    build:
      context: ./motion_consumer
      dockerfile: Dockerfile
    restart: unless-stopped
    networks: [surv_net]
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
    depends_on:
      kafka:
        condition: service_healthy
      postgres:
        condition: service_healthy

  status_monitor:
    build:
      context: ./workers
      dockerfile: Dockerfile
    restart: unless-stopped
    networks: [surv_net]
    command: python status_monitor.py
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      MEDIAMTX_API_URL: http://mediamtx:9997
```

### 5.6 Testing Without Physical ONVIF Camera

Use the ONVIF Device Test Tool (Windows/Linux) or simulate events directly:

```bash
# Simulate a motion event directly to Kafka (bypasses ONVIF)
docker compose exec kafka kafka-console-producer.sh \
  --bootstrap-server localhost:9092 \
  --topic camera.motion <<< '{"schema_version":"1.0","event_type":"motion.started","camera_id":1,"camera_path":"cam_test","timestamp_utc":"2024-01-15T14:30:00Z","is_motion":true}'

# Verify the consumer wrote to PostgreSQL
docker compose exec postgres psql -U surv -d sarvanetra \
  -c "SELECT * FROM survapp_motion_event ORDER BY id DESC LIMIT 5;"
```

### Phase 5 — Definition of Done

- [ ] ONVIF producer connects to at least one camera without error (or test simulator used)
- [ ] Motion start event appears in `camera.motion` Kafka topic
- [ ] Motion consumer creates a `motion_event` row with `is_active=true`
- [ ] Motion end event updates the row: `motion_end` timestamp set, `is_active=false`
- [ ] Status monitor publishes `camera.online` / `camera.offline` events on status change
- [ ] `camera_master` table `is_online` and `last_seen` fields update correctly
- [ ] Workers survive restart and resume consuming from Kafka without duplicate DB writes
- [ ] Consumer group lag is zero under normal operating conditions

---

## Phase 6 — FastAPI / Django Integration Layer

**Goal:** REST API is live. You can register cameras, retrieve motion events, query recording timelines, and get presigned playback URLs — all via API. This phase creates the bridge between infrastructure and the application layer.

### 6.1 Design Decision: FastAPI vs Django

**Use FastAPI if you are building from scratch or prioritizing:**
- High-performance async API (important for streaming token endpoints)
- OpenAPI/Swagger docs out of the box
- Pydantic validation
- Lighter footprint

**Use Django if you need:**
- Django Admin for camera management UI
- Django ORM for complex relational queries
- Django channels for WebSocket
- Full-featured auth framework (groups, permissions, sessions)

**Recommendation:** Start with FastAPI for the API layer, and add Django Admin separately if needed. Both can coexist pointing to the same PostgreSQL database.

### 6.2 FastAPI Application Structure

```
app/
├── main.py
├── config.py                  # settings from env
├── database.py                # SQLAlchemy async engine
├── models/
│   ├── camera.py
│   ├── motion_event.py
│   └── video_segment.py
├── schemas/
│   ├── camera.py
│   ├── motion_event.py
│   └── recording.py
├── routers/
│   ├── cameras.py
│   ├── streams.py
│   ├── recordings.py
│   ├── motion.py
│   └── health.py
├── services/
│   ├── minio_service.py
│   ├── mediamtx_service.py
│   └── kafka_service.py
└── Dockerfile
```

### 6.3 Core Models — `app/models/camera.py`

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone


class Camera(Base):
    __tablename__ = "survapp_camera_master"

    id = Column(Integer, primary_key=True)
    cam_id = Column(String(100), unique=True, nullable=False)  # e.g. "cam_001"
    cam_name = Column(String(200))
    cam_ip = Column(String(50), nullable=False)
    cam_port = Column(Integer, default=554)
    rtsp_url = Column(String(500))             # full RTSP URL if not pull-mode
    onvif_username = Column(String(100), default="admin")
    onvif_password = Column(String(100), default="admin")
    is_active = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)
    motion_active = Column(Boolean, default=True)
    last_seen = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    motion_events = relationship("MotionEvent", back_populates="camera")
    video_segments = relationship("VideoSegment", back_populates="camera")


class MotionEvent(Base):
    __tablename__ = "survapp_motion_event"

    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey("survapp_camera_master.id"))
    motion_start = Column(DateTime(timezone=True), nullable=False)
    motion_end = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    camera = relationship("Camera", back_populates="motion_events")


class VideoSegment(Base):
    __tablename__ = "survapp_video_segment"

    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey("survapp_camera_master.id"))
    object_key = Column(String(500), nullable=False)
    bucket = Column(String(100), default="recordings")
    segment_start = Column(DateTime(timezone=True), nullable=False)
    segment_end = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    file_size_bytes = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    camera = relationship("Camera", back_populates="video_segments")
```

### 6.4 Key API Endpoints — `app/routers/`

**Cameras:**
```
POST   /api/v1/cameras/             Register a new camera
GET    /api/v1/cameras/             List all cameras with online status
GET    /api/v1/cameras/{cam_id}/    Get camera detail
PATCH  /api/v1/cameras/{cam_id}/    Update camera config
DELETE /api/v1/cameras/{cam_id}/    Deactivate camera
```

**Streams:**
```
GET    /api/v1/streams/{cam_id}/hls-url     Get HLS playback URL (with JWT token)
GET    /api/v1/streams/{cam_id}/webrtc-url  Get WebRTC URL
GET    /api/v1/streams/{cam_id}/snapshot    Get latest snapshot URL
```

**Recordings (Timeline):**
```
GET    /api/v1/recordings/{cam_id}/timeline?date=2024-01-15
       → Returns list of segments for the day with presigned URLs
GET    /api/v1/recordings/{cam_id}/playback?start=...&end=...
       → Returns presigned URL for a specific time range
GET    /api/v1/recordings/{cam_id}/download?object_key=...
       → Returns presigned download URL
```

**Motion Events:**
```
GET    /api/v1/motion/?camera_id=1&date=2024-01-15&active=true
GET    /api/v1/motion/{event_id}/
GET    /api/v1/motion/active/       → All currently active motion events
```

**Health:**
```
GET    /health                       Service health
GET    /api/v1/health/cameras/       All camera status summary
GET    /api/v1/health/workers/       Worker health (via DB ping timestamps)
```

### 6.5 Stream URL Generation with JWT

```python
# services/stream_service.py
import jwt
import time
from datetime import datetime, timezone

SECRET_KEY = os.getenv("SECRET_KEY")
HLS_BASE_URL = os.getenv("HLS_BASE_URL", "http://nginx/hls")

def generate_stream_token(camera_id: int, cam_path: str, expires_in: int = 3600) -> str:
    payload = {
        "sub": str(camera_id),
        "path": cam_path,
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in,
        "type": "stream",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def get_hls_url(cam_path: str, camera_id: int) -> dict:
    token = generate_stream_token(camera_id, cam_path)
    return {
        "hls_url": f"{HLS_BASE_URL}/{cam_path}/index.m3u8",
        "token": token,
        "expires_at": datetime.now(timezone.utc).isoformat(),
    }
```

### 6.6 Timeline API

```python
# routers/recordings.py — timeline endpoint
@router.get("/{cam_id}/timeline")
async def get_timeline(
    cam_id: str,
    date: str,  # format: YYYY-MM-DD
    db: AsyncSession = Depends(get_db),
    minio: MinioService = Depends(get_minio),
):
    """
    Returns all recording segments for a camera on a given date,
    with presigned playback URLs. Powers the DVR timeline scrubber.
    """
    start = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    segments = await db.execute(
        select(VideoSegment)
        .where(VideoSegment.camera_id == cam_id)
        .where(VideoSegment.segment_start >= start)
        .where(VideoSegment.segment_start < end)
        .order_by(VideoSegment.segment_start)
    )

    result = []
    for seg in segments.scalars():
        presigned_url = minio.get_presigned_url(seg.object_key, expires_in=3600)
        result.append({
            "segment_id": seg.id,
            "start": seg.segment_start.isoformat(),
            "end": seg.segment_end.isoformat() if seg.segment_end else None,
            "duration_seconds": seg.duration_seconds,
            "playback_url": presigned_url,
        })

    return {
        "camera_id": cam_id,
        "date": date,
        "total_segments": len(result),
        "segments": result,
    }
```

### 6.7 Recording Segment Consumer (writes to VideoSegment table)

Add a new consumer that listens to `recording.segments` and writes to the DB:

```python
# workers/segment_db_consumer.py
# Listens to recording.segments Kafka topic
# Creates VideoSegment rows for timeline queries

for msg in consumer:
    event = msg.value
    camera = lookup_camera_by_path(conn, event["camera_path"])
    if not camera:
        continue
    insert_video_segment(conn, {
        "camera_id": camera["id"],
        "object_key": event["object_key"],
        "bucket": event["bucket"],
        "segment_start": event["segment_start_utc"],
        "segment_end": event["segment_end_utc"],
        "duration_seconds": event["duration_seconds"],
        "file_size_bytes": event["file_size_bytes"],
    })
```

### Phase 6 — Definition of Done

- [ ] FastAPI (or Django) app starts and `GET /health` returns `{"status": "ok"}`
- [ ] OpenAPI docs available at `/docs`
- [ ] `POST /api/v1/cameras/` creates a camera and it appears in DB
- [ ] `GET /api/v1/streams/{cam_id}/hls-url` returns a valid HLS URL that plays
- [ ] `GET /api/v1/recordings/{cam_id}/timeline?date=...` returns segment list with presigned URLs
- [ ] Presigned URL from timeline endpoint plays in browser video player
- [ ] `GET /api/v1/motion/` returns motion events recorded in Phase 5
- [ ] All endpoints return proper HTTP error codes (404 for missing cameras, 422 for validation)
- [ ] `VideoSegment` table populated by segment_db_consumer reading Kafka

---

## Phase 7 — Authentication & API Gateway (Kong + JWT)

**Goal:** Kong API Gateway is the only public-facing entry point. All API calls require a JWT. MediaMTX stream URLs are also protected by token validation. Konga admin UI is available.

### 7.1 Kong Architecture

```
Client → Kong (:8000) → [JWT validation] → Upstream service
                      → Django/FastAPI (:8000 internal)
                      → MinIO (:9000 internal)
                      → MediaMTX HLS (:8888 internal)
```

### 7.2 Docker Compose Addition — Kong

```yaml
  kong-db-init:
    image: postgres:15
    networks: [surv_net]
    environment:
      PGPASSWORD: ${POSTGRES_PASSWORD}
    entrypoint: >
      /bin/sh -c "
      until pg_isready -h postgres -U ${POSTGRES_USER}; do sleep 2; done;
      psql -h postgres -U ${POSTGRES_USER} -c 'CREATE DATABASE kong;' || true;
      "
    depends_on:
      postgres:
        condition: service_healthy

  kong-migration:
    image: kong:3.6
    networks: [surv_net]
    command: kong migrations bootstrap
    environment:
      KONG_DATABASE: postgres
      KONG_PG_HOST: postgres
      KONG_PG_USER: ${POSTGRES_USER}
      KONG_PG_PASSWORD: ${POSTGRES_PASSWORD}
      KONG_PG_DATABASE: kong
    depends_on:
      - kong-db-init
    restart: on-failure

  kong:
    image: kong:3.6
    restart: unless-stopped
    networks: [surv_net]
    ports:
      - "${KONG_PROXY_PORT}:8000"
      - "${KONG_PROXY_SSL_PORT}:8443"
      - "${KONG_ADMIN_PORT}:8001"
    environment:
      KONG_DATABASE: postgres
      KONG_PG_HOST: postgres
      KONG_PG_USER: ${POSTGRES_USER}
      KONG_PG_PASSWORD: ${POSTGRES_PASSWORD}
      KONG_PG_DATABASE: kong
      KONG_PROXY_LISTEN: 0.0.0.0:8000
      KONG_ADMIN_LISTEN: 0.0.0.0:8001
      KONG_PLUGINS: bundled,jwt
      KONG_LOG_LEVEL: info
    depends_on:
      - kong-migration
    healthcheck:
      test: ["CMD", "kong", "health"]
      interval: 10s
      retries: 5

  konga:
    image: pantsel/konga:latest
    restart: unless-stopped
    networks: [surv_net]
    ports:
      - "1337:1337"
    environment:
      DB_ADAPTER: postgres
      DB_HOST: postgres
      DB_USER: ${POSTGRES_USER}
      DB_PASSWORD: ${POSTGRES_PASSWORD}
      DB_DATABASE: konga
      NODE_ENV: production
    depends_on:
      - kong
```

### 7.3 Kong Setup Script — `kong/setup-kong-jwt.sh`

```bash
#!/bin/sh
set -e
KONG_ADMIN="http://kong:8001"

echo "Waiting for Kong..."
until curl -s "$KONG_ADMIN/status" | grep -q "database"; do sleep 3; done

# Create service for Django/FastAPI API
curl -s -X POST "$KONG_ADMIN/services" \
  -d "name=surv-api" \
  -d "url=http://app:8000"

# Create route for API
curl -s -X POST "$KONG_ADMIN/services/surv-api/routes" \
  -d "name=api-route" \
  -d "paths[]=/api" \
  -d "strip_path=false"

# Enable JWT plugin on the API route
curl -s -X POST "$KONG_ADMIN/routes/api-route/plugins" \
  -d "name=jwt" \
  -d "config.claims_to_verify=exp"

# Create service for HLS streaming (no auth — token in query param via MediaMTX hooks)
curl -s -X POST "$KONG_ADMIN/services" \
  -d "name=hls-stream" \
  -d "url=http://nginx_hls:80"

curl -s -X POST "$KONG_ADMIN/services/hls-stream/routes" \
  -d "name=hls-route" \
  -d "paths[]=/hls" \
  -d "strip_path=false"

# Rate limiting (commercial-grade: 1000 req/min per consumer)
curl -s -X POST "$KONG_ADMIN/plugins" \
  -d "name=rate-limiting" \
  -d "config.minute=1000" \
  -d "config.policy=local"

echo "Kong configured successfully"
```

### 7.4 Creating a JWT Consumer (per user/device)

```bash
# Create a Kong consumer
curl -X POST http://localhost:8001/consumers \
  -d "username=user_shahid" \
  -d "custom_id=user_42"

# Generate JWT credentials for this consumer
curl -X POST http://localhost:8001/consumers/user_shahid/jwt \
  -d "algorithm=HS256" \
  -d "secret=my-secret-key"

# Response includes key (iss) and secret — use these to sign JWTs
```

### 7.5 MediaMTX Stream Authentication Hook

For protected stream access, MediaMTX can call a webhook to validate tokens:

```yaml
# In mediamtx.yml
authMethod: external
authHTTPAddress: http://app:8000/api/v1/auth/stream/

# Your FastAPI endpoint validates the token and returns 200/401
```

```python
# app/routers/auth.py
@router.post("/auth/stream/")
async def validate_stream_access(request: Request):
    """Called by MediaMTX to validate stream access."""
    body = await request.json()
    token = body.get("query", "").replace("token=", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        # Optionally validate path matches payload
        return JSONResponse({"status": "ok"})
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
```

### Phase 7 — Definition of Done

- [ ] Kong starts and `GET http://localhost:8001/status` returns healthy
- [ ] Konga admin UI accessible at `http://localhost:1337`
- [ ] `GET http://localhost:8000/api/v1/cameras/` without JWT returns 401
- [ ] `GET http://localhost:8000/api/v1/cameras/` with valid JWT returns camera list
- [ ] Expired JWT returns 401 with descriptive error
- [ ] Rate limiting active (verify with burst test: >1000 req/min blocked)
- [ ] HLS stream via Kong proxy works with valid stream token
- [ ] MediaMTX auth hook rejects streams with invalid tokens

---

## Phase 8 — Frontend & Live Playback UI

**Goal:** A browser-based UI where users can: see live streams (multi-camera grid), scrub recording timelines, review motion events, and manage cameras. Uses the API built in Phase 6.

### 8.1 Technology Choice

For quick build: **React + Vite** or pure HTML/JS (served by Nginx or Django templates).

For full integration with Django: Django templates + HTMX for dynamic parts.

### 8.2 Core UI Screens

**Screen 1: Live Multi-Camera Grid**
- Grid of HLS players (Video.js or HLS.js)
- Online/offline indicator per camera
- Click to expand to full-screen
- Optional: WebRTC for sub-1-second latency

**Screen 2: Camera-Specific Playback / DVR Timeline**
- Timeline scrubber showing available recordings (colored bars = segment coverage)
- Hover for timestamp
- Click to jump and play that segment
- Motion event markers overlaid on timeline (red markers)
- Download button for selected segment

**Screen 3: Motion Event Alerts**
- Table: Camera | Motion Start | Motion End | Duration | Actions
- Filter by camera, date range
- Click row → jump to recording at that timestamp

**Screen 4: Camera Management**
- Add/edit/delete camera form
- RTSP URL tester (calls MediaMTX API)
- Camera health history chart (online/offline over time)

### 8.3 HLS.js Player Integration

```html
<!-- Live stream player component -->
<video id="player" controls style="width:100%"></video>
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<script>
const videoEl = document.getElementById('player');
const hlsUrl = '/hls/cam_001/index.m3u8';  // from API response

if (Hls.isSupported()) {
  const hls = new Hls({
    lowLatencyMode: true,
    liveSyncDurationCount: 2,
    liveMaxLatencyDurationCount: 4,
  });
  hls.loadSource(hlsUrl);
  hls.attachMedia(videoEl);
} else if (videoEl.canPlayType('application/vnd.apple.mpegurl')) {
  // Safari native HLS
  videoEl.src = hlsUrl;
}
</script>
```

### 8.4 Timeline Scrubber Concept

```javascript
// Fetch timeline segments and render as colored bars
async function loadTimeline(camId, date) {
  const resp = await fetch(`/api/v1/recordings/${camId}/timeline?date=${date}`, {
    headers: { Authorization: `Bearer ${getToken()}` }
  });
  const data = await resp.json();

  const canvas = document.getElementById('timeline');
  const ctx = canvas.getContext('2d');
  const dayStart = new Date(`${date}T00:00:00Z`).getTime();
  const dayEnd = dayStart + 86400000;

  data.segments.forEach(seg => {
    const start = new Date(seg.start).getTime();
    const end = new Date(seg.end).getTime();
    const x = ((start - dayStart) / 86400000) * canvas.width;
    const width = ((end - start) / 86400000) * canvas.width;
    ctx.fillStyle = '#2ecc71';
    ctx.fillRect(x, 0, width, canvas.height);
  });
}
```

### Phase 8 — Definition of Done

- [ ] Live stream plays in browser without manual URL entry
- [ ] Multi-camera grid shows all registered cameras
- [ ] Offline camera shows "disconnected" indicator without crashing the page
- [ ] Timeline scrubber loads and clicking a segment plays the recording
- [ ] Motion events visible in alert table with timestamps
- [ ] Camera can be added via UI form (calls POST /api/v1/cameras/)
- [ ] All API calls use JWT (stored in localStorage or httpOnly cookie)
- [ ] Page works on mobile Chrome (responsive layout)

---

## Phase 9 — Camera Health Monitoring

**Goal:** Comprehensive health visibility for all cameras and workers. Historical uptime graphs. Alerting for cameras offline >5 minutes.

### 9.1 What to Track

| Metric | Source | Storage | Refresh |
|---|---|---|---|
| Camera online/offline | Status monitor | `camera_status_log` table | 30s |
| MediaMTX path ready | MediaMTX API | In-memory + event | 60s |
| Motion detection health | ONVIF producer | `motion_detection_health` | Per event |
| Upload worker lag | Kafka consumer group offset | Log/metric | 60s |
| Disk usage (recordings dir) | Worker stats | `container_stats` | 5 min |
| MinIO bucket size | MinIO API | Logged | 1 hr |

### 9.2 Health Check Endpoints

```python
# app/routers/health.py

@router.get("/cameras/")
async def camera_health_summary(db: AsyncSession = Depends(get_db)):
    """Returns online/offline status and last_seen for all cameras."""
    cameras = await db.execute(
        select(Camera).where(Camera.is_active == True)
    )
    result = []
    for cam in cameras.scalars():
        offline_minutes = None
        if not cam.is_online and cam.last_seen:
            offline_minutes = (datetime.now(timezone.utc) - cam.last_seen).seconds // 60
        result.append({
            "camera_id": cam.cam_id,
            "name": cam.cam_name,
            "is_online": cam.is_online,
            "last_seen": cam.last_seen.isoformat() if cam.last_seen else None,
            "offline_minutes": offline_minutes,
        })
    return result


@router.get("/workers/")
async def worker_health():
    """Check Kafka and MinIO connectivity."""
    checks = {}
    # Kafka check
    try:
        admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP)
        admin.list_topics()
        checks["kafka"] = "healthy"
    except Exception:
        checks["kafka"] = "unreachable"
    # MinIO check
    try:
        s3 = get_s3_client()
        s3.list_buckets()
        checks["minio"] = "healthy"
    except Exception:
        checks["minio"] = "unreachable"
    return checks
```

### 9.3 Alerting — FCM Push Notifications

The existing codebase includes FCM (Firebase Cloud Messaging) for mobile push alerts. Structure:

```python
# workers/notifier.py
import requests

FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY")
FCM_ENDPOINT = "https://fcm.googleapis.com/fcm/send"

def send_push_notification(device_token: str, title: str, body: str, data: dict = {}):
    headers = {
        "Authorization": f"key={FCM_SERVER_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": device_token,
        "notification": {"title": title, "body": body},
        "data": data,
    }
    resp = requests.post(FCM_ENDPOINT, json=payload, headers=headers, timeout=10)
    return resp.status_code == 200
```

### Phase 9 — Definition of Done

- [ ] `GET /api/v1/health/cameras/` shows all cameras with accurate online status
- [ ] Camera going offline updates `is_online=false` and `last_seen` within 60s
- [ ] `CameraStatusLog` table records every online/offline transition with timestamp
- [ ] Health summary endpoint shows `offline_minutes` for cameras down >5 minutes
- [ ] FCM push notification received on mobile device when camera goes offline (if configured)
- [ ] Kafka health check reflects real Kafka connectivity

---

## Phase 10 — Retention, Cleanup & Storage Governance

**Goal:** Storage is managed automatically. Old recordings are deleted based on configurable policy. MinIO bucket sizes stay within limits. Orphaned files are cleaned up.

### 10.1 Retention Policy Design

Commercial NVR systems typically offer:
- **Time-based**: Delete recordings older than N days
- **Storage-based**: Delete oldest recordings when bucket exceeds X GB
- **Camera-specific**: Different retention per camera (e.g., entrance = 90 days, parking = 30 days)

Sarvanetra uses a combination: time-based via MinIO Lifecycle Policies + a Python cleaner for fine-grained control.

### 10.2 MinIO Lifecycle Policy (S3-compatible)

```python
# workers/minio_cleaner.py
import boto3
import json

def apply_lifecycle_policy(bucket: str, retention_days: int):
    """Apply an S3 lifecycle rule to auto-expire objects."""
    s3 = get_s3_client()
    lifecycle_config = {
        "Rules": [
            {
                "ID": f"retention-{retention_days}-days",
                "Status": "Enabled",
                "Expiration": {"Days": retention_days},
                "Filter": {"Prefix": ""},  # applies to all objects
            }
        ]
    }
    s3.put_bucket_lifecycle_configuration(
        Bucket=bucket,
        LifecycleConfiguration=lifecycle_config,
    )
    print(f"Lifecycle policy set: {bucket} → delete after {retention_days} days")
```

### 10.3 Enhanced Cleaner — `workers/minio_cleaner.py`

```python
"""
minio_cleaner.py
Scheduled job to:
1. Delete MinIO objects older than RETENTION_DAYS
2. Sync VideoSegment DB records (mark deleted objects)
3. Remove orphaned .uploaded marker files from disk
4. Log storage stats
"""

import os
import time
import logging
from datetime import datetime, timezone, timedelta
import boto3
import psycopg2

log = logging.getLogger(__name__)
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "30"))
RUN_INTERVAL = int(os.getenv("CLEANER_RUN_INTERVAL_HOURS", "6")) * 3600


def clean_old_recordings(s3, conn):
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    bucket = os.getenv("MINIO_BUCKET_RECORDINGS", "recordings")

    paginator = s3.get_paginator("list_objects_v2")
    deleted_count = 0

    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents", []):
            if obj["LastModified"].replace(tzinfo=timezone.utc) < cutoff:
                s3.delete_object(Bucket=bucket, Key=obj["Key"])
                # Mark as deleted in DB
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE survapp_video_segment SET deleted_at = NOW() WHERE object_key = %s",
                        (obj["Key"],)
                    )
                conn.commit()
                deleted_count += 1

    log.info(f"Cleaner: deleted {deleted_count} objects older than {RETENTION_DAYS} days")


def log_storage_stats(s3, conn):
    """Log total storage used per camera for reporting."""
    bucket = os.getenv("MINIO_BUCKET_RECORDINGS", "recordings")
    paginator = s3.get_paginator("list_objects_v2")
    total_size = 0
    for page in paginator.paginate(Bucket=bucket):
        total_size += sum(obj["Size"] for obj in page.get("Contents", []))

    log.info(f"Storage stats: recordings bucket = {total_size / (1024**3):.2f} GB")


def main():
    s3 = get_s3_client()
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    while True:
        log.info("Running cleaner cycle...")
        clean_old_recordings(s3, conn)
        log_storage_stats(s3, conn)
        time.sleep(RUN_INTERVAL)


if __name__ == "__main__":
    main()
```

### Phase 10 — Definition of Done

- [ ] MinIO lifecycle policy applied to `recordings` bucket (verify in MinIO console under Buckets → Lifecycle)
- [ ] Cleaner runs and deletes objects older than `RETENTION_DAYS`
- [ ] `VideoSegment` table rows have `deleted_at` set for cleaned objects
- [ ] Storage stats logged every 6 hours
- [ ] `.uploaded` marker files cleaned from disk for deleted recordings
- [ ] Camera-specific retention configurable via env or DB field
- [ ] Cleaner handles MinIO pagination correctly (tested with >1000 objects)

---

## Phase 11 — Hardening, Security & Production Readiness

**Goal:** The system is safe to deploy outside a LAN. Secrets are managed properly. SSL/TLS is in place. Settings are environment-driven with no hard-coded values.

### 11.1 Security Checklist

**Secrets & Config:**
- [ ] All secrets in `.env`, never in code
- [ ] `.env` not in version control (`.gitignore`)
- [ ] Production deployment uses Docker secrets or Vault, not `.env`
- [ ] `DEBUG=False` in production
- [ ] `ALLOWED_HOSTS` set to specific domain, not `*`
- [ ] `CORS_ALLOW_ALL_ORIGINS=False` — explicit origins only
- [ ] `SECRET_KEY` is 50+ random characters (use `python -c "import secrets; print(secrets.token_hex(50))"`)

**Network:**
- [ ] Only Kong's ports (8000, 8443) exposed to public internet
- [ ] All internal services (PostgreSQL, Redis, Kafka, MinIO, MediaMTX) on private Docker network
- [ ] RTSP ports (8554) accessible only from camera VLANs
- [ ] MinIO admin (9001) and Kong admin (8001) behind VPN or firewall

**SSL/TLS:**
- [ ] Kong configured with TLS certificates (Let's Encrypt or self-signed for internal)
- [ ] MediaMTX RTSP over TLS (RTSPS) for camera connections
- [ ] Nginx serving HTTPS for HLS

**Auth:**
- [ ] JWT expiry set (max 8 hours for web, 30 days for mobile with refresh)
- [ ] JWT secret rotatable without downtime
- [ ] All stream URLs require tokens
- [ ] Presigned MinIO URLs expire (max 1 hour)

**Credentials:**
- [ ] ONVIF camera passwords stored encrypted in DB (not plain text)
- [ ] MinIO access keys use IAM policies (not root credentials for workers)
- [ ] Kafka SASL/SCRAM enabled for production

### 11.2 Settings Cleanup Pattern (Django)

```python
# core/settings.py — clean, env-driven version
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ["SECRET_KEY"]  # fail fast if not set
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.getenv("POSTGRES_HOST", "postgres"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://redis:6379/0"),
    }
}

CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
CORS_ALLOW_ALL_ORIGINS = False  # never True in production
```

### 11.3 Production Docker Compose Overrides

```yaml
# docker-compose.prod.yml
version: "3.9"

services:
  app:
    environment:
      DEBUG: "False"
      ALLOWED_HOSTS: "yourdomain.com"
    restart: always

  postgres:
    ports: []  # remove external port exposure in production

  redis:
    ports: []

  kafka:
    ports: []

  minio:
    ports:
      - "9000:9000"  # only API, not console
      # 9001 console removed
```

### 11.4 Logging Strategy

```python
LOGGING = {
    "version": 1,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/sarvanetra/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {"handlers": ["console", "file"], "level": "WARNING"},
        "workers": {"handlers": ["console", "file"], "level": "INFO"},
    }
}
```

### Phase 11 — Definition of Done

- [ ] Zero hard-coded secrets anywhere in the codebase
- [ ] `DEBUG=False` works without crashing (static files served correctly)
- [ ] `ALLOWED_HOSTS` restricted and tested
- [ ] Internal services unreachable from outside Docker network
- [ ] JWT secret rotation tested — new token with new secret works, old token rejected
- [ ] All worker Dockerfiles use non-root user (`USER appuser`)
- [ ] Rotating log files configured
- [ ] `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d` brings up hardened stack

---

## Known Risks & Pitfalls

These are the issues already identified in the existing codebase that you should avoid repeating:

### 1. Duplicate / Legacy Files
The original codebase has `views copy.py`, `views copy 2.py`, multiple timeline templates. **Fix:** Never create "copy" files. Use git branches for experiments. Keep only one canonical file per purpose.

### 2. Timezone Handling
Django stores datetimes as UTC internally. Workers (upload_worker, motion_consumer) must also use UTC. ONVIF cameras often send local timestamps. **Fix:** Always call `.replace(tzinfo=timezone.utc)` or `.astimezone(timezone.utc)` when parsing timestamps. Use `USE_TZ = True` in Django settings unconditionally.

### 3. `VideoSegment.__str__` Bug (from existing codebase)
References `self.camera.camera_id` but the field is `cam_id`. **Fix in your rebuild:** Use `cam_id` consistently or add a `@property` alias.

### 4. settings.py Config Conflict
The original settings.py has two PostgreSQL configs where one overwrites the other. **Fix:** Single config block, always env-driven.

### 5. JWT Duplication
Auth logic scattered across views and utils. **Fix:** Single `services/auth_service.py` or `utils/jwt.py` — one place to generate and validate tokens.

### 6. MinIO Client in Wrong File
Original: `minio_client is in upload_worker.py`. **Fix:** Extract to `services/minio_service.py`, import from there in all workers.

### 7. Kafka Consumer Group IDs
If two consumer instances use the same `group_id`, Kafka distributes partitions between them (load balancing). If they use different `group_id`, both get all messages (fan-out). **Fix:** Use explicit, named group IDs per logical consumer type. Never leave as default.

### 8. ONVIF Subscription Renewal
ONVIF subscriptions expire (default 60 minutes). If renewal fails silently, motion events stop arriving without error. **Fix:** Track subscription expiry time in the producer and proactively renew before expiry.

### 9. MediaMTX Recording and Upload Race Condition
The upload worker must not upload segments that MediaMTX is still writing to. **Fix:** The `STABILITY_WAIT` pattern (wait N seconds after last modification) plus checking the file is not locked. Alternatively, use MediaMTX's `runOnRecordSegmentComplete` hook to trigger upload exactly when a segment is finalized.

### 10. MinIO Presigned URLs and Kong
If MinIO is behind Kong, presigned URLs must use the Kong hostname, not the internal `minio:9000` address. **Fix:** Set `MINIO_EXTERNAL_URL` env var for URL generation, separate from the internal `MINIO_ENDPOINT` used for API calls.

---

## Quick Reference: Port Map & Service Inventory

| Service | Internal Port | External Port | Purpose |
|---|---|---|---|
| PostgreSQL | 5432 | 5432 | Primary DB |
| Redis | 6379 | 6379 | Cache / sessions |
| Kafka | 9092, 9093 | 9092 | Event bus |
| MinIO API | 9000 | 9000 | S3 object storage |
| MinIO Console | 9001 | 9001 | Admin UI |
| MediaMTX RTSP | 8554 | 8554 | Camera ingest |
| MediaMTX HLS | 8888 | 8888 | Direct HLS |
| MediaMTX WebRTC | 8889 | 8889 | WebRTC |
| MediaMTX API | 9997 | 9997 | Management API |
| Nginx HLS Proxy | 80 | 8080 | HLS delivery |
| FastAPI/Django | 8000 | — | App (behind Kong) |
| Kong Proxy | 8000 | 80 / 443 | API gateway |
| Kong Admin | 8001 | 8001 | Kong management |
| Konga | 1337 | 1337 | Kong admin UI |

### Startup Order (dependency chain)

```
postgres → redis → kafka → minio → mediamtx → nginx_hls
postgres → kong-migration → kong → kong-config
postgres + kafka → app (FastAPI/Django)
kafka + postgres → onvif_producer
kafka + postgres → motion_consumer
kafka + postgres → status_monitor
kafka + minio + postgres → upload_worker
minio → minio_cleaner
```

### Key Configuration Files by Phase

| Phase | Key Files |
|---|---|
| 0 | `.env`, `docker-compose.yml` skeleton |
| 1 | `mediamtx/mediamtx.yml`, `nginx/conf.d/hls.conf` |
| 2 | `docker-compose.yml` (minio), `workers/upload_worker.py` |
| 3 | `mediamtx/mediamtx.yml` (recording paths), `workers/snapshot_worker.py` |
| 4 | `docker-compose.yml` (kafka), topic schema definitions |
| 5 | `onvif_producer/onvif_motion_producer.py`, `motion_consumer/motion_event_consumer.py`, `workers/status_monitor.py` |
| 6 | `app/` (all FastAPI/Django files), `app/routers/`, `app/models/` |
| 7 | `kong/setup-kong-jwt.sh`, `docker-compose.yml` (kong, konga) |
| 8 | Frontend HTML/React files, Nginx config for static serving |
| 9 | `app/routers/health.py`, `workers/notifier.py` |
| 10 | `workers/minio_cleaner.py`, MinIO lifecycle policy |
| 11 | `core/settings.py` cleanup, `docker-compose.prod.yml` |

---

*This document is your single source of truth for rebuilding Sarvanetra from the ground up. Each phase is independently testable. Work one phase at a time, hit every checkbox before advancing, and you will have a commercial-grade surveillance platform at the end.*
