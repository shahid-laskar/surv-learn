# Sarvanetra — Ground-Up Build Plan (As-Built Edition)
### From Bare Metal to Commercial-Grade Surveillance Platform

> **How to use this document**
> This is the as-built edition — it reflects what was actually implemented, including every real-world deviation from the original plan, every bug that was hit, and every fix that worked. Work through phases in order. Each phase ends with a "Definition of Done" checklist. Do not move to the next phase until every item is checked.
>
> **VM Environment:** Ubuntu VM at `10.44.0.209`. Dev PC accesses all UIs from that IP.
> **Stack:** FastAPI (not Django), React + Vite + Tailwind v4 (not plain HTML), Kafka KRaft (no Zookeeper).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Phase 0 — Environment Bootstrap](#phase-0--environment-bootstrap)
3. [Phase 1 — Camera Ingestion with MediaMTX](#phase-1--camera-ingestion-with-mediamtx)
4. [Phase 2 — Object Storage with MinIO](#phase-2--object-storage-with-minio)
5. [Phase 3 — Recording Pipeline](#phase-3--recording-pipeline)
6. [Phase 4 — Kafka Event Bus](#phase-4--kafka-event-bus)
7. [Phase 5 — Motion Detection Pipeline (ONVIF)](#phase-5--motion-detection-pipeline-onvif)
8. [Phase 6 — FastAPI Integration Layer](#phase-6--fastapi-integration-layer)
9. [Phase 7 — Authentication & API Gateway (Kong + JWT)](#phase-7--authentication--api-gateway-kong--jwt)
10. [Phase 8 — Frontend (React + Vite + Tailwind v4)](#phase-8--frontend-react--vite--tailwind-v4)
11. [Phase 9 — Camera Health Monitoring](#phase-9--camera-health-monitoring)
12. [Phase 10 — Retention, Cleanup & Storage Governance](#phase-10--retention-cleanup--storage-governance)
13. [Phase 11 — Hardening, Security & Production Readiness](#phase-11--hardening-security--production-readiness)
14. [Real-World Bugs & Fixes Log](#real-world-bugs--fixes-log)
15. [Quick Reference: Port Map & Service Inventory](#quick-reference-port-map--service-inventory)

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│   Browser on dev PC (10.44.0.55) → VM (10.44.0.209)            │
└───────────────────────┬──────────────────────────────────────────┘
                        │ HTTP (no TLS yet — Phase 11)
┌───────────────────────▼──────────────────────────────────────────┐
│              KONG API GATEWAY (:8000)                            │
│   /api  → FastAPI (internal http://app:8000)                    │
│   /hls  → nginx_hls (internal http://nginx_hls:80)             │
│   JWT plugin validates Bearer token on all routes except login  │
└──────┬──────────────────┬───────────────────────────────────────┘
       │                  │
┌──────▼──────┐   ┌───────▼──────────────────────────────────────┐
│  FastAPI    │   │  Nginx HLS Proxy (:8080 direct, :8000/hls    │
│  (:8000     │   │  via Kong)                                   │
│  internal)  │   │  Rewrites MediaMTX 302 redirect Location     │
└──────┬──────┘   │  header to preserve port + /hls/ prefix      │
       │          └───────┬──────────────────────────────────────┘
       │                  │ proxy_pass http://mediamtx:8888/
       │          ┌───────▼──────┐
       │          │   MediaMTX   │  authMethod: http → FastAPI
       │          │ (:8554 RTSP) │  /api/v1/auth/stream webhook
       │          │ (:8888 HLS)  │  validates stream tokens
       │          │ (:8889 WebRTC│
       │          │ (:9997 API)  │
       │          └───────┬──────┘
       │                  │ pulls RTSP from camera
       │          ┌───────▼──────┐
       │          │  IP Camera   │  CAMKRTVM00001
       │          │  10.44.0.219 │  rtsp://admin:admin@.../unicaststream/1
       │          └──────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────┐
│                   KAFKA EVENT BUS (surv_kafka:9092)              │
│   KRaft mode — no Zookeeper. Container name: surv_kafka         │
│   Topics: camera.motion · camera.status · recording.segments    │
└──────┬──────────────────┬──────────────────────────────────────┘
       │                  │
┌──────▼──────┐  ┌────────▼────────┐  ┌──────────────────────────┐
│ ONVIF       │  │ Motion Consumer │  │ Segment DB Consumer      │
│ Producer    │  │ → PostgreSQL    │  │ recording.segments →     │
│             │  │                 │  │ survapp_video_segment     │
└─────────────┘  └─────────────────┘  └──────────────────────────┘
       │
┌──────▼───────────────────────────────────────────────────────────┐
│  PostgreSQL (:5432)   Redis (:6379)   MinIO (:9000/:9001)       │
└──────────────────────────────────────────────────────────────────┘
```

**Core Data Flows:**
- **Live Stream**: Camera → MediaMTX RTSP → HLS segments → Nginx (with redirect rewrite) → Browser
- **Recording**: MediaMTX `runOnRecordSegmentComplete` hook → `upload_to_minio.py` → MinIO
- **Motion Event**: Camera ONVIF → Producer → `camera.motion` Kafka → Consumer → PostgreSQL → FastAPI → UI
- **Segment Tracking**: MinIO upload → `recording.segments` Kafka → Segment DB Consumer → `survapp_video_segment` → Timeline API
- **Auth**: Browser login → Kong `/api/v1/auth/login` (open route) → FastAPI signs JWT → Kong's JWT plugin validates on all subsequent requests

---

## Phase 0 — Environment Bootstrap

**Status: ✅ COMPLETE**

### Actual Directory Structure (as built)

```
surv/
├── docker-compose.yml
├── .env                          # single root .env for all services
├── .env.example
├── Dockerfile.mediamtx           # custom: MediaMTX + Python + kcat
├── Dockerfile.worker             # shared: snapshotter, status_monitor
├── Dockerfile.frontend           # multi-stage: Vite build → Nginx serve
├── mediamtx/
│   └── mediamtx.yml
├── nginx/
│   ├── nginx.conf
│   ├── empty.conf                # ⚠️ REQUIRED: neutralizes stock default.conf
│   └── conf.d/
│       ├── hls.conf              # HLS proxy with redirect rewrite
│       └── frontend.conf         # React SPA with /api proxy
├── kong/
│   └── setup-kong-jwt.sh
├── scripts/                      # MediaMTX hook scripts
│   ├── camera_ready.sh
│   ├── camera_down.sh
│   └── notify_segment.sh
├── workers/
│   ├── upload_to_minio.py        # called by notify_segment.sh hook
│   ├── snapshot_worker.py
│   ├── status_monitor.py
│   └── requirements.txt
├── onvif_producer/
│   ├── onvif_motion_producer.py
│   ├── Dockerfile
│   └── requirements.txt
├── motion_consumer/
│   ├── motion_event_consumer.py
│   ├── Dockerfile
│   └── requirements.txt
├── app/                          # FastAPI application
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       ├── 0001_initial.py   # camera, motion_event, video_segment tables
│   │       └── 0002_add_users.py # survapp_user table
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── camera.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── camera.py
│   │   ├── motion.py
│   │   ├── recording.py
│   │   └── auth.py
│   ├── routers/
│   │   ├── health.py
│   │   ├── cameras.py
│   │   ├── streams.py
│   │   ├── recordings.py
│   │   ├── motion.py
│   │   ├── auth.py
│   │   └── stream_auth.py        # MediaMTX webhook endpoint
│   ├── services/
│   │   ├── minio_service.py
│   │   ├── mediamtx_service.py
│   │   └── auth_service.py       # single source for JWT + password hashing
│   ├── dependencies/
│   │   └── auth.py               # get_current_user, require_admin
│   └── workers/
│       └── segment_db_consumer.py
├── frontend/                     # React + Vite + Tailwind v4
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── .env
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css             # @import "tailwindcss" + @theme {}
│       ├── api/client.ts
│       ├── hooks/usePolling.ts
│       ├── components/
│       │   ├── Sidebar.tsx
│       │   ├── HLSPlayer.tsx
│       │   ├── Timeline.tsx
│       │   ├── StatusBadge.tsx
│       │   └── ProtectedRoute.tsx
│       └── pages/
│           ├── Login.tsx
│           ├── LiveView.tsx
│           ├── Playback.tsx
│           ├── MotionEvents.tsx
│           ├── Cameras.tsx
│           └── Users.tsx
└── recordings/                   # bind mount for MediaMTX
```

### Root `.env` (single file for all services)

```ini
# ── PostgreSQL ────────────────────────────────────────────────────
POSTGRES_USER=surv
POSTGRES_PASSWORD=changeme
POSTGRES_DB=sarvanetra
POSTGRES_PORT=5432

# Sync URL for workers, Alembic, motion_consumer, onvif_producer
DATABASE_URL=postgresql://surv:changeme@postgres:5432/sarvanetra
SYNC_DATABASE_URL=postgresql://surv:changeme@postgres:5432/sarvanetra

# ── Redis ─────────────────────────────────────────────────────────
REDIS_PORT=6379

# ── MinIO ─────────────────────────────────────────────────────────
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=changeme123
MINIO_ENDPOINT=minio:9000
# External URL = VM IP — used for presigned URLs opened by browser
MINIO_EXTERNAL_URL=http://10.44.0.209:9000
MINIO_BUCKET_RECORDINGS=recordings
MINIO_BUCKET_SNAPSHOTS=snapshots

# ── Kafka ─────────────────────────────────────────────────────────
KAFKA_PORT=9092
KAFKA_UI_PORT=8090
# Must match KAFKA_ADVERTISED_LISTENERS — uses container name, not "kafka"
KAFKA_BOOTSTRAP_SERVERS=surv_kafka:9092

# ── MediaMTX ──────────────────────────────────────────────────────
MEDIAMTX_RTSP_PORT=8554
MEDIAMTX_HLS_PORT=8888
MEDIAMTX_WEBRTC_PORT=8889
MEDIAMTX_API_PORT=9997
SEGMENT_DURATION_SECONDS=60
MEDIAMTX_API_URL=http://mediamtx:9997
# These are returned to the browser — must use VM IP
MEDIAMTX_HLS_BASE=http://10.44.0.209:8080/hls
MEDIAMTX_WEBRTC_BASE=http://10.44.0.209:8889

# ── ONVIF ─────────────────────────────────────────────────────────
ONVIF_USERNAME=admin
ONVIF_PASSWORD=admin
ONVIF_PORT=80
CAMERA_PATHS=CAMKRTVM00001

# ── FastAPI ───────────────────────────────────────────────────────
# Generate: python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=replace-with-64-char-hex

# ── Kong JWT ──────────────────────────────────────────────────────
# kong_jwt_issuer = the "key" field of the Kong consumer JWT credential
# kong_jwt_secret = the "secret" field — must match FastAPI's signing secret
KONG_PROXY_PORT=8000
KONG_PROXY_SSL_PORT=8443
KONG_ADMIN_PORT=8001
KONG_JWT_ISSUER=sarvanetra-app
KONG_JWT_SECRET=replace-with-64-char-hex-same-as-secret-key

ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
DEBUG=false

# ── Frontend (baked into Vite bundle at build time) ───────────────
# Kong on :8000 is the single entry: /api → FastAPI, /hls → nginx_hls
VITE_API_BASE_URL=http://10.44.0.209:8000/api/v1
VITE_HLS_BASE=http://10.44.0.209:8000/hls
VITE_WEBRTC_BASE=http://10.44.0.209:8889
```

### ⚠️ Critical: Kafka Container Name

The Kafka container is named `surv_kafka` (set via `container_name: surv_kafka` in compose). The `KAFKA_ADVERTISED_LISTENERS` must use `surv_kafka:9092`, not `kafka:9092`. Every service that connects to Kafka must use `surv_kafka:9092`. This caused silent failures in `kafka_ui`, `onvif_producer`, `motion_consumer`, and `segment_db_consumer` when left as `kafka:9092`.

### Phase 0 — Definition of Done

- [x] Directory structure created
- [x] `.env` populated, in `.gitignore`
- [x] `docker compose up -d postgres redis` starts cleanly
- [x] `pg_isready` returns `accepting connections`
- [x] `redis-cli ping` returns `PONG`
- [x] No port conflicts on host

---

## Phase 1 — Camera Ingestion with MediaMTX

**Status: ✅ COMPLETE**

### What Changed from the Original Plan

**Custom Dockerfile required.** MediaMTX's official image has no Python or `kcat`. Since MediaMTX calls shell scripts (`camera_ready.sh`, `notify_segment.sh`) which in turn call `python3 upload_to_minio.py` and `kcat` for Kafka publishing, a custom `Dockerfile.mediamtx` is needed:

```dockerfile
FROM bluenviron/mediamtx:latest AS mediamtx
FROM python:3.12-slim

COPY --from=mediamtx /mediamtx /mediamtx

RUN apt-get update && apt-get install -y --no-install-recommends \
    kcat curl && rm -rf /var/lib/apt/lists/*

COPY workers/requirements.txt /tmp/worker-requirements.txt
RUN pip install --no-cache-dir -r /tmp/worker-requirements.txt

WORKDIR /
EXPOSE 8554 8888 8889 8189 9997 1935
ENTRYPOINT ["/mediamtx"]
CMD ["/mediamtx.yml"]
```

**Recording uses `runOnRecordSegmentComplete` hook, not a polling worker.** The original plan described a polling upload worker. The actual implementation uses MediaMTX's built-in hook:

```yaml
# mediamtx.yml
pathDefaults:
  record: true
  recordPath: /recordings/%path/%Y/%m/%d/%H-%M-%S-%f
  recordFormat: fmp4
  recordSegmentDuration: 60s
  runOnRecordSegmentComplete: /scripts/notify_segment.sh
```

`notify_segment.sh` calls `python3 /app/upload_to_minio.py "$MTX_SEGMENT_PATH"` directly — no polling, no race condition, no `STABILITY_WAIT` needed.

**Authentication set to `http` mode (not `internal`) in Phase 7.** Initially `authMethod: internal` with open permissions. Updated in Phase 7 to:

```yaml
authMethod: http
authHTTPAddress: http://app:8000/api/v1/auth/stream
authHTTPExclude:
  - action: api
  - action: metrics
  - action: pprof
```

### Camera Configuration (actual camera)

```yaml
# mediamtx.yml paths section
paths:
  CAMKRTVM00001:
    source: rtsp://admin:admin@10.44.0.219:554/unicaststream/1
    sourceProtocol: tcp
```

### nginx/conf.d/hls.conf — Final Working Version

The Nginx HLS proxy required four iterations to get right. The final working config:

```nginx
server {
    listen 80;
    server_name _;

    location /health {
        return 200 "ok\n";
        add_header Content-Type text/plain;
    }

    location /hls/ {
        proxy_pass         http://mediamtx:8888/;
        proxy_http_version 1.1;
        # $http_host preserves port — $host strips it, breaking the redirect
        proxy_set_header   Host $http_host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;

        # MediaMTX 302 cookie-check redirect emits a bare "/" relative Location.
        # Nginx would re-absolutize it using $host (no port) → browser hits :80.
        # This rewrite produces a fully-qualified absolute URL so Nginx has
        # nothing left to resolve — port is preserved from $http_host.
        proxy_redirect / $scheme://$http_host/hls/;

        # Strip MediaMTX's CORS headers — nginx adds its own below.
        # Without this, two Access-Control-Allow-Origin headers are sent,
        # which browsers reject as a CORS violation.
        proxy_hide_header Access-Control-Allow-Origin;
        proxy_hide_header Access-Control-Allow-Credentials;
        proxy_hide_header Access-Control-Allow-Methods;
        proxy_hide_header Access-Control-Allow-Headers;

        proxy_pass_header Set-Cookie;

        add_header Access-Control-Allow-Origin  * always;
        add_header Access-Control-Allow-Methods "GET, OPTIONS" always;
        add_header Cache-Control                "no-cache, no-store" always;

        types {
            application/vnd.apple.mpegurl m3u8;
            video/mp2t                    ts;
            video/mp4                     mp4;
        }
    }

    location /snapshots/ {
        proxy_pass       http://minio:9000/snapshots/;
        proxy_set_header Host $host;
    }
}
```

### nginx_hls Docker Compose Service (final)

```yaml
  nginx_hls:
    image: nginx:1.27-alpine
    container_name: surv_nginx_hls
    restart: unless-stopped
    networks: [surv_net]
    ports:
      - "8080:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d/hls.conf:/etc/nginx/conf.d/hls.conf:ro
      # ⚠️ REQUIRED: neutralize the stock default.conf baked into nginx:alpine
      # Without this, requests fall through to default.conf's location /,
      # which tries to serve files from /usr/share/nginx/html — giving 404
      # for every HLS request instead of proxying to MediaMTX.
      - ./nginx/empty.conf:/etc/nginx/conf.d/default.conf:ro
      - hls_segments:/var/hls:ro
    depends_on:
      - mediamtx
```

`nginx/empty.conf` is a file containing only a comment — it overrides the stock `default.conf` to prevent it intercepting requests.

### Phase 1 — Definition of Done

- [x] MediaMTX container starts and logs `listener opened on :8554`
- [x] Nginx starts and `curl http://10.44.0.209:8080/health` returns `ok`
- [x] `curl -v -L -c /tmp/c.txt -b /tmp/c.txt http://10.44.0.209:8080/hls/CAMKRTVM00001/index.m3u8` returns `#EXTM3U`
- [x] Stream plays in browser
- [x] MediaMTX API `GET /v3/paths/list` shows `CAMKRTVM00001` with `"ready":true`
- [x] Recording files appear in `./recordings/CAMKRTVM00001/YYYY/MM/DD/`

---

## Phase 2 — Object Storage with MinIO

**Status: ✅ COMPLETE**

### What Changed from the Original Plan

**Two separate MinIO clients in use.** The `upload_to_minio.py` worker uses the official `minio` Python SDK (`Minio` class). The FastAPI app uses `boto3` (S3-compatible). Both work — they just use different client libraries for different purposes.

**`MINIO_EXTERNAL_URL` is the critical env var for presigned URLs.** Internal workers use `minio:9000`. Presigned URLs generated for the browser must use `http://10.44.0.209:9000` (the VM's external IP), otherwise the browser tries to open `http://minio:9000/...` which doesn't resolve from outside the Docker network.

### Phase 2 — Definition of Done

- [x] MinIO healthy: `curl http://localhost:9000/minio/health/live` returns 200
- [x] `recordings` and `snapshots` buckets created by `minio_init`
- [x] Presigned URLs use `MINIO_EXTERNAL_URL` (VM IP), not internal `minio:9000`
- [x] MinIO console at `http://10.44.0.209:9001`

---

## Phase 3 — Recording Pipeline

**Status: ✅ COMPLETE**

### What Changed from the Original Plan

**`runOnRecordSegmentComplete` hook instead of polling worker.** This eliminates the race condition described in Known Risk #9. MediaMTX calls the hook script exactly when a segment file is fully written and closed:

```
MediaMTX finishes segment
  → runOnRecordSegmentComplete: /scripts/notify_segment.sh
    → notify_segment.sh calls: python3 /app/upload_to_minio.py "$MTX_SEGMENT_PATH"
      → upload_to_minio.py uploads to MinIO
      → uploads JSON sidecar metadata file alongside the .mp4
      → publishes event to Kafka `recording.segments` topic
```

**Segment naming format (actual):**
```
/recordings/CAMKRTVM00001/2026/06/30/08-33-26-438496.mp4
```

`upload_to_minio.py` parses the timestamp from this path structure (not from the filename stem alone).

**Kafka event published for each segment:**
```json
{
  "schema_version": "1.0",
  "event_type": "recording.segment.uploaded",
  "camera_path": "CAMKRTVM00001",
  "object_key": "CAMKRTVM00001/2026/06/30/08-33-26-438496.mp4",
  "bucket": "recordings",
  "segment_start_utc": "2026-06-30T08:33:26.438496+00:00",
  "segment_end_utc": "2026-06-30T08:34:26.438496+00:00",
  "duration_seconds": 60,
  "file_size_bytes": 8388608,
  "uploaded_at": "2026-06-30T08:34:28.123Z"
}
```

### Phase 3 — Definition of Done

- [x] MediaMTX creates segments in `/recordings/<path>/<Y>/<m>/<d>/` structure
- [x] Hook fires on segment completion — confirmed in mediamtx logs
- [x] Segments appear in MinIO `recordings` bucket within ~5s of completion
- [x] JSON sidecar metadata uploaded alongside each `.mp4`
- [x] Kafka `recording.segments` topic receives events

---

## Phase 4 — Kafka Event Bus

**Status: ✅ COMPLETE**

### What Changed from the Original Plan

**Used `apache/kafka:3.7.0` instead of `bitnami/kafka`.** KRaft mode config differs slightly between the two images.

**Container name `surv_kafka` — not `kafka`.** This is the single most important operational note from this phase. `KAFKA_ADVERTISED_LISTENERS` must use the container name:

```yaml
  kafka:
    image: apache/kafka:3.7.0
    container_name: surv_kafka      # ← must match advertised listener
    environment:
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://surv_kafka:9092
```

Every service connecting to Kafka uses `surv_kafka:9092` in its env, not `kafka:9092`.

**Broker version auto-detected as `2.6.0`.** The `apache/kafka:3.7.0` image's broker identifies itself as `2.6.0` during the `kafka-python-ng` handshake. Do not hardcode `api_version=(3, 7, 0)` in consumers — let it auto-detect.

**`kafka-python-ng` instead of `kafka-python`.** Drop-in replacement with the same API, better maintained. All consumers use this.

### Phase 4 — Definition of Done

- [x] Kafka healthy: topic list command returns without error
- [x] Topics `camera.motion`, `camera.status`, `recording.segments` created by `kafka_init`
- [x] Kafka UI accessible at `http://10.44.0.209:8090`
- [x] Test produce/consume works on each topic

---

## Phase 5 — Motion Detection Pipeline (ONVIF)

**Status: ✅ COMPLETE**

### What Changed from the Original Plan

**`KafkaConsumer.subscribe()` does not support `on_assign`/`on_revoke` callbacks in `kafka-python-ng`.** This is a `confluent-kafka` API. The fix: pass the topic directly to the `KafkaConsumer` constructor instead:

```python
# WRONG — kafka-python-ng doesn't support these kwargs
consumer.subscribe(
    ["camera.motion"],
    on_assign=lambda c, ps: ...,
    on_revoke=lambda c, ps: ...,
)

# CORRECT
consumer = KafkaConsumer(
    "camera.motion",              # topic in constructor
    bootstrap_servers=KAFKA_BOOTSTRAP,
    group_id=KAFKA_GROUP_ID,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    max_poll_interval_ms=300000,
    # api_version intentionally omitted — let broker auto-detect
)
```

**Matrix COMSEC camera sends `State` not `IsMotion`.** The ONVIF producer parses:
```python
for item in elem.findall('.//tt:SimpleItem', NS):
    if item.get('Name') == 'State':
        return item.get('Value', '').lower() == 'true'
```

**ONVIF subscription renewal implemented.** Subscriptions are renewed at 50 minutes (before the 60-minute expiry) to prevent silent motion detection gaps.

**`psycopg2-binary` required in worker images.** The `status_monitor.py` uses `psycopg2`. Add to `workers/requirements.txt`:
```
psycopg2-binary>=2.9
```

**Stale `cam_001` row caused recurring `[API] path not found` errors.** A test camera row (`cam_id='cam_001'`) was inserted during Phase 5 testing. The `status_monitor` polled MediaMTX for this path every 30 seconds, got `404`, and logged `ERR [API] path not found`. Fix: deactivate via API:
```bash
curl -X DELETE http://10.44.0.209:8000/api/v1/cameras/cam_001
```
Cannot hard-delete if `survapp_motion_event` rows reference it (FK constraint) — deactivate instead.

**`status_monitor.py` requires `psycopg2-binary`, `requests`, `kafka-python-ng`** — ensure all are in `workers/requirements.txt`.

### Phase 5 — Definition of Done

- [x] ONVIF producer connects to `CAMKRTVM00001` and creates pull-point subscription
- [x] Motion start event appears in `camera.motion` Kafka topic
- [x] Motion consumer creates `survapp_motion_event` row with `is_active=true`
- [x] Motion end event updates row: `motion_end` set, `is_active=false`
- [x] Status monitor publishes `camera.online`/`camera.offline` on transition
- [x] `survapp_camera_master.is_online` and `last_seen` update correctly
- [x] No `[API] path not found` errors in MediaMTX logs for active cameras

---

## Phase 6 — FastAPI Integration Layer

**Status: ✅ COMPLETE**

### What Changed from the Original Plan

**FastAPI only — Django not used.** Fresh system, no legacy Django code.

**Dockerfile uses `/code` workdir pattern, not `/app`:**

```dockerfile
FROM python:3.12-slim
WORKDIR /code
COPY app/requirements.txt /code/
RUN pip install --no-cache-dir -r /code/requirements.txt
COPY app/ /code/app/
ENV PYTHONPATH=/code
WORKDIR /code/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

This means:
- Alembic runs from `/code/app/` — `alembic.ini` and `alembic/` must be at `/code/app/alembic`
- Import paths use `app.` prefix: `from app.config import settings`

**Two database URLs required in env:**
- `DATABASE_URL=postgresql+asyncpg://...` — FastAPI's async SQLAlchemy engine
- `SYNC_DATABASE_URL=postgresql://...` — Alembic migrations and sync workers

**Alembic migration workflow:**

```bash
# Always rebuild before running migrations after adding a new migration file
docker compose build app
docker compose run --rm db_migrate
```

If the build cache doesn't pick up a new migration file, copy it directly:
```bash
docker compose run -d --name tmp_migrate app sleep 60
docker cp app/alembic/versions/0002_add_users.py tmp_migrate:/code/app/alembic/versions/
docker exec tmp_migrate alembic upgrade head
docker rm -f tmp_migrate
```

**FastAPI `app` service no longer exposes port 8000 to the host in Phase 7.** Kong owns `:8000`. FastAPI is only reachable inside the Docker network as `http://app:8000`.

### app/config.py (key settings)

```python
class Settings(BaseSettings):
    database_url: str           # postgresql+asyncpg://...
    sync_database_url: str      # postgresql://...
    minio_endpoint: str         # minio:9000 (internal)
    minio_external_url: str     # http://10.44.0.209:9000 (for presigned URLs)
    mediamtx_api_url: str       # http://mediamtx:9997 (internal)
    mediamtx_hls_base: str      # http://10.44.0.209:8080/hls (external, for browser)
    kafka_bootstrap_servers: str  # surv_kafka:9092
    kong_jwt_issuer: str        # must match Kong consumer credential "key"
    kong_jwt_secret: str        # must match Kong consumer credential "secret"
```

### API Endpoints (as built)

```
# Open (no auth required — on Kong's open route)
POST   /api/v1/auth/login
POST   /api/v1/auth/stream          ← MediaMTX webhook, internal only
GET    /health
GET    /api/v1/health/

# Protected (require Bearer token via Kong JWT plugin)
GET    /api/v1/health/services
GET    /api/v1/cameras/
POST   /api/v1/cameras/             ← admin only
GET    /api/v1/cameras/{cam_id}
PATCH  /api/v1/cameras/{cam_id}     ← admin only
DELETE /api/v1/cameras/{cam_id}     ← admin only
GET    /api/v1/streams/{cam_id}/hls-url     ← returns token-embedded URL
GET    /api/v1/streams/{cam_id}/webrtc-url
GET    /api/v1/streams/{cam_id}/snapshot-url
GET    /api/v1/recordings/{cam_id}/timeline?date=YYYY-MM-DD
GET    /api/v1/recordings/{cam_id}/download?object_key=...
GET    /api/v1/motion/
GET    /api/v1/motion/active
GET    /api/v1/motion/{event_id}
GET    /api/v1/auth/me
POST   /api/v1/auth/users           ← admin only
GET    /api/v1/auth/users           ← admin only
```

### Database Tables (as built)

```sql
survapp_camera_master     -- camera registry
survapp_motion_event      -- ONVIF motion events
survapp_video_segment     -- recording segment index (populated by Kafka consumer)
survapp_user              -- operator/admin accounts (added in Phase 7)
```

### app/requirements.txt

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
psycopg2-binary==2.9.9
alembic==1.13.1
greenlet==3.0.3
pydantic==2.7.1
pydantic-settings==2.2.1
python-dotenv==1.0.1
boto3==1.34.69
kafka-python-ng==2.2.3
requests==2.31.0
httpx==0.27.0
python-multipart==0.0.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

### Phase 6 — Definition of Done

- [x] `curl http://10.44.0.209:8000/health` returns `{"status":"ok"}`
- [x] Swagger at `http://10.44.0.209:8000/docs`
- [x] `POST /api/v1/cameras/` creates camera, appears in DB
- [x] `GET /api/v1/streams/CAMKRTVM00001/hls-url` returns URL
- [x] `GET /api/v1/recordings/CAMKRTVM00001/timeline?date=...` returns segments
- [x] `GET /api/v1/motion/` returns motion events
- [x] `survapp_video_segment` table populated by `segment_db_consumer`

---

## Phase 7 — Authentication & API Gateway (Kong + JWT)

**Status: ✅ COMPLETE**

### Architecture Decision

Kong validates JWT tokens but does NOT issue them. FastAPI's `/auth/login` endpoint issues tokens. The token's `iss` claim must match the Kong consumer's `key` field, and the signing secret must match the consumer's `secret`. Both are set from the same env vars: `KONG_JWT_ISSUER` and `KONG_JWT_SECRET`.

### Critical: JWT Secret Wiring

```
KONG_JWT_ISSUER=sarvanetra-app      (= JWT "iss" claim = Kong consumer credential "key")
KONG_JWT_SECRET=<64-char-hex>       (= JWT signing secret = Kong consumer credential "secret")
```

Both FastAPI (`auth_service.py`) and Kong (`setup-kong-jwt.sh`) read these same env vars. This is the single source of truth — never hardcode either value.

### Kong Route Structure

Two sets of routes to the same FastAPI service:

**1. Protected route** (`api-route`, path `/api`):
- JWT plugin enabled
- All requests require `Authorization: Bearer <token>`

**2. Open route** (`auth-open-route`, paths `/api/v1/auth/login`, `/api/v1/auth/stream`, `/health`, `/api/v1/health`):
- No JWT plugin
- Login endpoint must be open (chicken-and-egg: can't get a token if the login route requires a token)
- `/api/v1/auth/stream` must be open because MediaMTX calls it internally with no auth header

### Kong JWT Plugin on HLS Route

```bash
curl -X POST "$KONG_ADMIN/routes/hls-route/plugins" \
  -d "name=jwt" \
  -d "config.claims_to_verify=exp" \
  -d "config.uri_param_names=token" \
  -d "config.cookie_names=jwt"
```

The `uri_param_names=token` config tells Kong to also accept the JWT as `?token=<jwt>` in the URL — used by the stream URL generated by `GET /api/v1/streams/{cam_id}/hls-url`.

### Stream Token Flow

```
1. Frontend logs in → gets access_token
2. Frontend calls GET /api/v1/streams/CAMKRTVM00001/hls-url (with Bearer token)
3. FastAPI generates a short-lived (1hr) stream token scoped to that camera path
4. FastAPI returns: {"hls_url": "http://.../hls/CAMKRTVM00001/index.m3u8?token=<jwt>"}
5. HLS.js loads that URL → Kong's JWT plugin validates ?token= → proxies to nginx_hls
6. nginx_hls proxies to MediaMTX
7. MediaMTX calls FastAPI /api/v1/auth/stream webhook to validate the token per-request
```

### FastAPI Port Change

After adding Kong, FastAPI's port `8000` must NOT be published to the host — Kong owns `:8000`. Remove the `ports:` section from the `app` service:

```yaml
  app:
    # NO ports: section — Kong proxies to http://app:8000 internally
    networks:
      - surv_net
```

### First Admin User Bootstrap

No UI exists for the very first user. Create it directly:

```bash
# Get the password hash
docker compose exec app python3 -c "
from app.services.auth_service import hash_password
print(hash_password('your-password'))
"

# Insert the admin user
docker compose exec postgres psql -U surv -d sarvanetra -c "
INSERT INTO survapp_user (username, password_hash, role, is_active)
VALUES ('admin', '<paste-hash-here>', 'admin', true);
"
```

Subsequent users are created via `POST /api/v1/auth/users` (admin-only endpoint).

### Phase 7 — Definition of Done

- [x] Kong starts, `GET http://10.44.0.209:8001/status` returns healthy
- [x] `GET http://10.44.0.209:8000/api/v1/cameras/` without token returns 401
- [x] `POST http://10.44.0.209:8000/api/v1/auth/login` returns access_token
- [x] `GET http://10.44.0.209:8000/api/v1/cameras/` with valid token returns camera list
- [x] Expired/invalid token returns 401
- [x] HLS URL from stream endpoint contains `?token=` param
- [x] MediaMTX auth webhook validates stream tokens correctly
- [x] Konga accessible at `http://10.44.0.209:1337`

---

## Phase 8 — Frontend (React + Vite + Tailwind v4)

**Status: ✅ COMPLETE** (built before Phase 7 was complete, then updated)

### Technology Stack (actual)

- **React 18** + **TypeScript**
- **Vite 5** with `@tailwindcss/vite` plugin (no PostCSS config needed)
- **Tailwind CSS v4** — completely different from v3
- **TanStack Query v5** for data fetching and polling
- **React Router v6**
- **HLS.js** for live stream playback
- **date-fns** for timestamp formatting
- **lucide-react** for icons

### Tailwind v4 Key Differences from v3

| v3 | v4 |
|---|---|
| `@tailwind base/components/utilities` | `@import "tailwindcss"` |
| `tailwind.config.ts` with `theme.extend` | `@theme {}` block in CSS |
| PostCSS plugin | `@tailwindcss/vite` Vite plugin |
| `content: [...]` array | Auto content detection |
| Custom animations in config | `@keyframes` inside `@theme {}` |

**`src/index.css` structure (v4):**
```css
@import "tailwindcss";

@theme {
  --color-surface:  #080C10;
  --color-panel:    #0E1420;
  --color-border:   #1C2333;
  --color-accent:   #3B82F6;
  --color-online:   #22C55E;
  --color-alert:    #EF4444;
  --color-muted:    #64748B;
  --color-dim:      #374151;
  --font-sans: "Inter", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", monospace;

  @keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.35; }
  }
  @keyframes fade-in {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
  }
}
```

**`vite.config.ts` (v4 — no postcss.config.js needed):**
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

### Frontend `.env`

```ini
# Kong on :8000 routes /api → FastAPI, /hls → nginx_hls
VITE_API_BASE_URL=http://10.44.0.209:8000/api/v1
VITE_HLS_BASE=http://10.44.0.209:8000/hls
VITE_WEBRTC_BASE=http://10.44.0.209:8889
```

**⚠️ VITE_ vars are baked at build time.** Changing `.env` requires `docker compose build --no-cache frontend` — a container restart is not enough.

### Pages Built

| Page | Route | Auth required |
|---|---|---|
| Login | `/login` | No |
| Live View | `/` | Yes |
| Playback (DVR) | `/playback` | Yes |
| Motion Alerts | `/motion` | Yes |
| Cameras | `/cameras` | Yes (write: admin only) |
| Users | `/users` | Yes (admin only) |

### HLS Playback in Browser — Stream Token Pattern

LiveView fetches a per-camera token-embedded URL instead of constructing the URL client-side:

```typescript
// Per camera, fetch a token-embedded HLS URL from FastAPI
const { data: stream } = useQuery({
  queryKey: ['hls-url', cam.cam_id],
  queryFn:  () => fetchHlsUrl(cam.cam_id),   // GET /api/v1/streams/{cam_id}/hls-url
  enabled:  cam.is_online,
  staleTime: 50 * 60 * 1000,    // refresh before 1hr token expiry
  refetchInterval: 50 * 60 * 1000,
})
// stream.hls_url = "http://10.44.0.209:8000/hls/CAMKRTVM00001/index.m3u8?token=<jwt>"
```

### Phase 8 — Definition of Done

- [x] Frontend accessible at `http://10.44.0.209:3000`
- [x] Login page redirects unauthenticated users
- [x] Live View shows camera with LIVE badge when streaming
- [x] Playback timeline renders segments, click-to-seek works
- [x] Motion alerts table shows events with camera info and timestamps
- [x] Cameras page shows registered cameras with online status
- [x] Logout clears token and redirects to login
- [x] Admin users see "Add camera" and delete buttons; operators do not

---

## Phase 9 — Camera Health Monitoring

**Status: 🔲 NOT STARTED**

Pending. `status_monitor.py` is running (from Phase 5) and updating `is_online`/`last_seen`. The Phase 9 work remaining:
- `CameraStatusLog` table for historical uptime
- `/api/v1/health/cameras/` endpoint with offline duration
- FCM push notifications for cameras offline >5 minutes
- Health dashboard page in frontend

---

## Phase 10 — Retention, Cleanup & Storage Governance

**Status: 🔲 NOT STARTED**

`workers/minio_cleaner.py` exists in the original plan but has not been built or deployed. MinIO lifecycle policy not yet applied.

---

## Phase 11 — Hardening, Security & Production Readiness

**Status: 🔲 NOT STARTED**

Key items pending:
- TLS (Kong HTTPS, RTSPS for cameras) — required to fix `Secure` cookie issue with HLS session cookies
- Non-root users in all Dockerfiles
- `CORS_ALLOW_ALL_ORIGINS` restricted to frontend origin
- MinIO IAM policies instead of root credentials
- Kafka SASL/SCRAM
- `DEBUG=false` validation

---

## Real-World Bugs & Fixes Log

This section documents every significant bug encountered during the build and the exact fix applied.

---

### BUG-01: `kafka-python` `subscribe()` rejects `on_assign`/`on_revoke`

**Phase:** 5  
**Symptom:** `TypeError: KafkaConsumer.subscribe() got an unexpected keyword argument 'on_assign'`  
**Cause:** These callbacks exist in `confluent-kafka`, not in `kafka-python`/`kafka-python-ng`.  
**Fix:** Pass the topic to the `KafkaConsumer` constructor instead of calling `subscribe()`:
```python
consumer = KafkaConsumer("camera.motion", bootstrap_servers=..., ...)
# NOT: consumer.subscribe(["camera.motion"], on_assign=..., on_revoke=...)
```

---

### BUG-02: `kafka_ui` shows no brokers

**Phase:** 4  
**Symptom:** Kafka UI at `:8090` connects but shows empty broker list  
**Cause:** `KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092` — wrong container name  
**Fix:** `KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: surv_kafka:9092`

---

### BUG-03: `status_monitor` — `ModuleNotFoundError: No module named 'psycopg2'`

**Phase:** 5  
**Symptom:** `surv_status_monitor` exits immediately  
**Cause:** `psycopg2-binary` not in `workers/requirements.txt`  
**Fix:** Add to `workers/requirements.txt`: `psycopg2-binary>=2.9`

---

### BUG-04: `[API] path not found` recurring in MediaMTX logs

**Phase:** 5/6  
**Symptom:** Every 30 seconds: `ERR [API] path not found` in `surv_mediamtx` logs  
**Cause:** `survapp_camera_master` had a test row with `cam_id='cam_001'` from Phase 5 testing. `status_monitor` polled `GET /v3/paths/get/cam_001` which doesn't exist in MediaMTX.  
**Fix:** Deactivate the stale row:
```bash
curl -X DELETE http://10.44.0.209:8000/api/v1/cameras/cam_001
```
Cannot hard-delete due to FK constraint from `survapp_motion_event` — soft-delete with `is_active=false` is correct.

---

### BUG-05: Alembic migration fails — `Can't locate revision identified by '0002'`

**Phase:** 7  
**Symptom:** `docker compose run --rm db_migrate` fails even though `0002_add_users.py` exists on disk  
**Cause:** Docker build cache served the old `COPY app/ /code/app/` layer — the new file was not included in the image  
**Fix (temporary):** Copy file directly into a running container:
```bash
docker compose run -d --name tmp_migrate app sleep 60
docker cp app/alembic/versions/0002_add_users.py \
  tmp_migrate:/code/app/alembic/versions/0002_add_users.py
docker exec tmp_migrate alembic upgrade head
docker rm -f tmp_migrate
```
**Fix (permanent):** After adding any new file to `app/`, always run `docker compose build --no-cache app` before `db_migrate`.

---

### BUG-06: HLS proxy returns 404 — Nginx serves static files instead of proxying

**Phase:** 8  
**Symptom:** `curl http://10.44.0.209:8080/hls/CAMKRTVM00001/index.m3u8` returns 404 with `Server: nginx/1.27.5`  
**Cause:** The `nginx:1.27-alpine` image ships with a `default.conf` that has `location /` serving from `/usr/share/nginx/html`. This catches all requests before `hls.conf`'s `location /hls/` block.  
**Fix:** Mount an empty file over `default.conf`:
```yaml
volumes:
  - ./nginx/empty.conf:/etc/nginx/conf.d/default.conf:ro
```

---

### BUG-07: HLS redirect Location header missing port (302 → port 80)

**Phase:** 8  
**Symptom:** MediaMTX's 302 cookie-check redirect results in browser trying port 80 instead of 8080  
**Cause:** `proxy_redirect / /hls/` rewrites the path but when Nginx re-absolutizes the resulting relative URL, it uses `$host` (no port) not `$http_host` (with port).  
**Fix:** Produce a fully-qualified absolute URL so Nginx has nothing to re-absolutize:
```nginx
proxy_redirect / $scheme://$http_host/hls/;
```

---

### BUG-08: CORS error in browser — duplicate `Access-Control-Allow-Origin` headers

**Phase:** 8  
**Symptom:** Browser DevTools shows CORS error. Response has two `Access-Control-Allow-Origin` headers.  
**Cause:** MediaMTX echoes back the request's `Origin` as its own `Access-Control-Allow-Origin: http://10.44.0.209:3000`. Nginx then adds its own `add_header Access-Control-Allow-Origin *`. Two ACAO headers = browsers reject as CORS violation.  
**Fix:** Strip MediaMTX's CORS headers before Nginx adds its own:
```nginx
proxy_hide_header Access-Control-Allow-Origin;
proxy_hide_header Access-Control-Allow-Credentials;
proxy_hide_header Access-Control-Allow-Methods;
proxy_hide_header Access-Control-Allow-Headers;
add_header Access-Control-Allow-Origin * always;
```

---

### BUG-09: `postgres: FATAL: database "surv" does not exist` in logs

**Phase:** 6+  
**Symptom:** Recurring FATAL error in `surv_postgres` logs  
**Cause:** A healthcheck or client is connecting without specifying `-d sarvanetra` — PostgreSQL defaults to opening a database matching the username (`surv`), which doesn't exist (the database is `sarvanetra`).  
**Impact:** None — the FastAPI app itself connects correctly. Pure log noise.  
**Fix:** Add `-d sarvanetra` to any `psql`/`pg_isready` calls in healthchecks, or ignore — it doesn't affect operation.

---

### BUG-10: Frontend build cache — VITE_ URL changes not picked up

**Phase:** 8  
**Symptom:** Frontend still uses old `localhost:8000` URL after changing `.env` and restarting container  
**Cause:** Vite bakes `VITE_*` env vars into the JS bundle at **build time**. Container restart doesn't re-run the build.  
**Fix:** Always rebuild after changing any `VITE_*` env var:
```bash
docker compose build --no-cache frontend
docker compose up -d frontend
```

---

## Quick Reference: Port Map & Service Inventory

| Service | Container Name | Internal Port | External Port | Purpose |
|---|---|---|---|---|
| PostgreSQL | surv_postgres | 5432 | 5432 | Primary DB |
| Redis | surv_redis | 6379 | 6379 | Cache |
| Kafka | surv_kafka | 9092, 9093 | 9092 | Event bus (KRaft) |
| Kafka UI | surv_kafka_ui | 8080 | 8090 | Topic browser |
| MinIO API | surv_minio | 9000 | 9000 | S3 object storage |
| MinIO Console | surv_minio | 9001 | 9001 | Admin UI |
| MediaMTX RTSP | surv_mediamtx | 8554 | 8554 | Camera ingest |
| MediaMTX HLS | surv_mediamtx | 8888 | 8888 | Direct HLS (debug) |
| MediaMTX WebRTC | surv_mediamtx | 8889 | 8889 | WebRTC |
| MediaMTX API | surv_mediamtx | 9997 | 9997 | Management API |
| Nginx HLS | surv_nginx_hls | 80 | 8080 | HLS proxy |
| FastAPI | surv_app | 8000 | — | App (Kong only) |
| Kong Proxy | surv_kong | 8000 | 8000 | API gateway |
| Kong Admin | surv_kong | 8001 | 8001 | Kong management |
| Konga | surv_konga | 1337 | 1337 | Kong admin UI |
| Frontend | surv_frontend | 80 | 3000 | React SPA |

### URLs from Dev PC (10.44.0.55)

| What | URL |
|---|---|
| React frontend | `http://10.44.0.209:3000` |
| FastAPI Swagger | `http://10.44.0.209:8000/docs` |
| FastAPI health | `http://10.44.0.209:8000/health` |
| Kong Admin | `http://10.44.0.209:8001` |
| Konga UI | `http://10.44.0.209:1337` |
| MinIO console | `http://10.44.0.209:9001` |
| Kafka UI | `http://10.44.0.209:8090` |
| HLS direct (debug) | `http://10.44.0.209:8888/CAMKRTVM00001/index.m3u8` |
| HLS via Nginx | `http://10.44.0.209:8080/hls/CAMKRTVM00001/index.m3u8` |
| MediaMTX API | `http://10.44.0.209:9997/v3/paths/list` |

### Startup Order

```
postgres (healthcheck) → redis
postgres (healthcheck) → kafka (healthcheck) → kafka_init → kafka_ui
postgres (healthcheck) → minio (healthcheck) → minio_init
minio (healthy) + kafka (healthy) → mediamtx → nginx_hls
postgres (healthy) + kafka (healthy) + minio (healthy) → app
app → db_migrate (one-off, must run before app starts serving)
postgres (healthy) → kong-db-init → kong-migration → kong (healthcheck) → kong-config → konga
kafka (healthy) + postgres (healthy) → onvif_producer
kafka (healthy) + postgres (healthy) → motion_consumer
kafka (healthy) + postgres (healthy) → segment_db_consumer
kafka (healthy) + postgres (healthy) + mediamtx → status_monitor
minio (healthy) + mediamtx → snapshotter
frontend → (after app, nginx_hls)
```

### Key Configuration Files by Phase

| Phase | Key Files | Status |
|---|---|---|
| 0 | `.env`, `docker-compose.yml` | ✅ |
| 1 | `Dockerfile.mediamtx`, `mediamtx/mediamtx.yml`, `nginx/conf.d/hls.conf`, `nginx/empty.conf` | ✅ |
| 2 | `workers/upload_to_minio.py`, MinIO in compose | ✅ |
| 3 | `scripts/notify_segment.sh`, `mediamtx.yml` recording paths | ✅ |
| 4 | Kafka in compose, `kafka_init` topics | ✅ |
| 5 | `onvif_producer/onvif_motion_producer.py`, `motion_consumer/motion_event_consumer.py`, `workers/status_monitor.py` | ✅ |
| 6 | `app/` (all FastAPI files), `app/alembic/versions/0001_initial.py` | ✅ |
| 7 | `app/alembic/versions/0002_add_users.py`, `app/services/auth_service.py`, `app/routers/auth.py`, `app/routers/stream_auth.py`, `kong/setup-kong-jwt.sh` | ✅ |
| 8 | `frontend/` (all React/Vite files), `Dockerfile.frontend`, `nginx/conf.d/frontend.conf` | ✅ |
| 9 | `app/routers/health.py` (expanded), `workers/notifier.py` | 🔲 |
| 10 | `workers/minio_cleaner.py`, MinIO lifecycle policy | 🔲 |
| 11 | TLS certs, hardened compose, non-root Dockerfiles | 🔲 |

---

*This document reflects the actual as-built state of Sarvanetra as of 2026-06-30. Every bug in the Real-World Bugs section was hit during implementation and resolved as documented. Use this as the ground truth for any rebuild, onboarding, or context handoff.*