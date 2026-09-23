# Phase B — Edge NVR Core (Completed)

**Branch:** `feature/phaseB`  
**Date:** 2026-07-09

## Restructure

| Before | After |
|--------|-------|
| `edge-agent/` at repo root | `edge-nvr/edge-agent/` |
| `surv/docker-compose.edge.yml` | `edge-nvr/docker-compose.yml` |
| `surv/mediamtx/mediamtx-edge.yml` | `edge-nvr/mediamtx/mediamtx.yml` |
| `sim/` at repo root | `edge-sim/` (simulation only) |

Hub code (`surv/`) no longer contains edge deployment files. Copy `edge-nvr/` to a separate LAN VM for portable testing.

## Hub changes

- Migration `0008_edge_segments` — `site_enrollment_secret`, `edge_video_segment` table
- `fleet.py` — `X-Site-Token` auth, `overlay_ip` on heartbeat, camera assign/unassign APIs
- `motion.py` — `POST /motion/edge` for edge-agent sync
- `fleet_auth.py` — site token verification
- `NvrFleet.tsx` — shows `SITE_TOKEN` after provision
- ONVIF producer skips `nvr_node_id IS NOT NULL` cameras

## Edge agent (all loops implemented)

| Module | Status |
|--------|--------|
| `heartbeat.py` | Disk %, online cams, overlay IP, site token |
| `config_sync.py` | RTSP pull paths, SQLite cache |
| `motion_loop.py` | ONVIF workers (real cameras) |
| `motion_sync.py` | Push events to hub |
| `status_loop.py` | MediaMTX path readiness |
| `local_retention.py` | Filesystem cleanup by retention_days |
| `backup_uploader.py` | MinIO upload + hub metadata |
| `edge_db.py` | SQLite schema |

## Deploy edge NVR (separate VM)

```bash
cd edge-nvr
cp .env.example .env   # SITE_CODE, SITE_TOKEN, HUB_API_URL
docker compose up -d --build
```

## Simulate sites

```bash
cd edge-sim
cp site-envs/site-01.env.example site-envs/site-01.env
./generate_clips.sh
python3 register_site.py --site SITE01
./sim_manage.sh up SITE01
```

## Migration

```bash
docker compose -f surv/docker-compose.yml exec app alembic -c alembic.ini upgrade head
# Expect: 0008_edge_segments
```

## Next

Phase C — Headscale integration, real `overlay_ip` population, edge stream auth.
