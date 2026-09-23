# SARVANETRA — Phase 1 Deep Repository Archaeology & Reconnaissance Report
**Target Repository:** `/opt/surv-learn`  
**Branch:** `agent/sarvanetra-tender-readiness`  
**Baseline Commit:** `80280fc`  
**Execution Context:** Autonomous Lead Engineering Team  
**Verification Date:** September 23, 2026  
**Automated Tests Verified:** 35 passed, 0 failed (7 test suites, 2.79s execution)

---

## 1. Executive Architecture Map

SARVANETRA is a distributed Video Surveillance and Network Video Recorder (NVR) platform structured in three tiers:

```
                                      CLIENTS & EDGE SITES
  ┌─────────────────────────────────┐                       ┌───────────────────────────────┐
  │         Web Browser SPA         │                       │      Portable Edge NVR        │
  │    (React 18 / Vite / Tailwind) │                       │  (MediaMTX + edge-agent)      │
  └────────┬───────────────────┬────┘                       └──────────────┬────────────────┘
           │ :3000 / :3443     │ :8000 (Kong Proxy)                        │
           │ (Direct SPA)      │                                           │ :8000 (Kong) / :8002 (Direct)
           ▼                   ▼                                           │ (X-Site-Token)
  ┌────────────────────────────────────────────────────────────────────────▼────────────────┐
  │                                     KONG API GATEWAY (:8000 / :8443)                     │
  │  - Routes /api to FastAPI (surv-api: http://app:8000)                                   │
  │  - Routes /hls to Nginx HLS proxy (hls-stream: http://nginx_hls:80)                     │
  │  - Validates JWT tokens on protected routes (api-route, hls-route)                      │
  │  - Open routes: /api/v1/auth/login, /api/v1/auth/stream, /health, /api/v1/health       │
  │  - Edge open routes: /api/v1/fleet/heartbeat, /api/v1/motion/edge, fleet config/backup  │
  │  - Rate Limiting (1000 req/min), CORS handling, Wildcard TLS (*.bsnl.co.in)             │
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
  │  - Segments     │   │  - Lifecycle Hooks: camera_ready.sh, camera_down.sh (kcat)        │
  │  - User Sessions│   └──────────────────────┬────────────────────────────────────────────┘
  └─────────────────┘                          │
                                               │ Video Segments (.mp4) + Sidecars (.json)
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

## 2. Confirmed (Working & Verified in Code)

1. **Alembic Database Schema & ORM:**
   - 10 linear Alembic revisions (`0001` through `0010_recording_mode`) establishing core surveillance and multi-tenant schema.
   - Models in `surv/app/models/` (`camera.py`, `organization.py`, `rbac.py`, `user.py`, `nvr.py`, `edge_segment.py`, `mobile.py`) map to tables: `survapp_camera_master`, `survapp_motion_event`, `survapp_video_segment`, `camera_status_log`, `organization`, `organization_closure`, `customer`, `customer_site`, `circle_master`, `ba_master`, `survapp_role`, `survapp_permission`, `survapp_role_permission`, `survapp_user_role`, `survapp_user_camera`, `camera_group`, `camera_group_mapping`, `user_group_mapping`, `user_session`, `device_token`, `audit_log`, `notification`, `password_reset_token`, `nvr_node`, `nvr_camera_map`, `backup_clip`, `edge_video_segment`, `mobile_device`.
2. **FastAPI Application Core & RBAC:**
   - 15 operational routers (`surv/app/routers/`): `auth.py`, `cameras.py`, `streams.py`, `recordings.py`, `motion.py`, `health.py`, `fleet.py`, `organizations.py`, `customers.py`, `roles.py`, `camera_groups.py`, `audit.py`, `bsnl.py`, `mobile.py`, `stream_auth.py`.
   - Access service (`surv/app/services/access_service.py`): Hierarchical tree traversal via `organization_closure`, direct user-camera overrides (`survapp_user_camera`), camera groups (`camera_group_mapping`), and role permissions (`SUPER_ADMIN`, `NATIONAL_NOC`, `camera.view`, `camera.live`, etc.).
   - Unit test verification (`surv/app/tests/test_access_service.py`, `test_access_enforcement.py`, `test_auth.py`): All 14 tests passing for permission enforcement, token encoding/decoding, token expiration, tampering checks, and session revocation.
3. **Core Media Ingestion & Token-Gated Delivery:**
   - Dynamic path creation in MediaMTX (`surv/app/services/mediamtx_client.py`): RTSP pull (`rtsp://`), RTSPS pull (`rtsps://` with fallback to port 322), and RTMP push (`source: publisher` on port 1935).
   - Stream authentication: MediaMTX calls FastAPI webhook `/api/v1/auth/stream` (`surv/app/routers/stream_auth.py`) for every viewer session; verifies signed stream JWTs containing `cam_id` and action (`read`).
   - HLS Delivery: Proxied via `nginx_hls:8080/hls` with fMP4 1s segment slicing and 200ms parts.
4. **Continuous & Motion Recording Pipeline:**
   - MediaMTX slices 60s fMP4 chunks -> `notify_segment.sh` -> `surv/workers/upload_to_minio.py` uploads `.mp4` and `.json` sidecar to MinIO `recordings` bucket.
   - Kafka event emitted on `recording.segments` topic.
   - Local segment unlinked after MinIO byte size verification.
   - `surv/app/workers/segment_db_consumer.py` consumes `recording.segments`, checks motion intervals (`survapp_motion_event`), tags recording type (`full`, `motion`, `guard`), and writes row to `survapp_video_segment`.
5. **Camera Health & Lifecycle Monitoring:**
   - `surv/workers/status_monitor.py` verifies reachability via MediaMTX API and TCP port checks, computes offline/online duration, and writes audit records to `camera_status_log`.
   - Alert notifications dispatched via `surv/workers/notifier.py` (webhook + DB notification).
6. **Edge NVR Control Plane & Agent Stack:**
   - Hub fleet management API (`surv/app/routers/fleet.py`): Provisioning, `SITE_TOKEN` validation via `X-Site-Token`, heartbeat ingest, config sync, camera assignment, and backup clip metadata registry.
   - Edge agent (`edge-nvr/edge-agent/`): 7 concurrent asyncio loops (heartbeat, config pull, ONVIF motion, status sync, local SQLite retention, critical clip backup).
   - Unit tests pass for site token validation, unprovisioned node rejection, and heartbeat processing (`surv/app/tests/test_fleet.py`).
7. **Frontend SPA:**
   - Complete 13-page React 18 / TypeScript 5 / Tailwind CSS v4 web application (`surv/frontend/src/`).
   - Includes live video grid (1x1, 2x2, 3x3), HLS.js video player, WebRTC viewer, 24-hr interactive timeline (`Timeline.tsx`), segment filtering (`full`/`motion`/`guard`), NVR fleet management, and audit logs.

---

## 3. Incorrect (Documented vs Actual Discrepancies)

1. **Redis Usage:**
   - *Documented Claim:* Redis is utilized for session management and distributed caching.
   - *Codebase Reality:* Service `surv_redis` (`redis:7-alpine`) runs in Docker Compose, but `redis` is **never imported anywhere** in `surv/app/` or workers, and is absent from `requirements.txt`. All user sessions are managed exclusively inside PostgreSQL table `user_session`.
2. **Konga Admin UI:**
   - *Documented Claim:* Konga administrative UI exposed on port 1337 (`docs/archive/sarvanetra_architecture.md`).
   - *Codebase Reality:* Konga container does not exist in any Compose file (`docker-compose.yml`, `docker-compose.prod.yml`). Kong is managed via shell script `setup-kong-jwt.sh`.
3. **Django Framework:**
   - *Documented Claim:* Old architectural docs claim "Django / FastAPI hybrid".
   - *Codebase Reality:* Pure FastAPI 2.0.0; Django was never introduced.
4. **Browser HLS Traffic Path:**
   - *Documented Claim:* Kong routes HLS traffic via `hls-route` on port 8000.
   - *Codebase Reality:* Kong configuration has `hls-route`, but `surv/.env.example` and `surv/frontend/.env` route the browser directly to `nginx_hls:8080/hls` to bypass gateway buffering and latency overhead.
5. **Database Table Prefix Inconsistency:**
   - Historical tables use `survapp_` prefix (`survapp_camera_master`, `survapp_user`, `survapp_motion_event`, `survapp_video_segment`, `survapp_role`, `survapp_permission`), whereas newer tables use plain names (`organization`, `customer`, `nvr_node`, `mobile_device`, `camera_status_log`). Documentation inconsistently refers to both.
6. **Kafka Camera Status Consumer:**
   - *Documented Claim:* MediaMTX ready/notReady events published to Kafka `camera.status` drive online/offline state.
   - *Codebase Reality:* Shell hook `camera_ready.sh` publishes to `camera.status` using `kcat`, but **no Kafka consumer exists** for `camera.status`. Health tracking is actually done by polling in `status_monitor.py`.

---

## 4. Outdated / Stale Files

1. **Archive Documentation (`docs/archive/`):** 22 superseded markdown files containing obsolete architecture diagrams, dead Django references, and invalid phase completion claims.
2. **Duplicate Seeding Script:** `surv/app/scripts/seed_hierarchy.py` was retained in the app directory while canonical seeding was referenced in `surv/scripts/`.
3. **Pydantic V1 Deprecation Warnings:**
   - `surv/app/config.py`: `class Config:` instead of Pydantic v2 `ConfigDict`.
   - `surv/app/schemas/camera.py`: Deprecated `example=` kwargs in `Field(...)` and `class Config:`.
   - `surv/app/routers/recordings.py`: Deprecated `example=` in `Query(...)` (should be `examples=`).
4. **Legacy User Model Columns:** `survapp_user.role` (string) and `survapp_user.full_name` retained in `surv/app/models/user.py` alongside newer `survapp_user_role` and `first_name`/`last_name`.

---

## 5. Broken / Buggy Implementation

1. **Alembic vs SQLAlchemy Model Constraint Discrepancies:**
   - **`nvr_camera_map`:** Model (`surv/app/models/nvr.py:36-37`) specifies `ondelete="CASCADE"` for both foreign keys (`nvr_node_id`, `camera_id`). Alembic migration `0006_edge_fleet.py:40-41` omitted `ondelete="CASCADE"`. Cascade deletes work in Python ORM sessions but fail with foreign key violation errors on raw database deletes.
   - **`backup_clip`:** Model (`surv/app/models/nvr.py:47-48`) specifies `ondelete="SET NULL"` and `index=True` for foreign keys. Migration `0006_edge_fleet.py:48-49` omitted both `ondelete` and indices.
   - **`edge_video_segment`:** Model (`surv/app/models/edge_segment.py:16`) specifies `index=True` on `nvr_node_id`. Migration `0008_edge_segments.py` omitted index creation for `nvr_node_id`.
   - **Foreign Key Column Type Mismatch:** `survapp_user_camera.camera_id` and `camera_group_mapping.camera_id` are defined as `BigInteger`, whereas `survapp_camera_master.id` is `Integer`.
2. **Alembic Revision Tag Discrepancy:**
   - `surv/app/alembic/versions/0010_recording_mode.py`: Revision string is `"0010_recording_mode"` with `down_revision = "0009_stream_protocol"`, but the file docstring claims `Revision ID: 0010, Revises: 0009`.
3. **Kong Gateway Edge Agent Route Blocking (P0 Blocker):**
   - Edge agents sending `X-Site-Token` to port 8000 were rejected with 401 Unauthorized by Kong's JWT plugin because `/api/v1/fleet/*` and `/api/v1/motion/edge` were not in the open route bypass list. Script `surv/kong/setup-kong-jwt.sh` now configures `auth-open-route` with bypass paths for `/api/v1/fleet/heartbeat`, `/api/v1/motion/edge`, `~/api/v1/fleet/[^/]+/config`, and `~/api/v1/fleet/[^/]+/backup-clip`.

---

## 6. Partially Implemented

1. **Mobile Subsystem (`surv/app/routers/mobile.py`):**
   - Push notification token registration (`POST /api/v1/mobile/register-device`) and dashboard summary metrics (`GET /api/v1/mobile/dashboard-summary`) are implemented.
   - WireGuard VPN session allocation (`POST /api/v1/mobile/vpn-session`) and revocation (`DELETE /api/v1/mobile/vpn-session`) return `HTTP 501 Not Implemented`.
   - Mobile client application is 0% implemented (only architecture markdown in `docs/archive/mobile_desin.md`).
2. **Headscale Automated ACL Synchronization:**
   - `surv/app/services/acl_sync_service.py` contains working logic for namespace sanitization and ACL JSON structure generation (verified by 4 passing unit tests).
   - However, it lacks an event-driven trigger or cron worker to automatically execute when organizations or users are updated in PostgreSQL.
3. **Kafka `camera.status` Pipeline:**
   - MediaMTX shell hooks push ready/notReady events to Kafka `camera.status`, but there is no consumer service attached to this topic.

---

## 7. Missing Critical Components (Tender Scope)

1. **AI / Computer Vision Inference Engine (0% code):**
   - No ANPR / License Plate OCR engine.
   - No vehicle classification model (LMV, HMV, 2-wheelers, 3-wheelers, buses).
   - No traffic violation models (Helmet / Triple Riding detection).
   - No crowd density estimation or pedestrian flow analytics.
   - No video analytics models (perimeter breach, virtual tripwire, loitering, abandoned object).
2. **Parking Management Domain & Data Models (0% code):**
   - No tables, schemas, or routers for `parking_zone`, `parking_lane`, `parking_session`, `parking_tariff`, or `parking_slip`.
   - No zone allocation logic, occupancy accumulation, or entry/exit slip integration.
3. **Integrated Command & Control Centre (ICCC) / GIS Map (0% code):**
   - No GIS map component (Leaflet / MapLibre) on the frontend for Common Operating Picture (COP).
   - No spatial camera mapping, layer overlays, or GPS telemetry ingestion.
4. **Incident Management Workflow (0% code):**
   - No incident ticket state machine (`New` -> `Assigned` -> `Escalated` -> `Resolved` -> `Closed`).
   - No audit trail or SLA tracking for operator incident resolution.
5. **Tamper-Proof Evidence Packaging (0% code):**
   - No cryptographic signing service (SHA-256 / digital certificate), sidecar verification, or chain-of-custody export package generator.
6. **Bilingual User Interface (0% code):**
   - Frontend lacks `react-i18next` or localization files for English & Malayalam support.

---

## 8. Unknown / Requires Live Environment

1. **Live ONVIF Hardware Interoperability:** Requires physical ONVIF cameras on the network to test WS-Notification event polling in production conditions.
2. **Headscale WireGuard WAN Routing:** Requires connecting remote Tailscale nodes across the public internet to verify STUN/DERP NAT traversal.
3. **Production Wildcard TLS:** Requires testing `*.bsnl.co.in` certificate validation against an authoritative BSNL DNS resolver.

---

## 9. Security Risks

1. **Cleartext Camera Credentials in Database:**
   - `survapp_camera_master` stores `onvif_username` and `onvif_password` in plaintext VARCHAR columns (`surv/app/models/camera.py:39-40`), defaulting to `admin`/`admin`.
2. **Hardcoded Secrets & Default Passwords:**
   - `SYNC_DATABASE_URL` fallback in `surv/app/alembic/env.py:15` contains `"postgresql://surv:surv1234@postgres:5432/sarvanetra"`.
   - Default JWT secret in `.env.example` (`sarvanetra_jwt_secret_change_in_production_32bytes`).
   - MinIO credentials default to `minioadmin:minioadmin`.
3. **Committed Private TLS Keys:**
   - Wildcard private TLS certificate key (`surv/certs/star_bsnl_co_in.key`) is committed in the repository git history.
4. **Edge Authentication via Custom Header Without Signature:**
   - Edge endpoints rely strictly on `X-Site-Token: <secret>`. If intercepted or exposed in transit (over unencrypted LAN/HTTP), an attacker can spoof heartbeats or inject false motion events.
5. **CORS and Gateway Bypasses:**
   - Regex bypass in Kong for `~/api/v1/fleet/[^/]+/config` bypasses JWT verification at the gateway perimeter for any client presenting the path pattern.

---

## 10. Infrastructure Risks

1. **Single Points of Failure (SPOF):**
   - Primary database (`postgres:16`), object store (`minio`), and Kafka broker (`surv_kafka`) run as single standalone containers. No Patroni / repmgr failover, no MinIO erasure-coded multi-node cluster, and single-broker KRaft setup.
2. **Idle Resource Consumption:**
   - `surv_redis` container runs continuously and binds port 6379, consuming container memory without providing any active utility to the application.
3. **Unbounded Storage & Local Buffers:**
   - MediaMTX slices segments to local container disk `/recordings`. In the event of MinIO outage or slow network uploads, local storage can rapidly saturate the host filesystem.
4. **Lack of Resource Quotas:**
   - Containers in `surv/docker-compose.yml` lack memory and CPU reservation/limit parameters (`deploy.resources.limits`), exposing the host to OOM crashes under FFmpeg / MediaMTX load spikes.

---

## 11. Tender Gaps (Against Kerala Police PMS & Keltron AI EOI Requirements)

### A. Kerala Police PMS (Nilakkal / Sabarimala Tender A)
* **T1-PMS-001 to 007 (Parking Management):** **100% Gap.** No multi-zone allocation, no real-time occupancy tallying, no handheld Android POS slip generation, no 26-lane management.
* **T1-ANPR-001 to 003 (ANPR OCR & Vehicle Classification):** **100% Gap.** No license plate detection, no classification into LMV/HMV/2W/3W/Bus, no vehicle color/make/model recognition.
* **T1-ANPR-004 & 017 (Watchlist & Manual Plate Correction):** **100% Gap.** No stolen/suspicious vehicle hotlist matching; no authorized plate correction workflow with immutable audit logging.
* **T1-ANPR-010 & 011 (Violation Detection):** **100% Gap.** No "No Helmet" or "Triple Riding" computer vision models; no damaged plate anomaly detection.
* **T1-ANPR-013 & 014 (Fuzzy Search & Tamper-Proof Watermarking):** **100% Gap.** No Levenshtein distance 1-2 fuzzy plate search (`pg_trgm`); no cryptographic timestamp watermarking on captured vehicle snapshots.
* **T1-ANPR-015 (Bilingual UI):** **100% Gap.** No English + Malayalam language support.
* **T1-ANPR-018 (Crowd Estimation):** **100% Gap.** No vehicle-to-passenger multiplier algorithm (e.g. Bus = 50, Car = 5).
* **T1-CCTV-002 to 004 (Evidentiary Export & Retention):** **Partial Gap.** MinIO retention policy exists, but there is no tamper-proof cryptographic evidence export bundle tool.

### B. Keltron AI Surveillance EOI (Tender B)
* **T2-AI-001 to 008 (AI Video Analytics Engine):** **100% Gap.** Perimeter intrusion, virtual tripwire line crossing, loitering detection, abandoned object detection, human fall / medical emergency detection, abnormal behavior, and multi-camera Re-ID are completely absent.
* **T2-FLOW & CROWD (Crowd & Queue Analytics):** **100% Gap.** Bidirectional counting, crowd density regression (CSRNet), trajectory heatmaps, queue progression / wait-time analysis, and predictive crowd build-up modeling (LSTM/ARIMA) are absent.
* **T2-ICCC-001 to 003 (Command Centre, GIS & Incidents):** **100% Gap.** No GIS Common Operating Picture (COP) map dashboard; no multi-stage incident management workflow.
* **T2-MISSING-001 (Biometric Face Search):** **100% Gap.** No facial detection, embedding extraction, or vector search database (e.g. pgvector / Milvus).
* **T2-DRONE-001 & 002 (Drone Telemetry):** **Partial Gap.** RTMP streaming ingest is supported via MediaMTX, but MAVLink aerial telemetry overlay and mission control are absent.
* **T2-ARCH-003 & 004 (High Availability & Clustering):** **Infrastructure Gap.** System is configured for single-node container deployment; active-active HA database clustering and distributed broker quorums are absent.
* **T2-SEC-001 to 003 (Compliance & DPDP Act):** **Compliance Gap.** No PII redaction pipeline, consent registry, or formal CERT-In audit certification package.
