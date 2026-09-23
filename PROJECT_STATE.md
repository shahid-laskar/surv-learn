# SARVANETRA — Current Project State
**Canonical Source of Truth: WHAT EXISTS NOW**  
**Repository Baseline:** Branch `dev` (Commit `8fa82fd`, Aug 3, 2026)  
**Verification Date:** September 22, 2026 (Post-Archaeology Verified)  

---

## 1. Executive Summary

SARVANETRA is an enterprise-grade, containerized Video Surveillance and Network Video Recorder (NVR) management platform developed for deployment across BSNL telecommunication networks and customer premises. The platform provides RTSP/ONVIF camera ingestion, live low-latency streaming (HLS and WebRTC), automated 24/7 and motion-triggered continuous recording into S3-compliant object storage, multi-tenant hierarchical access control (BSNL Circle → Business Area → SSA → Site), customer/site isolation, role-based access control (RBAC), camera health monitoring, and a fleet management control plane for distributed Edge NVR appliances.

The system is structured as a three-tier architecture:
1. **Central Hub (`surv/`):** The primary control plane, video ingestion hub for VLAN cameras, object storage repository, metadata database, event streaming cluster, API gateway, and administrative web application.
2. **Portable Edge NVR (`edge-nvr/`):** A standalone appliance stack designed to run on customer-premises hardware or remote branch VMs, providing local camera ingestion, on-premise recording retention, local motion detection, and automated heartbeat/configuration sync back to the Hub.
3. **Edge Simulation Suite (`edge-sim/`):** A Dockerized test harness simulating multi-site edge environments with synthetic FFmpeg video streams and automated motion injection.

### Primary Technology Stack

| Layer | Technologies in Active Code | Code Status & Usage Truth |
|---|---|---|
| **Backend Framework** | FastAPI 2.0.0, Python 3.12 (ASGI on Uvicorn), SQLAlchemy 2.0 (asyncpg + psycopg2), Alembic | Active core API service (`surv/app/`). |
| **Relational Database** | PostgreSQL 16 | Active primary store for metadata, RBAC, users, segments, and audit logs. |
| **In-Memory Store** | Redis 7 (Alpine) | **IDLE / UNUSED:** Service `surv_redis` runs in Docker Compose, but is NOT imported or utilized by backend code. Sessions are stored in PostgreSQL (`user_session`). |
| **Object Storage** | MinIO S3 (Buckets: `recordings`, `snapshots`, `backup_clips`) | Active storage for video chunks, JSON metadata sidecars, and backup clips. |
| **Media Server** | MediaMTX (bluenviron/mediamtx:latest-ffmpeg) | Active ingest engine for RTSP, RTSPS, RTMP, low-latency HLS, and WebRTC. |
| **API Gateway & Proxy** | Kong Gateway 3.6, Nginx 1.27 (HLS reverse proxy) | Kong validates JWT perimeter on `/api`; Nginx proxies HLS directly on port 8080. |
| **Event Bus** | Apache Kafka 3.7.0 (KRaft mode, 3 partitions: `camera.motion`, `camera.status`, `recording.segments`), Kafka UI | Active message bus coordinating motion events and recording ingestion. |
| **Networking & VPN** | Headscale (Alpine), Caddy 2 (TLS proxy), Tailscale client, fredliang/derper (DERP relay), dnsmasq | Deployed in Compose, manual peer connection; automated ACL sync is stubbed. |
| **Frontend Application** | React 18, TypeScript 5, Vite 5, Tailwind CSS v4, Lucide React, Hls.js | Active 13-page single-page application (`surv/frontend/`). |

---

## 2. Current Implementation Status

Features across the repository are classified according to actual code and configuration evidence:

* ✅ **IMPLEMENTED:** Fully coded, wired into the active runtime, and verified in codebase configuration.
* 🟡 **PARTIALLY IMPLEMENTED:** Implemented in code but lacks complete pipeline integration, relies on stubs, or requires manual steps.
* 🔴 **NOT IMPLEMENTED:** Documented or planned, but absent from the codebase.
* ⚠️ **BROKEN / NEEDS FIX:** Code exists but will fail at runtime due to missing dependencies, syntax, or configuration mismatch.
* ❓ **UNKNOWN / NEEDS VERIFICATION:** Code exists but requires live physical hardware or third-party connectivity to verify.
* 📄 **DOCUMENTED ONLY:** Feature exists purely in specification documents with no code present.

### Subsystem Status Matrix

| Subsystem | Feature | Status | Evidence (Files) | Notes |
|---|---|---|---|---|
| **Core Media** | RTSP Camera Ingest | ✅ IMPLEMENTED | `surv/mediamtx/mediamtx.yml`, `surv/app/services/mediamtx_client.py` | MediaMTX pulls RTSP feeds dynamically via REST API. |
| **Core Media** | RTSPS Ingest | ✅ IMPLEMENTED | `surv/app/services/mediamtx_client.py#L36-L67`, `0009_stream_protocol.py` | Secure RTSP pull with port 322 fallback and URL credentials. |
| **Core Media** | RTMP Push Ingest | ✅ IMPLEMENTED | `surv/app/services/mediamtx_client.py#L68-L77`, `surv/mediamtx/mediamtx.yml#L34-L38` | Sets `source: "publisher"` on port 1935 for external RTMP encoders. |
| **Core Media** | Low-Latency HLS Delivery | ✅ IMPLEMENTED | `surv/nginx/conf.d/hls.conf`, `surv/frontend/src/components/HLSPlayer.tsx` | fMP4 1s segments with 200ms parts proxied via Nginx on port 8080. |
| **Core Media** | WebRTC Live Streaming | ✅ IMPLEMENTED | `surv/mediamtx/mediamtx.yml#L56-L64`, `surv/app/routers/streams.py#L54-L71` | WebRTC exposed on port 8889; token-authenticated. |
| **Core Media** | Dynamic Stream Authentication | ✅ IMPLEMENTED | `surv/app/routers/stream_auth.py`, `surv/mediamtx/mediamtx.yml#L15-L21` | MediaMTX calls `/api/v1/auth/stream` webhook per viewer connection. |
| **Recording** | 60s Segment Slicing | ✅ IMPLEMENTED | `surv/mediamtx/mediamtx.yml#L66-L79` | MediaMTX writes fMP4 segments to `/recordings/%path/%Y/%m/%d/...`. |
| **Recording** | MinIO Segment & Sidecar Upload | ✅ IMPLEMENTED | `surv/workers/upload_to_minio.py` | Hook triggers Python worker, uploads `.mp4` and `.json` metadata sidecar. |
| **Recording** | Kafka Segment Event Dispatch | ✅ IMPLEMENTED | `surv/workers/upload_to_minio.py#L114-L159` | Emits `recording.segment.uploaded` to `recording.segments` topic. |
| **Recording** | Database Segment Registration | ✅ IMPLEMENTED | `surv/app/workers/segment_db_consumer.py` | Kafka consumer inserts rows into `survapp_video_segment`. |
| **Recording** | Motion/Guard Segment Tagging | ✅ IMPLEMENTED | `surv/app/workers/segment_db_consumer.py#L53-L103` | Classifies segments as `motion`, `guard`, or `full` using time windows. |
| **Recording** | Local Segment Cleanup | ✅ IMPLEMENTED | `surv/workers/upload_to_minio.py#L160-L189` | Deletes local file only after MinIO file size verification matches. |
| **Storage** | MinIO Bucket Initialization | ✅ IMPLEMENTED | `surv/docker-compose.yml#L274-L290` | `minio_init` creates `recordings` and `snapshots` buckets automatically. |
| **Storage** | MinIO Retention Cleaner | ✅ IMPLEMENTED | `surv/workers/minio_cleaner.py` | Enforces per-camera `retention_days` and S3 bucket lifecycle safety net. |
| **Storage** | Snapshot Capture & Storage | ✅ IMPLEMENTED | `surv/workers/snapshot_worker.py`, `surv/app/routers/streams.py` | Worker writes timestamped key and `latest.jpg`, dynamically queries active cameras from PostgreSQL. |
| **Motion** | ONVIF Event Polling (Profile S) | ✅ IMPLEMENTED | `surv/onvif_producer/onvif_motion_producer.py` | PullPointSubscription parser supporting standard and non-standard cameras. |
| **Motion** | Kafka Motion Event Publishing | ✅ IMPLEMENTED | `surv/onvif_producer/onvif_motion_producer.py#L125-L132` | Publishes normalized `motion.started` and `motion.ended` to `camera.motion`. |
| **Motion** | Motion Database Consumer | ✅ IMPLEMENTED | `surv/motion_consumer/motion_event_consumer.py` | Consumes `camera.motion` and writes to `survapp_motion_event`. |
| **Motion** | Stale Motion Event Auto-Closer | ✅ IMPLEMENTED | `surv/app/routers/motion.py#L29-L46` | Closes un-ended active motion rows older than 30 minutes on read. |
| **Monitoring** | Camera Health & Uptime Worker | ✅ IMPLEMENTED | `surv/workers/status_monitor.py` | MediaMTX API / TCP port checks, logs transitions to `camera_status_log`. |
| **Monitoring** | Status Webhook / DB Alerting | ✅ IMPLEMENTED | `surv/workers/notifier.py` | HTTP webhook + in-app DB notification on camera offline threshold. |
| **Monitoring** | MediaMTX Ready/Down Hooks | ✅ IMPLEMENTED | `surv/scripts/camera_ready.sh`, `surv/Dockerfile.mediamtx` | MediaMTX image includes `kcat`; publishes ready/notReady events to Kafka `camera.status`. |
| **Monitoring** | Kafka Camera Status Consumer | 🔴 NOT IMPLEMENTED | `surv/docker-compose.yml` | `camera.status` topic receives messages, but no consumer service exists. |
| **Auth & Gateway** | Kong JWT Perimeter Validation | ✅ IMPLEMENTED | `surv/kong/setup-kong-jwt.sh`, `surv/docker-compose.yml` | Validates JWT for users; routes edge-agent `X-Site-Token` fleet and motion calls via open routes. |
| **Auth & RBAC** | Hierarchical Scope Enforcement | ✅ IMPLEMENTED | `surv/app/services/access_service.py` | Filters cameras by `organization_closure` subtree, direct grants, groups. |
| **Auth & RBAC** | Session Management & Revocation | ✅ IMPLEMENTED | `surv/app/services/auth_service.py`, `surv/app/routers/auth.py` | `user_session` tracking with server-side revocation on logout. |
| **Multi-Tenancy**| BSNL Hierarchy (ROOT/Circle/BA) | ✅ IMPLEMENTED | `surv/app/models/organization.py`, `surv/app/scripts/seed_hierarchy.py` | Full tree structure with closure table and idempotent seeding script. |
| **Multi-Tenancy**| Customer & Site Hierarchy | ✅ IMPLEMENTED | `surv/app/models/organization.py`, `surv/app/routers/customers.py` | `customer` and `customer_site` models with geolocation and camera mapping. |
| **Fleet / Edge** | NVR Fleet Hub API | ✅ IMPLEMENTED | `surv/app/routers/fleet.py` | Provisioning, heartbeat, config sync, camera assignment, clip registry. |
| **Fleet / Edge** | Edge Agent Appliance Loops | ✅ IMPLEMENTED | `edge-nvr/edge-agent/main.py` | 7 concurrent asyncio loops (heartbeat, config, motion, status, backup, etc.). |
| **Fleet / Edge** | Edge Backup to Hub MinIO | ✅ IMPLEMENTED | `edge-nvr/edge-agent/backup_uploader.py` | Motion-triggered video clip upload to central MinIO `backup_clips` bucket. |
| **Fleet / Edge** | Edge MediaMTX Stream Auth | ✅ IMPLEMENTED | `edge-nvr/mediamtx/mediamtx.yml`, `edge-nvr/docker-compose.yml` | Viewer playback requests validated against Hub stream webhook over VPN/LAN. |
| **Fleet / Edge** | Simulated Site Harness | ✅ IMPLEMENTED | `edge-sim/` | Docker Compose stack running 3 fake FFmpeg cameras and edge agent. |
| **VPN / Overlay**| Headscale & DERP Server | ✅ IMPLEMENTED | `surv/docker-compose.yml`, `surv/caddy/Caddyfile` | Headscale control plane + Hub Tailscale peer client (`surv_tailscale`) container. |
| **VPN / Overlay**| Automated ACL Synchronization | ✅ IMPLEMENTED | `surv/app/services/acl_sync_service.py` | Maps BSNL organizations to Headscale namespaces and constructs role-based ACLs. |
| **Mobile** | Mobile Device Token Registration | ✅ IMPLEMENTED | `surv/app/routers/mobile.py#L36-L80`, `0007_mobile_devices.py` | Upsert FCM/APNs push tokens per user in `mobile_device`. |
| **Mobile** | Mobile Dashboard Summary API | ✅ IMPLEMENTED | `surv/app/routers/mobile.py#L82-L150` | Scoped camera list, online count, active motion, and last motion time. |
| **Mobile** | Mobile VPN Session Issuance | 🔴 NOT IMPLEMENTED | `surv/app/routers/mobile.py#L159-L184` | Endpoints return HTTP 501 Not Implemented (pending Headscale client). |
| **Mobile** | Mobile Application Client | 📄 DOCUMENTED ONLY | `docs/archive/mobile_desin.md` | React Native / Expo app spec with embedded WireGuard; 0 lines of app code. |

---

## 3. Current Architecture

```
                                      CLIENTS & EDGE SITES
  ┌─────────────────────────────────┐                       ┌───────────────────────────────┐
  │         Web Browser SPA         │                       │      Portable Edge NVR        │
  │    (React 18 / Vite / Tailwind) │                       │  (MediaMTX + edge-agent)      │
  └────────┬───────────────────┬────┘                       └──────────────┬────────────────┘
           │ :3000 / :3443     │ :8000                                     │
           │ (Direct SPA)      │ (Kong Proxy)                              │ :8000 (Kong) or :8002 (Direct App)
           ▼                   ▼                                           │ (X-Site-Token)
  ┌────────────────────────────────────────────────────────────────────────▼────────────────┐
  │                                     KONG API GATEWAY (:8000 / :8443)                     │
  │  - Routes /api to FastAPI (surv-api)                                                    │
  │  - Routes /hls to Nginx HLS proxy (hls-stream)                                          │
  │  - Validates JWT tokens on protected routes (api-route, hls-route)                      │
  │  - Open routes: /api/v1/auth/login, /api/v1/auth/stream, /health, /api/v1/health       │
  │  - CRITICAL BUG: Rejects edge-agent X-Site-Token calls on :8000 (missing from open route)│
  │  - Commercial CORS handling, Rate Limiting (1000 req/min), BSNL Wildcard TLS            │
  └────────┬──────────────────────────────────────────┬─────────────────────────────────────┘
           │                                          │
           │ http://app:8000                          │ http://nginx_hls:80 (via Kong)
           ▼                                          │ Note: Browser connects directly to :8080
  ┌─────────────────────────────────┐                 │
  │     FastAPI Application         │                 ▼
  │   - Auth & RBAC enforcement     │        ┌──────────────────────────────────────────────┐
  │   - Camera & Org metadata       │        │               NGINX HLS PROXY                │
  │   - Presigned URL generation    │        │  - Port 8080 host (Direct Browser Access)    │
  │   - MediaMTX stream auth hook   │        │  - Proxies /hls/ to MediaMTX:8888            │
  │   - Fleet control plane         │        │  - Proxies /snapshots/ to MinIO:9000         │
  │   - SESSIONS IN POSTGRESQL      │        │  - Strips conflicting MediaMTX CORS headers  │
  │     (Redis is NOT connected)    │        └──────────────────────┬───────────────────────┘
  └────────┬──────────────┬─────────┘                               │
           │              │                                         │
           │ asyncpg      │ HTTP API (:9997)                        │ HLS Segments
           ▼              ▼                                         ▼
  ┌─────────────────┐   ┌───────────────────────────────────────────────────────────────────┐
  │  PostgreSQL 16  │   │                        MediaMTX MEDIA SERVER                      │
  │  - Port 5432    │   │  - RTSP (:8554), RTSPS (pull), RTMP (:1935), WebRTC (:8889)       │
  │  - Metadata     │   │  - authMethod: http -> FastAPI /api/v1/auth/stream                │
  │  - Closure Tree │   │  - 60s fMP4 recording segments to /recordings                     │
  │  - RBAC tables  │   │  - Hook: notify_segment.sh -> upload_to_minio.py                  │
  │  - Segments     │   └──────────────────────┬────────────────────────────────────────────┘
  │  - User Sessions│                          │
  └─────────────────┘                          │ Video Segments (.mp4) + Sidecars (.json)
                                               ▼
  ┌─────────────────────────────────────────────────────────────────────────────────────────┐
  │                                    MinIO OBJECT STORAGE                                 │
  │  - Ports :9000 (API) / :9001 (Web Console)                                              │
  │  - Buckets: 'recordings', 'snapshots', 'backup_clips'                                   │
  │  - Automated lifecycle policy + minio_cleaner retention enforcement                     │
  └────────────────────────┬────────────────────────────────────────────────────────────────┘
                           │
                           │ Kafka Producer (recording.segment.uploaded)
                           ▼
  ┌─────────────────────────────────────────────────────────────────────────────────────────┐
  │                              APACHE KAFKA 3.7.0 (KRaft Mode)                            │
  │  - Port 9092 (surv_kafka) / Kafka UI on :8090                                           │
  │  - Topics (3 partitions): camera.motion, camera.status, recording.segments              │
  └────────┬──────────────────────────────────────────┬─────────────────────────────────────┘
           │                                          │
           │ Consumer (camera.motion)                 │ Consumer (recording.segments)
           ▼                                          ▼
  ┌─────────────────────────────────┐        ┌──────────────────────────────────────────────┐
  │      motion_consumer            │        │           segment_db_consumer                │
  │  - Writes active/closed motion  │        │  - Classifies: 'motion', 'guard', 'full'     │
  │    to survapp_motion_event      │        │  - Inserts into survapp_video_segment        │
  └─────────────────────────────────┘        └──────────────────────────────────────────────┘
```

---

## 4. Repository Structure

```
/opt/surv-learn/
├── README.md                          # Monorepo directory overview and canonical pointers
├── PROJECT_STATE.md                   # Canonical Document 1: Verified As-Built Project State
├── PROJECT_ROADMAP.md                 # Canonical Document 2: Prioritized Development Roadmap
├── DOCUMENTATION_CLEANUP.md           # Master Documentation Audit Trail & Cleanup Log
├── surv/                              # CENTRAL HUB APPLICATION STACK
│   ├── app/                           # FastAPI Application Root
│   │   ├── main.py                    # App entrypoint, lifespan startup sync, router registration
│   │   ├── config.py                  # Pydantic settings schema from environment variables
│   │   ├── database.py                # SQLAlchemy async engine, sessionmaker, get_db dependency
│   │   ├── alembic.ini                # Migration configuration
│   │   ├── alembic/                   # Alembic migrations (10 linear revisions: 0001 -> 0010)
│   │   ├── models/                    # ORM entities (user, camera, organization, rbac, nvr, mobile)
│   │   ├── schemas/                   # Pydantic request/response validation models
│   │   ├── routers/                   # 15 API routers (auth, cameras, streams, recordings, fleet, etc.)
│   │   ├── dependencies/              # FastAPI dependencies (auth, fleet_auth)
│   │   ├── services/                  # Business logic (access_service, mediamtx_client, auth_service)
│   │   ├── workers/                   # In-app workers (segment_db_consumer.py)
│   │   ├── scripts/                   # Seeding scripts (seed_hierarchy.py)
│   │   ├── tests/                     # Automated tests (test_access_enforcement.py)
│   │   └── Dockerfile                 # Hub app Dockerfile (Python 3.12-slim, non-root appuser)
│   ├── frontend/                      # React 18 TypeScript SPA
│   │   ├── src/                       # Application code
│   │   │   ├── pages/                 # 13 views (Cameras, LiveView, Playback, Motion, Fleet, etc.)
│   │   │   ├── components/            # Reusable UI (HLSPlayer, Timeline, VideoControls, Sidebar)
│   │   │   ├── api/client.ts          # Central Axios HTTP client with typed contracts
│   │   │   ├── lib/                   # Utilities (auth.ts, videoPlayback.ts)
│   │   │   └── hooks/                 # Custom hooks (usePolling, useVideoZoom, useVideoKeyboard)
│   │   ├── vite.config.ts             # Vite build configuration
│   │   └── package.json               # Frontend dependencies (React Router 7, Lucide, Tailwind v4)
│   ├── mediamtx/                      # MediaMTX configuration (mediamtx.yml)
│   ├── nginx/                         # Reverse proxy configurations (hls.conf, frontend.conf)
│   ├── kong/                          # Kong configuration scripts (setup-kong-jwt.sh)
│   ├── workers/                       # Dedicated Hub worker scripts
│   │   ├── upload_to_minio.py         # MediaMTX segment completion handler
│   │   ├── status_monitor.py          # Periodic camera reachability & health monitor
│   │   ├── minio_cleaner.py           # S3 recording retention & cleanup worker
│   │   ├── snapshot_worker.py         # FFmpeg periodic JPEG frame grabber
│   │   └── notifier.py                # Alert dispatcher (HTTP webhook + DB notifications)
│   ├── onvif_producer/                # Vendor-agnostic ONVIF WS-Notification event subscriber
│   ├── motion_consumer/               # Kafka consumer writing motion events to PostgreSQL
│   ├── headscale/                     # Headscale VPN configuration and ACL definition
│   ├── caddy/                         # Caddyfile reverse proxy for Headscale
│   ├── certs/                         # Wildcard TLS certificates (*.bsnl.co.in)
│   ├── scripts/                       # Shell scripts (upload_to_minio.sh, notify_segment.sh, etc.)
│   ├── docker-compose.yml             # Central Hub Docker Compose stack (26 services)
│   └── docker-compose.prod.yml        # Production override (port restrictions, replica scaling)
├── edge-nvr/                          # PORTABLE EDGE NVR STACK
│   ├── edge-agent/                    # Python edge agent (heartbeat, config sync, retention, backup)
│   ├── mediamtx/                      # Edge MediaMTX config (local recording, RTSP, HLS)
│   ├── docker-compose.yml             # Appliance Compose file (mediamtx, edge-agent, optional tailscale)
│   └── README.md                      # Edge deployment instructions
├── edge-sim/                          # EDGE SITE SIMULATION HARNESS
│   ├── docker-compose.yml             # Multi-site simulation stack (3 FFmpeg fake cameras + edge agent)
│   ├── generate_clips.sh              # Synthetic MP4 generator with burned-in site labels
│   ├── register_site.py               # Automated camera registration & fleet assignment script
│   ├── inject_motion.py               # Synthetic motion event injector for load testing
│   ├── sim_manage.sh                  # Site lifecycle helper script
│   └── site-envs/                     # Environment definitions for simulated sites
└── docs/                              # Project documentation directory
    ├── prompt1.md                     # Documentation consolidation prompt specification
    ├── prompt2.md                     # Architectural verification prompt specification
    ├── tender_prompt.md               # Tender analysis prompt specification
    ├── 1789370597 (1).pdf             # Kerala Police / Home Dept tender document
    ├── Surveillance Tender-KELTRON (1).pdf # Keltron EOI tender document
    ├── setup/                         # Active network and hierarchy specifications
    └── archive/                       # Historical and superseded implementation plans (22 files)
```

---

## 5. Services and Responsibilities

The Hub `surv/docker-compose.yml` defines **26 service definitions** running on the bridge network `surv_net`:

| Service Name | Container Name | Image / Build Context | Internal Ports | Host Published Ports | Responsibility & Implementation Reality |
|---|---|---|---|---|---|
| `postgres` | `surv_postgres` | `postgres:16` | 5432 | `5432:5432` | Relational storage for all metadata, RBAC, users, segments, and audit logs. |
| `redis` | `surv_redis` | `redis:7-alpine` | 6379 | `6379:6379` | **IDLE CONTAINER:** Started by compose, but unused by application code. Sessions live in PostgreSQL. |
| `kong-db-init` | `surv_kong_db_init` | `postgres:16` | — | — | One-shot init container creating the `kong` database if absent. |
| `kong-migration` | `surv_kong_migration` | `kong:3.6` | — | — | One-shot bootstrap runner executing `kong migrations bootstrap`. |
| `kong` | `surv_kong` | `kong:3.6` | 8000, 8001, 8443 | `8000:8000`, `8443:8443`, `8001:8001` | API Gateway verifying JWTs, rate-limiting, and routing `/api` and `/hls`. |
| `kong-config` | `surv_kong_config` | `curlimages/curl:8.8.0` | — | — | Idempotent script provisioning Kong consumers, routes, JWT plugin, and TLS cert. |
| `kafka` | `surv_kafka` | `apache/kafka:3.7.0` | 9092, 9093 | `9092:9092` | Event broker running in KRaft mode (controller quorum). |
| `kafka_init` | `surv_kafka_init` | `apache/kafka:3.7.0` | — | — | One-shot topic initializer creating `camera.motion`, `camera.status`, `recording.segments`. |
| `kafka_ui` | `surv_kafka_ui` | `provectuslabs/kafka-ui:latest` | 8080 | `8090:8080` | Web administration UI for Kafka cluster inspection. |
| `minio` | `surv_minio` | `minio/minio:latest` | 9000, 9001 | `9000:9000`, `9001:9001` | S3-compatible object storage for video recordings and snapshots. |
| `minio_init` | `surv_minio_init` | `minio/mc:latest` | — | — | One-shot bucket provisioning container creating `recordings` and `snapshots`. |
| `mediamtx` | `surv_mediamtx` | `Dockerfile.mediamtx` | 8554, 1935, 8888, 8889, 9997, 8189/udp | `8554`, `1935`, `8888`, `8889`, `9997`, `8189/udp` | Core media ingestion engine for RTSP/RTMP/HLS/WebRTC with segment slicing. |
| `nginx_hls` | `surv_nginx_hls` | `nginx:1.27-alpine` | 80 | `8080:80` | HLS reverse proxy rewriting MediaMTX CORS headers and relative 302 redirects. |
| `frontend` | `surv_frontend` | `Dockerfile.frontend` | 8080, 8443 | `3000:8080`, `3443:8443` | Nginx web server hosting the compiled React SPA. |
| `app` | `surv_app` | `app/Dockerfile` | 8000 | `8002:8000` | Core FastAPI backend application server (proxied at port 8000 via Kong). |
| `db_migrate` | `surv_db_migrate` | `app/Dockerfile` | — | — | One-shot Alembic migration container executing `alembic upgrade head`. |
| `segment_db_consumer` | `surv_segment_consumer` | `app/Dockerfile` | — | — | Kafka consumer classifying and recording uploaded segments in PostgreSQL. |
| `onvif_producer` | `surv_onvif_producer` | `onvif_producer/Dockerfile` | — | — | Poller subscribing to camera ONVIF motion events and dispatching to Kafka. |
| `motion_consumer` | `surv_motion_consumer` | `motion_consumer/Dockerfile` | — | — | Kafka consumer inserting/updating motion events in `survapp_motion_event`. |
| `status_monitor` | `surv_status_monitor` | `Dockerfile.worker` | — | — | Background worker verifying camera online status and logging uptime. |
| `minio_cleaner` | `surv_minio_cleaner` | `Dockerfile.worker` | — | — | Retention worker pruning old video segments according to policy. |
| `snapshotter` | `surv_snapshotter` | `Dockerfile.worker` | — | — | FFmpeg worker capturing periodic JPEG snapshots from camera RTSP feeds. |
| `dnsmasq` | `surv_dnsmasq` | `alpine:latest` | 53/tcp, 53/udp | `53:53/udp`, `53:53/tcp` | Private DNS server resolving `sarvanetra.bsnl.co.in` to local host LAN IP. |
| `headscale` | `surv_headscale` | `headscale/headscale:latest-alpine`| 8080 | — | Self-hosted Tailscale control plane coordinating WireGuard VPN overlay. |
| `caddy` | `surv_caddy` | `caddy:2` | 443 | `8180:443` | Reverse proxy terminating TLS for Headscale using wildcard BSNL certificates. |
| `derp` | `surv_derp` | `fredliang/derper:latest` | 3478/udp, 443 | `3478:3478/udp`, `8443:443` | STUN / DERP relay server assisting Tailscale NAT traversal. |

---

## 6. Backend Analysis

The backend is built with FastAPI 2.0.0 (`surv/app/`), running under Python 3.12.

### Entry Point and Lifecycle (`surv/app/main.py`)
- Modern FastAPI `lifespan` context manager.
- **Startup:** Queries all active cameras (`Camera.is_active == True`) and calls `mediamtx_client.sync_cameras()` to ensure streaming paths exist in MediaMTX on startup.
- **Dual Database Connections:**
  - `DATABASE_URL`: `postgresql+asyncpg://...` used by FastAPI for asynchronous queries.
  - `SYNC_DATABASE_URL`: `postgresql://...` used by Alembic migrations and background worker processes (`psycopg2`).
- **Dependencies in `requirements.txt`:** Does NOT include `redis`. Sessions are stored in PostgreSQL table `user_session`.

---

## 7. Frontend Analysis

The frontend is a single-page application built with React 18, TypeScript 5, Vite 5, and Tailwind CSS v4 (`surv/frontend/`).

### Routing and Page Map (`surv/frontend/src/App.tsx`)

| Route | Page Component | Required Permission / Role | Features Implemented |
|---|---|---|---|
| `/login` | `Login.tsx` | Public | Username/password login, JWT storage in localStorage, user metadata extraction. |
| `/` | `LiveView.tsx` | `camera.live` | Responsive video grid (1x1, 2x2, 3x3), HLS playback via `HLSPlayer.tsx`, WebRTC support, full-screen expansion, digital zoom, keyboard navigation. |
| `/playback` | `Playback.tsx` | `camera.playback` | Date picker, 24-hour interactive recording timeline (`Timeline.tsx`), segment filtering (`full`, `motion`, `guard`), playback speed controls (0.5x to 16x), clip download. |
| `/motion` | `MotionEvents.tsx` | `camera.view` | Live active motion indicator badge, historical motion event table, duration calculation, direct link to playback time. |
| `/cameras` | `Cameras.tsx` | `camera.view` / `camera.create` | Camera list with online/offline status, camera registration modal supporting RTSP/RTSPS/RTMP protocols, motion guard time configuration, delete/edit actions. |
| `/health` | `Health.tsx` | `report.view` | Dashboard summary cards (total, online, offline, motion), per-camera uptime percentages, offline duration, status change history modal, S3 storage stats. |
| `/fleet` | `NvrFleet.tsx` | `SUPER_ADMIN` / `system.settings` | Edge NVR site list, hardware labels, disk usage progress bar, last heartbeat indicator, NVR provisioning modal displaying generated `SITE_TOKEN`, camera assignment drawer. |
| `/org` | `Organizations.tsx` | `system.settings` | Hierarchical BSNL tree view (Circle, BA, SSA, Site), organization creation modal with parent selection, active status toggle. |
| `/customers` | `Customers.tsx` | `customer.create` | Customer enterprise list, customer creation modal, site management per customer with latitude/longitude inputs. |
| `/users` | `Users.tsx` | `user.create` / `SUPER_ADMIN` | User directory table, user account creation modal (employee vs customer user types), organization/customer assignment, account lock status. |
| `/roles` | `Roles.tsx` | `system.settings` | Standard roles catalog, permission mapping inspection, role assignment to users, custom permission toggle. |
| `/audit` | `AuditLog.tsx` | `system.audit` | Filterable security audit trail (LOGIN, LOGOUT, camera access, configuration changes), IP address tracking. |
| `/camera-groups` | `CameraGroups.tsx` | `camera.create` | Camera group creation, camera membership mapping, user group access assignment. |

---

## 8. Database Architecture

Database management uses PostgreSQL 16 with 10 linear Alembic revisions.

### Alembic Migration Sequence

```
0001 (initial) ──▶ 0002 (add_users) ──▶ 0003 (company_hierarchy) ──▶ 0004_bsnl_masters ──▶ 0005_camera_health
                                                                                                  │
0010_recording_mode ◀── 0009_stream_protocol ◀── 0008_edge_segments ◀── 0007_mobile_devices ◀── 0006_edge_fleet
```

---

## 9. Authentication & Authorization

Authentication combines the Kong Gateway at the perimeter with fine-grained RBAC in FastAPI.

### 1. Perimeter Authentication (Kong)
- Routes `/api` (`api-route`) and `/hls` (`hls-route`) are protected by Kong's `jwt` plugin.
- Open bypass route `auth-open-route` allows: `/api/v1/auth/login`, `/api/v1/auth/stream`, `/health`, `/api/v1/health`.
- **Perimeter Defect:** Edge-agent endpoints (`/api/v1/fleet/heartbeat`, `/api/v1/fleet/*/config`, `/api/v1/fleet/*/backup-clip`, `/api/v1/motion/edge`) authenticate via `X-Site-Token` without a JWT. Kong rejects them on port 8000 with HTTP 401 Unauthorized unless added to `auth-open-route`.

### 2. Live HLS Delivery Divergence
- While Kong defines an `hls-route`, both `surv/.env.example` (`MEDIAMTX_HLS_BASE=http://10.44.0.209:8080/hls`) and `surv/frontend/.env` point the browser directly to `nginx_hls:8080/hls`, bypassing Kong.
- MediaMTX verifies tokens by calling FastAPI `/api/v1/auth/stream` directly container-to-container.

---

## 10. Camera Management

Camera lifecycle is managed via `surv/app/routers/cameras.py`:
- Registration, updating, and deactivation invoke `mediamtx_client` methods to dynamically update MediaMTX paths.

---

## 11. ONVIF, RTSP & Streaming Ingest

Supports RTSP pull, RTSPS pull (port 322), and RTMP push (`source: "publisher"` on port 1935).
`onvif_motion_producer.py` polls Profile S cameras, handles vendor-specific WS-Notification XML quirks (Matrix, TP-Link, CP Plus), and emits normalized events to Kafka `camera.motion`.

---

## 12. MediaMTX Integration

Configuration is defined in `surv/mediamtx/mediamtx.yml`:
- Ingests RTSP/RTMP/WebRTC feeds.
- Authenticates viewers via `authMethod: http` -> `http://app:8000/api/v1/auth/stream`.
- Slices recordings into 60s fMP4 chunks.

---

## 13. Recording Pipeline

```
MediaMTX (fMP4 segment) ──▶ notify_segment.sh ──▶ upload_to_minio.py ──▶ MinIO 'recordings'
                                                                     ──▶ Kafka 'recording.segments'
                                                                     ──▶ Local file unlinked
                                                                                │
                                                                                ▼
                                                                segment_db_consumer.py (DB insert)
```

---

## 14. MinIO Object Storage

- Buckets: `recordings`, `snapshots`, `backup_clips`.
- Retention cleaner (`minio_cleaner.py`) prunes expired segments every 6 hours and sets S3 safety-net lifecycle rules.

---

## 15. HLS & Live Playback

- Live streams generated by MediaMTX, served via `nginx_hls:8080`.
- 24-hr recording timeline generated by `GET /api/v1/recordings/{cam_id}/timeline`.

---

## 16. Kafka & Event Processing

Cluster runs Kafka 3.7.0 in KRaft mode (`surv_kafka:9092`):
- `camera.motion` (Produced by `onvif_motion_producer.py`, consumed by `motion_event_consumer.py`).
- `recording.segments` (Produced by `upload_to_minio.py`, consumed by `segment_db_consumer.py`).
- `camera.status` (Produced by `status_monitor.py`; no consumer service attached).

---

## 17. API Inventory

The complete, verified route inventory of the FastAPI backend (`surv/app/routers/`):

| Method | Path | Router File | Authentication / Permission | Dependencies | Purpose | Status |
|---|---|---|---|---|---|---|
| `GET` | `/health` | `main.py` | None | None | Root service health check | ✅ OPERATIONAL |
| `GET` | `/api/v1/health/` | `routers/health.py` | None | None | Base health ping | ✅ OPERATIONAL |
| `GET` | `/api/v1/health/services` | `routers/health.py` | None | MediaMTX, MinIO S3 | Legacy dependency status probe | ✅ OPERATIONAL |
| `GET` | `/api/v1/health/summary` | `routers/health.py` | `get_current_user` | PostgreSQL | Overall system dashboard counts | ✅ OPERATIONAL |
| `GET` | `/api/v1/health/cameras` | `routers/health.py` | `get_current_user` | PostgreSQL | Per-camera status & uptime stats | ✅ OPERATIONAL |
| `GET` | `/api/v1/health/cameras/{cam_id}/history` | `routers/health.py` | `get_current_user` | PostgreSQL | Camera status transition history | ✅ OPERATIONAL |
| `GET` | `/api/v1/health/storage` | `routers/health.py` | `system.settings` / `SUPER_ADMIN` | MinIO S3 | MinIO bucket object counts and size | ✅ OPERATIONAL |
| `POST` | `/api/v1/auth/login` | `routers/auth.py` | None (Open) | PostgreSQL | Authenticate user, issue JWT token | ✅ OPERATIONAL |
| `POST` | `/api/v1/auth/logout` | `routers/auth.py` | `get_current_user` | PostgreSQL | Revoke current user session | ✅ OPERATIONAL |
| `GET` | `/api/v1/auth/me` | `routers/auth.py` | `get_current_user` | PostgreSQL | Fetch current user profile & roles | ✅ OPERATIONAL |
| `POST` | `/api/v1/auth/users` | `routers/auth.py` | `require_admin` | PostgreSQL | Create a new user account | ✅ OPERATIONAL |
| `GET` | `/api/v1/auth/users` | `routers/auth.py` | `require_admin` | PostgreSQL | List all system user accounts | ✅ OPERATIONAL |
| `POST` | `/api/v1/auth/stream` | `routers/stream_auth.py` | None (Webhook from MediaMTX) | None | MediaMTX stream token validation | ✅ OPERATIONAL |
| `GET` | `/api/v1/cameras/` | `routers/cameras.py` | `camera.view` | PostgreSQL, `access_service` | List accessible cameras | ✅ OPERATIONAL |
| `POST` | `/api/v1/cameras/` | `routers/cameras.py` | `camera.create` | PostgreSQL, MediaMTX API | Register new camera | ✅ OPERATIONAL |
| `GET` | `/api/v1/cameras/{cam_id}` | `routers/cameras.py` | `camera.view` | PostgreSQL, `access_service` | Get camera details | ✅ OPERATIONAL |
| `PATCH` | `/api/v1/cameras/{cam_id}` | `routers/cameras.py` | `camera.update` | PostgreSQL, MediaMTX API | Update camera parameters | ✅ OPERATIONAL |
| `DELETE` | `/api/v1/cameras/{cam_id}` | `routers/cameras.py` | `camera.delete` | PostgreSQL, MediaMTX API | Soft-deactivate camera | ✅ OPERATIONAL |
| `GET` | `/api/v1/streams/{cam_id}/hls-url` | `routers/streams.py` | `camera.live` | `access_service` | Get signed HLS stream URL | ✅ OPERATIONAL |
| `GET` | `/api/v1/streams/{cam_id}/webrtc-url` | `routers/streams.py` | `camera.live` | `access_service` | Get signed WebRTC stream URL | ✅ OPERATIONAL |
| `GET` | `/api/v1/streams/{cam_id}/snapshot-url` | `routers/streams.py` | `camera.view` | MinIO S3 | Get presigned snapshot URL | ⚠️ BROKEN (404) |
| `GET` | `/api/v1/recordings/{cam_id}/timeline` | `routers/recordings.py` | `camera.playback` | PostgreSQL, MinIO S3 | Fetch 24-hr segment timeline | ✅ OPERATIONAL |
| `GET` | `/api/v1/recordings/{cam_id}/download` | `routers/recordings.py` | `camera.download` | MinIO S3 | Get presigned segment download URL | ✅ OPERATIONAL |
| `GET` | `/api/v1/motion/active` | `routers/motion.py` | `get_current_user` | PostgreSQL, `access_service` | List current active motion events | ✅ OPERATIONAL |
| `GET` | `/api/v1/motion/` | `routers/motion.py` | `get_current_user` | PostgreSQL, `access_service` | Query historical motion events | ✅ OPERATIONAL |
| `GET` | `/api/v1/motion/{event_id}` | `routers/motion.py` | `get_current_user` | PostgreSQL, `access_service` | Get single motion event detail | ✅ OPERATIONAL |
| `POST` | `/api/v1/motion/edge` | `routers/motion.py` | `X-Site-Token` | PostgreSQL, `fleet_auth` | Edge agent motion event ingestion | ⚠️ BLOCKED BY KONG |
| `GET` | `/api/v1/org/` | `routers/organizations.py`| `get_current_user` | PostgreSQL | List organizations | ✅ OPERATIONAL |
| `POST` | `/api/v1/org/` | `routers/organizations.py`| `system.settings` | PostgreSQL | Create organization & rebuild closure | ✅ OPERATIONAL |
| `GET` | `/api/v1/org/{org_id}` | `routers/organizations.py`| `get_current_user` | PostgreSQL | Get organization details | ✅ OPERATIONAL |
| `GET` | `/api/v1/org/{org_id}/subtree` | `routers/organizations.py`| `get_current_user` | PostgreSQL | Fetch complete subtree organization IDs | ✅ OPERATIONAL |
| `PATCH` | `/api/v1/org/{org_id}` | `routers/organizations.py`| `system.settings` | PostgreSQL | Update organization metadata | ✅ OPERATIONAL |
| `GET` | `/api/v1/bsnl/circles` | `routers/bsnl.py` | `get_current_user` | PostgreSQL | List BSNL circles master | ✅ OPERATIONAL |
| `GET` | `/api/v1/bsnl/bas` | `routers/bsnl.py` | `get_current_user` | PostgreSQL | List BSNL Business Areas master | ✅ OPERATIONAL |
| `GET` | `/api/v1/customers/` | `routers/customers.py` | `get_current_user` | PostgreSQL | List customers | ✅ OPERATIONAL |
| `POST` | `/api/v1/customers/` | `routers/customers.py` | `customer.create` | PostgreSQL | Create customer enterprise | ✅ OPERATIONAL |
| `GET` | `/api/v1/customers/{customer_id}`| `routers/customers.py` | `get_current_user` | PostgreSQL | Get customer details | ✅ OPERATIONAL |
| `PATCH` | `/api/v1/customers/{customer_id}`| `routers/customers.py` | `customer.update` | PostgreSQL | Update customer details | ✅ OPERATIONAL |
| `GET` | `/api/v1/customers/{customer_id}/sites`| `routers/customers.py` | `get_current_user` | PostgreSQL | List sites under a customer | ✅ OPERATIONAL |
| `POST` | `/api/v1/customers/{customer_id}/sites`| `routers/customers.py` | `customer.update` | PostgreSQL | Create customer site | ✅ OPERATIONAL |
| `GET` | `/api/v1/roles/` | `routers/roles.py` | `system.settings` | PostgreSQL | List system roles | ✅ OPERATIONAL |
| `POST` | `/api/v1/roles/` | `routers/roles.py` | `system.settings` | PostgreSQL | Create custom role | ✅ OPERATIONAL |
| `GET` | `/api/v1/roles/{role_id}/permissions`| `routers/roles.py`| `system.settings` | PostgreSQL | Get permissions for a role | ✅ OPERATIONAL |
| `POST` | `/api/v1/roles/{role_id}/permissions`| `routers/roles.py`| `system.settings` | PostgreSQL | Assign permission to role | ✅ OPERATIONAL |
| `DELETE`| `/api/v1/roles/{role_id}/permissions/{perm_id}`| `routers/roles.py`| `system.settings`| PostgreSQL| Remove permission from role | ✅ OPERATIONAL |
| `GET` | `/api/v1/permissions/` | `routers/roles.py` | `system.settings` | PostgreSQL | List all available permissions | ✅ OPERATIONAL |
| `POST` | `/api/v1/permissions/` | `routers/roles.py` | `system.settings` | PostgreSQL | Register new permission code | ✅ OPERATIONAL |
| `POST` | `/api/v1/users/{user_id}/roles`| `routers/roles.py` | `system.settings` | PostgreSQL | Assign role to user | ✅ OPERATIONAL |
| `DELETE`| `/api/v1/users/{user_id}/roles/{role_id}`| `routers/roles.py`| `system.settings`| PostgreSQL| Unassign role from user | ✅ OPERATIONAL |
| `GET` | `/api/v1/camera-groups/` | `routers/camera_groups.py`| `camera.view` | PostgreSQL | List camera groups | ✅ OPERATIONAL |
| `POST` | `/api/v1/camera-groups/` | `routers/camera_groups.py`| `camera.create` | PostgreSQL | Create camera group | ✅ OPERATIONAL |
| `GET` | `/api/v1/camera-groups/{group_id}`| `routers/camera_groups.py`| `camera.view` | PostgreSQL | Get camera group details | ✅ OPERATIONAL |
| `POST` | `/api/v1/camera-groups/{group_id}/cameras`| `routers/camera_groups.py`| `camera.update`| PostgreSQL| Add camera to group | ✅ OPERATIONAL |
| `DELETE`| `/api/v1/camera-groups/{group_id}/cameras/{camera_id}`| `routers/camera_groups.py`| `camera.update`| PostgreSQL| Remove camera from group | ✅ OPERATIONAL |
| `POST` | `/api/v1/camera-groups/{group_id}/users`| `routers/camera_groups.py`| `system.settings`| PostgreSQL| Grant user access to camera group | ✅ OPERATIONAL |
| `GET` | `/api/v1/audit/` | `routers/audit.py` | `system.audit` | PostgreSQL | Query filterable security audit logs | ✅ OPERATIONAL |
| `GET` | `/api/v1/fleet/` | `routers/fleet.py` | `SUPER_ADMIN` / `system.settings` | PostgreSQL | List all Edge NVR appliances | ✅ OPERATIONAL |
| `POST` | `/api/v1/fleet/` | `routers/fleet.py` | `SUPER_ADMIN` / `system.settings` | PostgreSQL | Provision new NVR (generates token) | ✅ OPERATIONAL |
| `GET` | `/api/v1/fleet/{site_code}`| `routers/fleet.py`| `SUPER_ADMIN` / `system.settings` | PostgreSQL | Get single NVR details | ✅ OPERATIONAL |
| `DELETE`| `/api/v1/fleet/{site_code}`| `routers/fleet.py`| `SUPER_ADMIN` / `system.settings` | PostgreSQL | Decommission Edge NVR | ✅ OPERATIONAL |
| `GET` | `/api/v1/fleet/{site_code}/cameras`| `routers/fleet.py`| `SUPER_ADMIN` / `system.settings`| PostgreSQL| List cameras mapped to edge NVR | ✅ OPERATIONAL |
| `POST` | `/api/v1/fleet/{site_code}/cameras`| `routers/fleet.py`| `SUPER_ADMIN` / `system.settings`| PostgreSQL| Assign camera to edge NVR | ✅ OPERATIONAL |
| `DELETE`| `/api/v1/fleet/{site_code}/cameras/{cam_id}`| `routers/fleet.py`| `SUPER_ADMIN` / `system.settings`| PostgreSQL| Unassign camera from edge NVR | ✅ OPERATIONAL |
| `POST` | `/api/v1/fleet/heartbeat` | `routers/fleet.py` | `X-Site-Token` | PostgreSQL | Edge agent heartbeat sync | ⚠️ BLOCKED BY KONG |
| `GET` | `/api/v1/fleet/{site_code}/config` | `routers/fleet.py` | `X-Site-Token` | PostgreSQL | Edge agent configuration pull | ⚠️ BLOCKED BY KONG |
| `POST` | `/api/v1/fleet/{site_code}/backup-clip`| `routers/fleet.py`| `X-Site-Token` | PostgreSQL | Edge critical clip metadata ingestion | ⚠️ BLOCKED BY KONG |
| `POST` | `/api/v1/mobile/register-device` | `routers/mobile.py` | `get_current_user` | PostgreSQL | Upsert mobile push notification token | ✅ OPERATIONAL |
| `GET` | `/api/v1/mobile/dashboard-summary`| `routers/mobile.py`| `get_current_user` | PostgreSQL | Mobile-optimized dashboard metrics | ✅ OPERATIONAL |
| `POST` | `/api/v1/mobile/vpn-session` | `routers/mobile.py` | `get_current_user` | None | Mobile WireGuard session issue | 🔴 NOT IMPLEMENTED (501) |
| `DELETE`| `/api/v1/mobile/vpn-session` | `routers/mobile.py` | `get_current_user` | None | Mobile WireGuard session revoke | 🔴 NOT IMPLEMENTED (501) |

---

## 18. Docker & Infrastructure

The project includes four distinct Docker Compose environments:
1. `surv/docker-compose.yml`: Primary Hub stack with 26 service definitions.
2. `surv/docker-compose.prod.yml`: Production overrides closing internal ports.
3. `edge-nvr/docker-compose.yml`: Portable Edge appliance stack.
4. `edge-sim/docker-compose.yml`: Multi-site simulated test harness.

---

## 19. Configuration

Configuration relies on environment variables loaded via Pydantic (`surv/app/config.py`) and Compose `.env`.

---

## 20. Testing & Test Coverage
 
- Automated unit test suite with **35 passing tests** across 7 test modules:
  - `surv/app/tests/test_auth.py` (7 tests: password hashing, access JWT encoding/decoding, expiration, tampering, stream token lifecycle, session creation & revocation)
  - `surv/app/tests/test_cameras.py` (8 tests: schema validation, protocol normalization, credential encoding, RTMP publisher payloads, RTSP pull payloads, MediaMTX API registration & removal)
  - `surv/app/tests/test_access_service.py` (4 tests: unrestricted roles, org subtree resolution, direct camera overrides, group mappings, permission enforcement)
  - `surv/app/tests/test_access_enforcement.py` (3 tests: camera accessibility enforcement checks)
  - `surv/app/tests/test_acl_sync.py` (4 tests: namespace sanitization, Headscale user creation idempotency, ACL rule construction, organization batch sync)
  - `surv/app/tests/test_fleet.py` (6 tests: edge site token authentication, header validation, unprovisioned NVR handling, heartbeat processing & commit)
  - `surv/app/tests/test_recordings.py` (3 tests: camera not found, date format validation, timeline segment queries with presigned URLs)
- Multi-site simulation suite in `edge-sim/` with synthetic FFmpeg video feeds and randomized motion injection.

---

## 21. Known Problems & Operational Deficiencies

1. **Kong Gateway Blocks Edge Agent Fleet & Motion Endpoints:**  
   - **Status:** ✅ RESOLVED. `setup-kong-jwt.sh` now configures `auth-open-route` with bypass paths for `/api/v1/fleet/heartbeat`, `/api/v1/motion/edge`, `~/api/v1/fleet/[^/]+/config`, and `~/api/v1/fleet/[^/]+/backup-clip`. `X-Site-Token` is included in allowed CORS headers.
2. **Missing `kcat` Dependency in MediaMTX Container:**  
   - **Status:** ✅ RESOLVED. Added `kcat` to Alpine package install in `surv/Dockerfile.mediamtx`.
3. **Snapshot Key Mismatch (HTTP 404):**  
   - **Status:** ✅ RESOLVED. `surv/workers/snapshot_worker.py` now writes both the timestamped JPEG and `{camera_path}/latest.jpg` on each capture cycle.
4. **Hardcoded Snapshot Camera Targets:**  
   - **Status:** ✅ RESOLVED. `snapshot_worker.py` dynamically queries active cameras from PostgreSQL with safe fallback to `CAMERA_PATHS`. Added `DATABASE_URL` and `postgres` dependency to `snapshotter` in `docker-compose.yml`.
5. **Idle / Unused Redis Container:**  
   - **Status:** 🟡 PENDING DECISION. `surv_redis` runs in Docker Compose, but is unreferenced by backend code (sessions live in PostgreSQL `user_session`). Can be removed to conserve memory or wired into FastAPI for query caching.
6. **Architectural Divergence: Browser HLS Traffic Bypasses Kong:**  
   - Direct browser connection to `nginx_hls:8080` is retained for optimal low-latency playback; MediaMTX token webhook validates playback tokens directly with FastAPI.
7. **Empty and Stale Files in Codebase:**  
   - **Status:** ✅ RESOLVED. Removed 0-byte `surv/workers/upload_worker.py` and `surv/kong/kong.yml`.
8. **Stubbed Headscale ACL Synchronization:**  
   - **Status:** ✅ RESOLVED. Implemented `surv/app/services/acl_sync_service.py` with organization synchronization, namespace sanitization, and Headscale ACL policy generation.
9. **Hardcoded Development IP (`10.44.0.209`):**  
   - **Status:** ✅ RESOLVED. Introduced `HOST_IP` parameterization across `.env`, `.env.example`, `frontend/.env`, `app/config.py`, `setup-kong-jwt.sh`, `register_site.py`, and `inject_motion.py`.

---

## 22. Documentation Conflicts vs. Implementation Reality

| Document | Stated Claim in Document | Codebase Truth | Divergence Classification |
|---|---|---|---|
| `docs/archive/sarvanetra_architecture.md` | "Django / FastAPI application layer" | FastAPI only (`surv/app/main.py`); Django was never implemented. | Obsolete / Superseded |
| `docs/archive/sarvanetra_architecture.md` | "Admin UI: Konga (:1337)" | Konga container is completely absent from all `docker-compose.yml` files. | Documented Only |
| `docs/archive/implementation_status.md` (Table §4) | "Phase 9 (Health), 10 (Retention), 11 (Hardening): ❌ Not started" | All three phases are fully coded (`status_monitor.py`, `minio_cleaner.py`, `0005_camera_health.py`, `docker-compose.prod.yml`). Later text note corrects this. | Internal Conflict |
| `docs/archive/implementation_plan_phase_12+.md` | "Phase 12 and 14 are complete" | Phase 14 Headscale integration is only partially configured; `acl_sync_service.py` is stubbed and `mobile.py` VPN endpoints return 501. | Inaccurate Claim |
| `docs/archive/sarvanetra_final_implementation_plan.md` | "Applied Migrations: 0001 through 0007" | Subsequent migrations `0008_edge_segments`, `0009_stream_protocol`, and `0010_recording_mode` were added to the codebase. | Stale Baseline |
| `docs/archive/sarvanetra_status_plan.md` | "Postgres tables: camera_master, motion_event, video_segment" | Actual PostgreSQL tables created by Alembic are prefixed with `survapp_` (`survapp_camera_master`, etc.). | Schema Naming Inconsistency |

---

## 23. Technical Debt

1. **Security & Secrets:** Default credentials in `.env.example`; private TLS key committed in git history (`surv/certs/star_bsnl_co_in.key`).
2. **Unused Infrastructure:** Idle Redis container consuming system memory.
3. **Database Naming Inconsistencies:** Mixture of `survapp_` prefix for older tables and clean names for newer tables.
4. **Duplicate Scripts:** `seed_hierarchy.py` exists in both `surv/app/scripts/seed_hierarchy.py` and `surv/scripts/seed_hierarchy.py`.

---

## 24. End-to-End Data Flows

### Flow 1: Live Viewing (HLS)
Browser requests signed HLS URL -> FastAPI validates permission & camera scope -> issues stream JWT -> browser connects to `nginx_hls:8080/hls/{cam_id}/index.m3u8?token={token}` -> `nginx_hls` forwards to MediaMTX -> MediaMTX webhook validates token with FastAPI `/api/v1/auth/stream` -> video fragments delivered to browser.

### Flow 2: Continuous Recording Pipeline
MediaMTX slices 60s fMP4 segment -> triggers `notify_segment.sh` -> `upload_to_minio.py` uploads segment & `.json` sidecar to MinIO -> publishes event to Kafka `recording.segments` -> verifies file size & deletes local file -> `segment_db_consumer.py` consumes event, checks motion intervals, classifies (`motion`|`guard`|`full`), and inserts row into `survapp_video_segment`.

---

## 25. How to Run

### 1. Launching Central Hub
```bash
cd /opt/surv-learn/surv
cp -n .env.example .env
docker compose up -d --build
docker compose exec app alembic -c alembic.ini upgrade head
docker compose exec app python3 /code/scripts/seed_hierarchy.py
```

### 2. Launching Portable Edge NVR (Separate VM)
```bash
cd /opt/surv-learn/edge-nvr
cp .env.example .env
docker compose up -d --build
```

### 3. Launching Edge Site Simulation
```bash
cd /opt/surv-learn/edge-sim
./generate_clips.sh
python3 register_site.py --site SITE01
./sim_manage.sh up SITE01
```

---

## 26. What Is Currently Working (Code-Backed)

1. **Dynamic Camera Ingestion:** RTSP, RTSPS, and RTMP ingestion via MediaMTX without restarting containers.
2. **Stream Authentication:** Token-gated HLS and WebRTC delivery with MediaMTX webhook authorization.
3. **Automated Recording & Tagging:** Segment upload to MinIO, Kafka messaging, and motion-based segment classification in PostgreSQL.
4. **Multi-Tenant Hierarchy & RBAC:** BSNL organization closure tree, 14 roles, 16 permissions, and fine-grained camera access filtering.
5. **Camera Health Monitoring:** Online/offline status transition detection, uptime tracking, and webhook alerting.
6. **Edge Appliance Stack:** Heartbeat reporting, remote configuration pull, local video retention, and critical clip offloading.
7. **Full Web Application:** Complete 13-page React dashboard with live grid, 24-hr timeline playback, fleet controls, and user administration.

---

## 27. What Is Not Verified / Requires Manual Verification

1. **Live ONVIF Hardware Interoperability:** Requires physical ONVIF cameras on the network to test WS-Notification event polling in production conditions.
2. **Headscale WireGuard WAN Routing:** Requires connecting remote Tailscale nodes across the public internet to verify STUN/DERP NAT traversal.
3. **Production Wildcard TLS:** Requires testing `*.bsnl.co.in` certificate validation against an authoritative BSNL DNS resolver.

---

## 28. Resume-Point Verification Checklist

- [ ] **Docker Containers:** Run `docker compose ps` in `surv/` and confirm services are healthy.
- [ ] **Database Migration Head:** Run `docker compose exec app alembic -c alembic.ini current` and confirm revision is `0010_recording_mode`.
- [ ] **Kong Perimeter Proxy:** Test login: `curl -s -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"changeme"}'`.
- [ ] **MediaMTX Control API:** Verify active paths: `curl -s http://localhost:9997/v3/paths/list`.
- [ ] **MinIO Bucket Availability:** Confirm `recordings` and `snapshots` buckets exist.
- [ ] **Kafka Cluster Status:** Inspect topic partition health using Kafka UI on `:8090`.
- [ ] **Automated Tests:** Execute `PYTHONPATH=surv surv/.venv/bin/pytest surv/app/tests/`.
