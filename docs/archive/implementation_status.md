> **Superseded:** See [sarvanetra_final_implementation_plan.md](sarvanetra_final_implementation_plan.md) for the authoritative implementation plan. This document is retained as historical reference.

# Sarvanetra — As-Built Status & Completed Work
## Comprehensive Handoff Document (for continued planning)

*Companion documents: `sarvanetra_edge_vpn_extension_plan.md` (Phases 12–14: edge NVR + WireGuard overlay), `sarvanetra_mobile_app_spec.md` (Expo/React Native app spec). This document describes everything that exists and works today, so those two plans can be finalized against an accurate baseline rather than the aspirational architecture doc alone.*

---

## 1. What Sarvanetra Is

Sarvanetra is a containerised, self-hosted CCTV/NVR management platform: RTSP/ONVIF camera ingestion, live streaming (HLS/WebRTC), recording with a queryable timeline, motion detection, multi-tenant access control, and a web dashboard — all running on open-source components under Docker Compose, originally scoped to operate entirely inside a private BSNL FTTH surveillance VLAN with no public internet exposure.

Two things are true simultaneously about the codebase today, and both matter for planning:

1. **The single-tenant core platform (Phases 0–8) is fully built, deployed, and running** on a VM at `10.44.0.209`, verified end-to-end with a real camera.
2. **A second, larger body of work — a full multi-tenant/RBAC re-architecture (Phases A–I from a separate implementation plan) — has also been substantially built** (migrations, models, routers, frontend pages, typed API client) but its integration/verification status is unconfirmed, and three further phases (9–11: health monitoring, retention, hardening) were designed but never started.

---

## 2. Deployment Context

| Item | Value |
|---|---|
| Environment | Single Ubuntu VM, IP `10.44.0.209` |
| Orchestration | Docker Compose (single `docker-compose.yml`, growing per phase) |
| Access | Dev PC at `10.44.0.55` reaches all service UIs directly by VM IP:port (no TLS yet) |
| Intended production network | Isolated BSNL surveillance VLAN (VLAN 200, illustrative ID), no public IP, no NAT to internet — see §8 |
| Backend framework | **FastAPI** (the original plan considered Django; FastAPI was what was actually built) |
| Frontend framework | **React 18 + TypeScript + Vite 5 + Tailwind CSS v4** |
| Kafka mode | KRaft (no Zookeeper), image `apache/kafka:3.7.0`, container name **`surv_kafka`** (see gotcha in §7) |

---

## 3. Architecture As Built

```
Browser (dev PC) ──HTTP──▶ Kong (:8000) ──┬──▶ FastAPI "app" (internal :8000, no host port)
                                          ├──▶ Nginx HLS proxy (:8080 direct / via Kong /hls)
                                          └──▶ (JWT plugin validates all routes except /auth/login, /auth/stream, /health)

FastAPI ──▶ PostgreSQL (:5432)     FastAPI ──▶ Redis (:6379, cache/session)
FastAPI/MediaMTX ──▶ MinIO (:9000 API / :9001 console) — recordings/snapshots buckets, presigned URLs

MediaMTX (:8554 RTSP ingest, :8888 HLS, :8889 WebRTC, :9997 mgmt API)
  ├─ pulls RTSP from camera(s), e.g. rtsp://admin:admin@10.44.0.219:554/unicaststream/1
  ├─ records 60s fmp4 segments → runOnRecordSegmentComplete hook → upload_to_minio.py → MinIO
  └─ authMethod: http → calls FastAPI /api/v1/auth/stream webhook per stream request

Kafka (surv_kafka:9092, KRaft) — topics: camera.motion, camera.status, recording.segments
  ├─ ONVIF Producer → camera.motion
  ├─ Motion Consumer → PostgreSQL survapp_motion_event
  ├─ Segment DB Consumer → PostgreSQL survapp_video_segment
  └─ Status Monitor → publishes camera.status + writes camera_master.is_online directly

Kong (JWT-issuing is FastAPI's job; Kong only validates) + Konga admin UI (:1337)
```

**Key data flows (all verified working):**
- **Live stream:** Camera → MediaMTX RTSP → HLS segments → Nginx (custom redirect/CORS rewrite) → Browser, via a per-camera short-lived JWT stream token issued by `GET /api/v1/streams/{cam_id}/hls-url`.
- **Recording:** MediaMTX segment-complete hook → `upload_to_minio.py` → MinIO `recordings` bucket + Kafka event → `segment_db_consumer` → `survapp_video_segment` row → timeline API.
- **Motion:** Camera ONVIF pull-point → ONVIF Producer → Kafka `camera.motion` → Motion Consumer → `survapp_motion_event`.
- **Auth:** `POST /auth/login` (open Kong route) → FastAPI signs JWT → Kong's JWT plugin validates on every subsequent request. Both FastAPI and Kong read the same `KONG_JWT_ISSUER` / `KONG_JWT_SECRET` env vars — single source of truth for the signing secret.

---

## 4. Phase-by-Phase Completion Status

| Phase | Scope | Status |
|---|---|---|
| 0 | Environment bootstrap, directory structure, `.env`, Postgres + Redis | ✅ Complete |
| 1 | MediaMTX camera ingestion, custom `Dockerfile.mediamtx` (adds Python+kcat), Nginx HLS proxy | ✅ Complete |
| 2 | MinIO object storage, `recordings`/`snapshots` buckets, presigned URL pattern | ✅ Complete |
| 3 | Recording pipeline via `runOnRecordSegmentComplete` hook (not polling) | ✅ Complete |
| 4 | Kafka event bus, KRaft mode, 3 topics | ✅ Complete |
| 5 | ONVIF motion pipeline + camera status monitor | ✅ Complete |
| 6 | FastAPI integration layer, all core routers/models/endpoints | ✅ Complete |
| 7 | Kong + JWT auth, stream token flow, MediaMTX auth webhook | ✅ Complete |
| 8 | React/Vite/Tailwind v4 frontend, all core pages | ✅ Complete |
| **9** | **Camera health monitoring** (status log history, uptime %, health dashboard, FCM/webhook alerting) | ❌ **Not started** |
| **10** | **Retention/cleanup/storage governance** (`minio_cleaner.py` retention enforcement, per-camera retention) | ❌ **Not started** (`minio_cleaner.py` exists only as an empty file) |
| **11** | **Hardening** (TLS, non-root containers, CORS lockdown, MinIO IAM least-privilege, secrets audit, prod compose override) | ❌ **Not started** |
| A–I (Multi-tenant/RBAC) | Organizations, customers, roles/permissions, camera groups, audit log, BSNL org hierarchy | ⚠️ **Backend substantially built, integration unverified** (see §6) |
Phase 9 to 11 has been completed.
### 4.1 Real-world bugs already hit and fixed (Phases 0–8)

These are resolved, but worth carrying forward as institutional knowledge — several are the kind of thing that reappears when new services or a new deployment target are added:

| Bug | Cause | Fix |
|---|---|---|
| Kafka UI / consumers can't find broker | Wrong hostname (`kafka:9092` instead of container name `surv_kafka:9092`) | Every Kafka client must use `surv_kafka:9092` |
| `KafkaConsumer.subscribe()` TypeError | `on_assign`/`on_revoke` kwargs are a `confluent-kafka` API, not `kafka-python-ng` | Pass topic directly into the `KafkaConsumer` constructor |
| `status_monitor` crashes on boot | Missing `psycopg2-binary` in `workers/requirements.txt` | Added dependency |
| Recurring `[API] path not found` in MediaMTX logs | Stale test camera row (`cam_001`) polled after the FK-constrained row couldn't be hard-deleted | Soft-delete (`is_active=false`) instead of hard delete |
| Alembic `Can't locate revision` despite file existing | Docker build cache served a stale image layer | Always `docker compose build --no-cache app` before `db_migrate` after adding new files |
| HLS proxy returns 404 | `nginx:alpine`'s stock `default.conf` intercepts requests before the custom `hls.conf` | Mount an empty file over `default.conf` |
| HLS redirect drops to port 80 | `proxy_redirect` re-absolutized using `$host` (no port) instead of `$http_host` | `proxy_redirect / $scheme://$http_host/hls/;` |
| Duplicate CORS headers / browser rejects response | Both MediaMTX and Nginx add `Access-Control-Allow-Origin` | `proxy_hide_header` MediaMTX's CORS headers before Nginx adds its own |
| Frontend still hits old URL after `.env` change | Vite bakes `VITE_*` vars in at build time, not runtime | `docker compose build --no-cache frontend` required after any `VITE_*` change |

---

## 5. Technology Stack (confirmed, as deployed)

| Concern | Choice |
|---|---|
| API framework | FastAPI 0.111, Uvicorn, SQLAlchemy 2.0 (async, `asyncpg`) + Alembic (sync, `psycopg2-binary`) |
| Auth | `python-jose` JWT (HS256), `passlib[bcrypt]`, Kong JWT plugin for gateway-level validation |
| Object storage clients | `boto3` (FastAPI app) **and** the official `minio` SDK (`upload_to_minio.py` worker) — two different clients for two different components, intentional, not a bug |
| Kafka client | `kafka-python-ng` (drop-in replacement for unmaintained `kafka-python`); broker auto-detects as `2.6.0` — never hardcode `api_version` |
| Media server | MediaMTX (`bluenviron/mediamtx`), custom image adding Python 3.12 + `kcat` for hook scripts |
| Frontend build | Vite 5 + `@tailwindcss/vite` plugin (Tailwind v4 — no `tailwind.config.ts`, no PostCSS config; theme lives in an `@theme {}` CSS block) |
| Frontend data layer | TanStack Query v5, React Router v6, HLS.js for playback, `date-fns`, `lucide-react` |
| Gateway | Kong 3.6 + Postgres-backed config, Konga for admin UI |

---

## 6. Multi-Tenant / RBAC Backbone — What Exists, What's Unverified

A separate implementation plan (Phases A–I, referenced but not reproduced here) designed a full organizational hierarchy (BSNL Circle → BA → SSA → District → Site/NOC), customers with sites, granular roles/permissions, camera groups, and an audit log. The build status:

**Confirmed present in the codebase:**
- Migrations `0003_company_hierarchy` and `0004_bsnl_masters`
- All new SQLAlchemy models for organizations, customers, roles, permissions, camera groups, audit log
- All new routers: `organizations`, `customers`, `roles`, `audit`, `camera_groups`, `bsnl`
- All new frontend pages designed (Organizations, Customers, Users, Roles, Audit Log, Camera Groups) per `implementation_plan_frontend.md`
- A fully-typed API client covering the new entities
- A seed script for the BSNL org hierarchy and default roles/permissions, in `app/scripts/`

**Not confirmed — needs verification before building anything further on top of it:**
- Whether migrations `0003`/`0004` are actually **applied** to the running database (`alembic current` needs to be run and checked against `0004_bsnl_masters (head)`)
- Whether the seed script has been **run** (it's designed to be idempotent, but idempotent ≠ already executed)
- Whether `GET /api/v1/cameras/` and other camera-scoped endpoints actually **enforce** access control via `get_accessible_cameras()` from `access_service.py`, or still use an unscoped `select(Camera)`
- Whether the frontend's `Login.tsx`/`ProtectedRoute.tsx`/`Sidebar.tsx` were actually updated to store and act on `roles`/`permissions` from the JWT (the frontend implementation plan describes this work as needed; it is not confirmed done, unlike the backend pieces above which were confirmed present)

> [!IMPORTANT]
> Any further planning (including the edge/VPN extension) should treat "multi-tenant verification" as a **prerequisite checkpoint**, not a parallel task — the new `nvr_node`/fleet model in the edge extension plan hangs directly off `customer_site`, so if that table's data isn't actually populated and enforced yet, fleet management has nothing real to attach to.

---

## 7. Database (as built)

### 7.1 Core tables (Phases 0–8)
```
survapp_camera_master     -- camera registry (cam_id, cam_ip, onvif creds, is_active, is_online, last_seen)
survapp_motion_event      -- ONVIF motion start/end records
survapp_video_segment     -- recording segment index, populated by Kafka consumer, feeds timeline API
survapp_user              -- operator/admin accounts (legacy flat `role` string field)
```

### 7.2 Multi-tenant tables (migrations 0003/0004 — presence confirmed, application unverified per §6)
Organizations, customer/customer_site, roles, permissions (with role↔permission mapping), camera_groups (with camera assignment), audit_log, plus BSNL master data (circles, business areas) referenced by `bsnl` router.

### 7.3 Designed but not yet migrated (Phase 9/10, not started)
```sql
-- from the Phase 9 plan, migration 0005 — not applied, file may not even exist yet
camera_status_log (id, camera_id, status, changed_at, duration_seconds)
survapp_camera_master.retention_days  -- additive column, default 30
```

### 7.4 Known field-naming gotcha
The original build plan's risk log flags a mismatch risk between `camera_id` and `cam_id` naming (`VideoSegment.__str__` referencing the wrong attribute in an earlier draft). Worth a quick grep across the current codebase before extending the schema further, since the edge/fleet plan introduces yet more camera-referencing tables (`nvr_camera_map`, `backup_clip`).

---

## 8. Network & Security Model (as designed for BSNL deployment)

The production target (not yet realized — current VM is a flat dev network) is a **dedicated surveillance VLAN** (illustrative VLAN 200) provisioned by BSNL at the OLT/GPON layer, terminating in a BNG context with **no default route to the internet**. Properties:

- Camera RTSP and video storage traffic never traverse BSNL's internet-facing routing context
- No public IP, no NAT, no port-forwarding possible on the surveillance server
- Layer-2 subscriber isolation at the OLT prevents cross-VLAN traffic to the standard internet VLAN
- A formal BSNL NOC/RPoP coordination checklist exists (VLAN ID assignment, GEM port provisioning, BNG context creation, ONT LAN-port mapping) but has **not been executed** — this is a real-world provisioning dependency, not a software task, and its timeline is outside engineering's control

**Current gap this creates for the product roadmap:** this network model assumes every camera and every viewer sits inside BSNL's own infrastructure. It has no answer for a customer premises on a normal retail internet connection, and no answer for a phone on mobile data wanting to view a live feed from anywhere — which is exactly the gap the edge-NVR + WireGuard-overlay extension plan (companion document) is designed to close, without weakening the "no unauthenticated party can reach a video stream, no inbound ports required anywhere" principle this VLAN design was built around.

### 8.1 Port reference (current dev VM)

| Port | Service | Reachable from |
|---|---|---|
| 3000 | Frontend | Dev PC |
| 8000 | Kong Proxy | Dev PC (FastAPI is internal-only behind it) |
| 8001 | Kong Admin | Dev PC / admin |
| 8443 | Kong Proxy TLS | Reserved for Phase 11, not active |
| 8080 | Nginx HLS | Dev PC |
| 8554 | MediaMTX RTSP | Camera network |
| 8888/8889/9997 | MediaMTX HLS/WebRTC/mgmt API | Internal / debug |
| 9000/9001 | MinIO API / console | Dev PC / admin |
| 8090 | Kafka UI | Dev PC |
| 1337 | Konga | Admin |
| 5432/6379/9092 | Postgres/Redis/Kafka | Internal Docker network only |

---

## 9. API Surface (as built, Phase 0–8)

```
# Open (no JWT required)
POST   /api/v1/auth/login
POST   /api/v1/auth/stream            ← MediaMTX webhook only
GET    /health
GET    /api/v1/health/

# Protected (Kong JWT plugin)
GET    /api/v1/health/services
GET|POST|PATCH|DELETE  /api/v1/cameras/[...]   ← write ops admin-only
GET    /api/v1/streams/{cam_id}/hls-url | webrtc-url | snapshot-url
GET    /api/v1/recordings/{cam_id}/timeline?date=YYYY-MM-DD
GET    /api/v1/recordings/{cam_id}/download?object_key=...
GET    /api/v1/motion/  | /motion/active | /motion/{event_id}
GET    /api/v1/auth/me
GET|POST /api/v1/auth/users            ← admin-only
```

Plus the multi-tenant routers referenced in §6 (`organizations`, `customers`, `roles`, `audit`, `camera_groups`, `bsnl`) whose exact route list should be pulled from the live OpenAPI schema (`/docs`) rather than assumed, given the verification gap noted above.

---

## 10. Frontend (as built, Phase 8)

| Page | Route | Auth |
|---|---|---|
| Login | `/login` | — |
| Live View | `/` | ✅ |
| Playback (DVR) | `/playback` | ✅ |
| Motion Alerts | `/motion` | ✅ |
| Cameras | `/cameras` | ✅ (write: admin only) |
| Users | `/users` | ✅ (admin only) |

Designed but **not confirmed wired** (per §6): Organizations, Customers, Users (expanded multi-tenant version), Roles & Permissions, Audit Log, Camera Groups — pages exist per the frontend implementation plan's file list, but `lib/auth.ts`, permission-aware `Sidebar.tsx`, and enriched `Login.tsx`/`ProtectedRoute.tsx` need a verification pass.

---

## 11. Already-Designed, Not-Yet-Built Work (full detail in companion docs)

To avoid duplicating content, only summarized here — see the named documents for full specs:

1. **Phase 9 — Camera Health Monitoring** *(original implementation plan, this repo's docs)*: `camera_status_log` table, expanded `/health/cameras/` endpoints with uptime %, `notifier.py` (FCM HTTP v1 or webhook fallback — **open decision: no Firebase project confirmed yet**), Health dashboard frontend page.
2. **Phase 10 — Retention & Storage Governance**: implement the currently-empty `minio_cleaner.py`, per-camera `retention_days`, scheduled cleaner service in Compose.
3. **Phase 11 — Hardening**: TLS (self-signed vs. Let's Encrypt — **open decision**), non-root Dockerfiles, CORS lockdown to `FRONTEND_ORIGIN`, MinIO least-privilege IAM user instead of root creds, `docker-compose.prod.yml`, secrets audit, structured logging, secret-rotation runbook.
4. **Phases 12–14 — Edge NVR + VPN Overlay + Commercial Hardening** *(`sarvanetra_edge_vpn_extension_plan.md`)*: site-premises NVR appliance (stripped-down MediaMTX + a new `edge-agent` service, local SQLite, no Kafka/MinIO/Kong at the edge), a self-hosted Headscale/WireGuard overlay network as the only path between hub, edge sites, and mobile clients, critical-clip backup-to-hub, and usage metering for commercial billing.
5. **Mobile App** *(`sarvanetra_mobile_app_spec.md`)*: Expo/React Native app with an embedded WireGuard client (Expo Modules API + Config Plugin over the official `WireGuardKit`/`com.wireguard.android` libraries, session-scoped keys, UI-driven tunnel lifecycle) and a QR-first/OCR-fallback "add camera by photographing its serial number" onboarding flow.

---

## 12. Consolidated Open Decisions (carried forward from all planning docs)

> [!IMPORTANT]
> **Migration verification (Phase 9+ prerequisite).** Run `alembic current` against the live DB; confirm it shows `0004_bsnl_masters` as head before any Phase 9/edge work touches the schema further.

> [!IMPORTANT]
> **Seed script execution.** Confirm whether `scripts/seed_hierarchy.py` has actually been run against the live database, not just written.

> [!IMPORTANT]
> **Access-control enforcement audit.** Confirm `get_accessible_cameras()` is actually used in `GET /cameras/` and equivalent endpoints, not a raw unscoped query.

> [!IMPORTANT]
> **FCM vs. webhook for Phase 9 alerting.** No Firebase project/service-account confirmed yet — default to webhook-based alerting (`ALERT_WEBHOOK_URL`) unless one is provided, and note that the mobile app's own push notifications (FCM/APNs, per the mobile spec) are a related but separate concern from this camera-offline alert channel.

> [!IMPORTANT]
> **TLS approach for Phase 11.** Self-signed (fits the current LAN/VLAN-only deployment) vs. Let's Encrypt (needs a public domain) — recommendation on file is self-signed with a documented upgrade path.

> [!IMPORTANT]
> **Production target ambiguity.** Is the current VM the permanent production host, or does this move to different hardware/cloud before go-live? Affects Phase 11's network-hardening rules and the edge plan's hub placement.

> [!IMPORTANT]
> **Overlay network technology (edge/VPN plan).** Headscale (recommended — lighter, RBAC bridge built by us) vs. NetBird (built-in group ACLs/SSO).

> [!IMPORTANT]
> **Mobile VPN embedding approach (mobile spec).** Confirmed decision: embed a plain WireGuard peer (not a full Tailscale-protocol client) pointed at the hub — flagged as revisitable only if direct low-latency mobile-to-edge P2P live view becomes a hard requirement.

> [!WARNING]
> **CORS is currently wide open** (`allow_origins=["*"]`) in `main.py` — this is a known, tracked gap closed by Phase 11, not an oversight, but worth flagging if any external-facing testing happens before Phase 11 lands.

> [!WARNING]
> **`minio_cleaner.py` is empty** — there is currently **no automated retention enforcement running**. Storage will grow unbounded until Phase 10 ships. If disk space is a near-term concern, this should be prioritized ahead of new feature work.

---

## 13. Repository Layout (as built, Phase 0–8 baseline)

```
surv/
├── docker-compose.yml
├── .env / .env.example
├── Dockerfile.mediamtx / Dockerfile.worker / Dockerfile.frontend
├── mediamtx/mediamtx.yml
├── nginx/{nginx.conf, empty.conf, conf.d/{hls.conf, frontend.conf}}
├── kong/setup-kong-jwt.sh
├── scripts/{camera_ready.sh, camera_down.sh, notify_segment.sh, seed_hierarchy.py}
├── workers/{upload_to_minio.py, snapshot_worker.py, status_monitor.py, minio_cleaner.py [EMPTY], requirements.txt}
├── onvif_producer/  ·  motion_consumer/
├── app/                              # FastAPI
│   ├── alembic/versions/{0001_initial, 0002_add_users, 0003_company_hierarchy, 0004_bsnl_masters}.py
│   ├── models/{camera, user, organization*, customer*, role*, camera_group*, audit*}.py
│   ├── routers/{health, cameras, streams, recordings, motion, auth, stream_auth, organizations*, customers*, roles*, audit*, camera_groups*, bsnl*}.py
│   ├── services/{minio_service, mediamtx_service, auth_service, access_service}.py
│   └── workers/segment_db_consumer.py
├── frontend/src/
│   ├── api/client.ts  ·  lib/auth.ts*
│   ├── components/{Sidebar, HLSPlayer, Timeline, StatusBadge, ProtectedRoute}.tsx
│   └── pages/{Login, LiveView, Playback, MotionEvents, Cameras, Users, Organizations*, Customers*, Roles*, AuditLog*, CameraGroups*}.tsx
└── recordings/                       # bind mount

  * = multi-tenant addition, presence confirmed per §6 but wiring/enforcement unverified
```

---

*This document reflects the state of the codebase as understood from the as-built status plan, the original build plan, the frontend/backend implementation plans, and the architecture/network briefs already in the project. It intentionally does not repeat the full detail of the edge-NVR/VPN or mobile-app designs — those live in their own documents and should be read alongside this one.*
