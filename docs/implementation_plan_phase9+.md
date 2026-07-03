# Sarvanetra — Phase 9 → Production: Implementation Plan

## Current State (As-Built — Phase 8 Complete + Multi-tenant Backbone)

**Infrastructure:** Phases 0–8 are fully complete and running on VM `10.44.0.209`.  
**Surprise bonus:** The multi-tenant/RBAC architecture from `implementation_plan.md` (Phases A–I) has **also been partially built** — migrations 0003 + 0004 exist, all new models exist, all new routers exist (`organizations`, `customers`, `roles`, `audit`, `camera_groups`, `bsnl`), all new frontend pages exist, and the API client is fully typed for the new entities.

**What is actually missing / incomplete:**

| Area | Status |
|------|--------|
| Phase 9: Camera Health Monitoring | ❌ Not built |
| Phase 10: Retention/Cleanup/Storage | ❌ Not built (`minio_cleaner.py` is empty) |
| Phase 11: Hardening & Production Readiness | ❌ Not built |
| Multi-tenant Phase A-I: DB migration + seed | ⚠️ Migrations exist but migrations 0003/0004 **may not be applied** — needs verification |
| Multi-tenant Phase A-I: Access control enforcement | ⚠️ Routers exist but need verification that `get_accessible_cameras()` is used correctly |
| Multi-tenant Phase A-I: Seed script | ⚠️ Exists in `app/scripts/` — needs to be run |
| `CameraStatusLog` table | ❌ Not in any migration |
| `notifier.py` (FCM push worker) | ❌ Not built |
| `minio_cleaner.py` | ❌ Empty file — not implemented |
| Health dashboard frontend page | ❌ Not built |
| Retention settings UI | ❌ Not built |
| Production hardening (TLS, non-root, CORS) | ❌ Not built |

---

## User Review Required

> [!IMPORTANT]
> **Migrations 0003 and 0004** — We need to verify whether they have been applied to the running database. If not, running them may fail if the DB has live data that conflicts. The plan includes a verification step before any migration work.

> [!IMPORTANT]
> **FCM Push Notifications** — Phase 9 in the original plan calls for Firebase Cloud Messaging for mobile camera offline alerts. This requires a Firebase project and `FCM_SERVER_KEY`. The plan includes FCM but we should use the **modern FCM HTTP v1 API** (the legacy `fcm.googleapis.com/fcm/send` is deprecated). **Decision needed: Do you have a Firebase project / service account JSON?** If not, we'll implement the alerting framework and use a placeholder (email/webhook) instead of FCM.

> [!WARNING]
> **TLS in Phase 11** — Enabling Kong HTTPS requires valid TLS certificates. For the current VM-only deployment (no public DNS), we use **self-signed certs**. If you want production-grade TLS (Let's Encrypt), you need a public domain name pointing to the server. **Decision: self-signed or public domain?**

> [!WARNING]
> **CORS in Phase 11** — `allow_origins=["*"]` is currently set in `main.py`. Phase 11 tightens this to the frontend's origin. Make sure the `FRONTEND_ORIGIN` env var is set correctly before deploying.

> [!NOTE]
> **Camera-specific retention** — Phase 10 adds `retention_days` to `survapp_camera_master`. This is an additive migration (0005). No existing data is affected.

---

## Open Questions

> [!IMPORTANT]
> **Q1: FCM notification delivery** — Do you have a Firebase project with a service account? If yes, provide the `google-services.json` path. If no, we'll implement webhook-based alerting instead (POST to a configurable URL).

> [!IMPORTANT]
> **Q2: TLS certificates** — Self-signed (for LAN deployment, which is what this is) or Let's Encrypt (requires public domain)? Recommend: self-signed for now, documented upgrade path.

> [!IMPORTANT]
> **Q3: Production target** — Is the VM deployment the final production target, or will this be moved to a cloud server? This affects Phase 11's network hardening rules.

> [!IMPORTANT]
> **Q4: Seed script** — The BSNL org hierarchy and role/permission seed script exists. Should it be run as part of this plan, or is it already done?

---

## Proposed Changes

---

### Phase 9 — Camera Health Monitoring

#### 9.1 Database — Migration 0005

#### [MODIFY] [0005_camera_health.py](file:///opt/surv-learn/surv/app/alembic/versions/0005_camera_health.py) [NEW]

New Alembic migration creating:

- **`camera_status_log`** — immutable history of every online/offline transition:
  ```sql
  CREATE TABLE camera_status_log (
    id          BIGSERIAL PRIMARY KEY,
    camera_id   INTEGER NOT NULL REFERENCES survapp_camera_master(id),
    status      VARCHAR(20) NOT NULL,   -- 'online' | 'offline'
    changed_at  TIMESTAMPTZ DEFAULT NOW(),
    duration_seconds INTEGER            -- filled on transition OUT of this status
  );
  CREATE INDEX ON camera_status_log(camera_id, changed_at DESC);
  ```

- **`retention_days`** column on `survapp_camera_master`:
  ```sql
  ALTER TABLE survapp_camera_master ADD COLUMN retention_days INTEGER DEFAULT 30;
  ```

#### 9.2 Backend

#### [MODIFY] [models/camera.py](file:///opt/surv-learn/surv/app/models/camera.py)
- Add `retention_days = Column(Integer, default=30)` to `Camera`
- Add new `CameraStatusLog` model

#### [MODIFY] [workers/status_monitor.py](file:///opt/surv-learn/surv/workers/status_monitor.py)
- Add `insert_status_log(conn, camera_id, status)` — writes row to `camera_status_log` on **every transition**
- Add `update_duration_seconds()` — fills `duration_seconds` on the *previous* log row when status changes (so we know how long a camera was offline)
- Add `offline_alert_check()` — if camera has been offline for >5 minutes and a prior alert hasn't been sent, trigger the notifier

#### [NEW] [workers/notifier.py](file:///opt/surv-learn/surv/workers/notifier.py)
New standalone module (imported by `status_monitor`):
- `send_camera_offline_alert(camera_id, cam_path, offline_minutes)` — sends to all active `device_token` rows for users with `camera.view` permission on that camera
- Supports both **FCM HTTP v1** (if `FIREBASE_SERVICE_ACCOUNT_JSON` env is set) and **webhook** fallback (`ALERT_WEBHOOK_URL`)
- Stores `Notification` row in DB for in-app notification bell

#### [MODIFY] [routers/health.py](file:///opt/surv-learn/surv/app/routers/health.py)
Expand the health router:
```
GET /api/v1/health/cameras/        — all cameras with is_online, last_seen, offline_minutes
GET /api/v1/health/cameras/{id}/history  — last N status log entries for a camera (uptime chart data)
GET /api/v1/health/workers/        — Kafka + MinIO connectivity check (already exists, keep)
GET /api/v1/health/storage/        — MinIO bucket sizes + recording dir disk usage
```

#### [NEW] [schemas/health.py](file:///opt/surv-learn/surv/app/schemas/health.py)
- `CameraHealthOut` — `camera_id`, `name`, `is_online`, `last_seen`, `offline_minutes`, `uptime_pct_24h`
- `StatusLogEntry` — `status`, `changed_at`, `duration_seconds`
- `StorageStats` — `bucket`, `total_size_gb`, `object_count`, `oldest_object`

#### 9.3 Frontend

#### [NEW] [pages/Health.tsx](file:///opt/surv-learn/surv/frontend/src/pages/Health.tsx)
Health dashboard page:
- **Camera health grid** — cards for each camera: green (online) / red (offline) with offline duration
- **Uptime sparklines** — 24-hour uptime bars per camera (built from `/health/cameras/{id}/history`)
- **Worker status** — Kafka / MinIO health indicators
- **Storage stats** — MinIO bucket size, oldest recording age
- Polls every 30 seconds

#### [MODIFY] [App.tsx](file:///opt/surv-learn/surv/frontend/src/App.tsx)
Add `/health` route

#### [MODIFY] [Sidebar.tsx](file:///opt/surv-learn/surv/frontend/src/components/Sidebar.tsx)
Add "Health" nav item with `HeartPulse` icon, showing offline camera count as badge

#### [MODIFY] [api/client.ts](file:///opt/surv-learn/surv/frontend/src/api/client.ts)
Add `fetchCameraHealth()`, `fetchCameraHistory()`, `fetchStorageStats()` functions

---

### Phase 10 — Retention, Cleanup & Storage Governance

#### 10.1 Backend

#### [MODIFY] [workers/minio_cleaner.py](file:///opt/surv-learn/surv/workers/minio_cleaner.py)
Implement the currently-empty file as a full retention cleaner:
- `clean_old_recordings(s3, conn)` — paginates MinIO `recordings` bucket, deletes objects older than each camera's `retention_days`, marks `deleted_at` in `survapp_video_segment`
- `apply_minio_lifecycle_policy(s3, bucket, days)` — sets S3 lifecycle rule as a safety net
- `clean_orphaned_markers()` — removes `.uploaded` marker files whose `.mp4` is gone
- `log_storage_stats(s3, conn)` — logs bucket size + per-camera storage breakdown
- `main()` — runs every `CLEANER_RUN_INTERVAL_HOURS` (default: 6h), re-reads `retention_days` from DB each cycle so changes take effect without restart

#### [MODIFY] [routers/cameras.py](file:///opt/surv-learn/surv/app/routers/cameras.py)
- `PATCH /cameras/{id}` — add `retention_days` to the patchable fields

#### [MODIFY] [schemas/camera.py](file:///opt/surv-learn/surv/app/schemas/camera.py)
- `CameraOut` — expose `retention_days`
- `CameraUpdate` — add `retention_days: int | None`

#### 10.2 Docker Compose

#### [MODIFY] [docker-compose.yml](file:///opt/surv-learn/surv/docker-compose.yml)
Add `minio_cleaner` service:
```yaml
  minio_cleaner:
    build:
      context: .
      dockerfile: Dockerfile.worker
    container_name: surv_minio_cleaner
    restart: unless-stopped
    command: python /app/minio_cleaner.py
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ROOT_USER=${MINIO_ROOT_USER}
      - MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}
      - MINIO_BUCKET_RECORDINGS=${MINIO_BUCKET_RECORDINGS}
      - RETENTION_DAYS=${RETENTION_DAYS}
      - CLEANER_RUN_INTERVAL_HOURS=6
    networks: [surv_net]
    depends_on:
      minio:
        condition: service_healthy
      postgres:
        condition: service_healthy
```

#### 10.3 Frontend

#### [MODIFY] [pages/Cameras.tsx](file:///opt/surv-learn/surv/frontend/src/pages/Cameras.tsx)
- Add `retention_days` field to the camera edit form (number input, 1–365 days)
- Display retention policy badge on each camera card

---

### Phase 11 — Hardening, Security & Production Readiness

#### 11.1 TLS — Kong HTTPS

#### [MODIFY] [kong/setup-kong-jwt.sh](file:///opt/surv-learn/surv/kong/setup-kong-jwt.sh)
Add self-signed cert generation and Kong TLS configuration:
- Generate self-signed cert for the VM IP / domain
- Register cert with Kong Admin API (`POST /certificates`)
- Update Kong proxy listen to include `:8443`

#### [NEW] [scripts/gen-self-signed-cert.sh](file:///opt/surv-learn/surv/scripts/gen-self-signed-cert.sh)
One-shot cert generation script using `openssl`:
```bash
openssl req -x509 -newkey rsa:4096 -keyout kong/certs/server.key \
  -out kong/certs/server.crt -days 365 -nodes \
  -subj "/CN=10.44.0.209" \
  -addext "subjectAltName=IP:10.44.0.209"
```

#### 11.2 Non-root Dockerfiles

#### [MODIFY] [Dockerfile.worker](file:///opt/surv-learn/surv/Dockerfile.worker)
Add `USER appuser`:
```dockerfile
RUN useradd -m -u 1001 appuser
USER appuser
```

#### [MODIFY] [Dockerfile.mediamtx](file:///opt/surv-learn/surv/Dockerfile.mediamtx)
Note: MediaMTX needs root for port binding. Use `EXPOSE` without `USER` change, but restrict capabilities in compose.

#### [MODIFY] [app/Dockerfile](file:///opt/surv-learn/surv/app/Dockerfile)
Add non-root user.

#### 11.3 CORS Tightening

#### [MODIFY] [app/main.py](file:///opt/surv-learn/surv/app/main.py)
```python
FRONTEND_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://10.44.0.209:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,   # no more wildcard
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)
```

#### [MODIFY] [.env](file:///opt/surv-learn/surv/.env) / [.env.example](file:///opt/surv-learn/surv/.env.example)
Add `CORS_ALLOWED_ORIGINS=http://10.44.0.209:3000`

#### 11.4 MinIO IAM Policies (Least-Privilege)

#### [MODIFY] [docker-compose.yml](file:///opt/surv-learn/surv/docker-compose.yml) — `minio_init` service
Create a dedicated MinIO service account with restricted policy instead of using root creds for workers:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket"],
      "Resource": ["arn:aws:s3:::recordings/*", "arn:aws:s3:::snapshots/*"]
    }
  ]
}
```
- Create `surv_worker` MinIO user with this policy
- New env vars: `MINIO_WORKER_USER`, `MINIO_WORKER_PASSWORD`

#### 11.5 Kafka SASL (Optional / Low Priority)
Document the SASL/SCRAM config steps but mark as **optional** for LAN deployment. Kafka SASL adds significant operational complexity for marginal gain on a private network.

#### 11.6 Environment & Secrets Audit

#### [MODIFY] [app/config.py](file:///opt/surv-learn/surv/app/config.py)
- Add `cors_allowed_origins: str = "http://10.44.0.209:3000"`
- Add `firebase_service_account_json: str | None = None`
- Add `alert_webhook_url: str | None = None`
- Add `minio_worker_user: str = "minioadmin"` (fallback until IAM is set)
- Ensure all secrets fail fast (`Field(...)` with no default) in prod mode

#### [NEW] [docker-compose.prod.yml](file:///opt/surv-learn/surv/docker-compose.prod.yml)
Production override file:
- Removes external port exposure for postgres, redis, kafka, minio console
- Sets `DEBUG=false`
- Sets `CORS_ALLOWED_ORIGINS` to actual domain
- Adds `restart: always` everywhere
- Adds resource limits (memory caps per container)

#### 11.7 Logging

#### [MODIFY] [app/main.py](file:///opt/surv-learn/surv/app/main.py)
Add structured JSON logging with rotating file handler for production.

#### 11.8 Rate Limiting (Kong)

Rate limiting is already set globally in `setup-kong-jwt.sh`. Phase 11 adds **per-consumer** rate limits and documents the burst-test procedure.

#### 11.9 Secret Rotation Guide

#### [NEW] [docs/secret_rotation.md](file:///opt/surv-learn/docs/secret_rotation.md)
Step-by-step guide to rotate JWT signing secret without downtime:
1. Generate new secret
2. Update `SECRET_KEY` and `KONG_JWT_SECRET` in `.env`
3. Re-run Kong setup script to update consumer credential
4. Restart `app` and `kong-config`
5. All existing sessions become invalid (users log in again)

---

### Multi-tenant Verification & Completion

Before Phase 9 work begins, we need to verify the partially-built multi-tenant work:

#### [VERIFY] Database migration status
```bash
docker compose exec app alembic current
# Should show: 0004_bsnl_masters (head)
# If it shows 0002_add_users, need to run 0003 and 0004
```

#### [VERIFY] Seed script
```bash
docker compose exec app python3 scripts/seed_hierarchy.py
# Should be idempotent — safe to re-run
```

#### [VERIFY] Access control enforcement
Check that `GET /api/v1/cameras/` uses `get_accessible_cameras()` from `access_service.py`, not a raw `select(Camera)`.

---

## Migration Sequence

```
0001_initial          ← applied ✅
0002_add_users        ← applied ✅
0003_company_hierarchy ← status: verify
0004_bsnl_masters     ← status: verify
0005_camera_health    ← NEW (this plan)
```

---

## Implementation Order (Execution Sequence)

### Step 1 — Verification (no code changes)
1. Run `alembic current` to check migration status
2. Run seed script
3. Smoke-test a SUPER_ADMIN login to confirm roles/permissions in JWT
4. Confirm `GET /cameras/` is filtered by `get_accessible_cameras()`

### Step 2 — Phase 9: Camera Health (Backend)
1. Write migration `0005_camera_health.py`
2. Add `CameraStatusLog` model to `models/camera.py`
3. Add `retention_days` to `Camera` model
4. Update `status_monitor.py` to write status logs + compute durations
5. Build `workers/notifier.py`
6. Expand `routers/health.py` with new endpoints
7. Add `schemas/health.py`
8. Apply migration + restart services

### Step 3 — Phase 9: Camera Health (Frontend)
1. Add health API functions to `api/client.ts`
2. Build `pages/Health.tsx` dashboard
3. Add to `App.tsx` routes
4. Add to `Sidebar.tsx` nav

### Step 4 — Phase 10: Retention Cleanup
1. Implement `workers/minio_cleaner.py`
2. Add `retention_days` to camera schemas + router
3. Add `minio_cleaner` service to `docker-compose.yml`
4. Update camera edit form in `Cameras.tsx`
5. Deploy and verify cleaner runs

### Step 5 — Phase 11: Hardening
1. CORS tightening in `main.py` + `.env`
2. Non-root Dockerfiles
3. MinIO IAM policy + dedicated worker user
4. Self-signed cert generation + Kong TLS
5. `docker-compose.prod.yml`
6. Secrets audit + `config.py` cleanup
7. Logging configuration
8. Write `docs/secret_rotation.md`

---

## Verification Plan

### Automated Tests

```bash
# After migration 0005
docker compose build app
docker compose run --rm db_migrate
docker compose exec postgres psql -U surv -d sarvanetra -c "\dt" | grep camera_status_log

# Phase 9 — health endpoints
curl -H "Authorization: Bearer <token>" http://10.44.0.209:8000/api/v1/health/cameras/
# Expect: array of camera objects with is_online, offline_minutes

# Phase 9 — status log writes
# Take camera offline (kill ffmpeg test stream)
# Wait 35 seconds, then:
docker compose exec postgres psql -U surv -d sarvanetra -c \
  "SELECT * FROM camera_status_log ORDER BY changed_at DESC LIMIT 5;"

# Phase 10 — cleaner
docker compose exec minio_cleaner python3 /app/minio_cleaner.py --dry-run
# Expect: lists objects that would be deleted without deleting them

# Phase 11 — CORS
curl -H "Origin: http://evil.example.com" http://10.44.0.209:8000/api/v1/cameras/
# Expect: 403 or missing Access-Control-Allow-Origin

# Phase 11 — TLS
curl -k https://10.44.0.209:8443/api/v1/health/
# Expect: {"status": "ok"}
```

### Manual Verification

- Camera going offline → `camera_status_log` row appears within 35 seconds
- Camera offline >5 minutes → push notification received (or webhook called)
- MinIO cleaner deletes segments past their camera's `retention_days`
- `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d` brings up hardened stack
- Internal services (postgres, redis, kafka) NOT reachable from outside Docker network
- All Dockerfiles run as non-root user (verify with `docker compose exec <svc> whoami`)

---

## Key Files Summary

| Phase | Files | Status |
|-------|-------|--------|
| 9 (Health) | `0005_camera_health.py`, `models/camera.py`, `workers/status_monitor.py`, `workers/notifier.py`, `routers/health.py`, `schemas/health.py`, `pages/Health.tsx`, `App.tsx`, `Sidebar.tsx`, `api/client.ts` | 🔲 |
| 10 (Retention) | `workers/minio_cleaner.py`, `routers/cameras.py`, `schemas/camera.py`, `docker-compose.yml`, `pages/Cameras.tsx` | 🔲 |
| 11 (Hardening) | `app/main.py`, `app/config.py`, `Dockerfile.worker`, `app/Dockerfile`, `docker-compose.prod.yml`, `scripts/gen-self-signed-cert.sh`, `kong/setup-kong-jwt.sh`, `docs/secret_rotation.md`, `.env.example` | 🔲 |
| Multi-tenant verify | Migration status check, seed run, access control audit | ⚠️ |
