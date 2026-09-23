# Phase A — Baseline Verification Gate (Completed)

**Branch:** `feature/phaseA`  
**Date:** 2026-07-09

## Code Changes

| File | Change |
|------|--------|
| `surv/app/services/access_service.py` | Added `ensure_camera_accessible()` helper |
| `surv/app/routers/cameras.py` | Access check on GET/PATCH/DELETE by `cam_id` |
| `surv/app/routers/streams.py` | Access check on HLS, WebRTC, snapshot endpoints |
| `surv/app/routers/recordings.py` | Access check on timeline and download |
| `surv/app/routers/motion.py` | Filter list/active by accessible cameras; check on GET by id |
| `surv/app/tests/test_access_enforcement.py` | Unit tests for access helper |

## Exit Criteria

| Criterion | Status |
|-----------|--------|
| `get_accessible_camera_ids` enforced on cameras, streams, recordings, motion | ✅ Done |
| `ensure_camera_accessible` used on all per-camera endpoints | ✅ Done |
| Alembic at `0007_mobile_devices` | ⏳ Run on deployment VM |
| BSNL seed script executed | ⏳ Run on deployment VM if org count is 0 |
| Unit tests for `ensure_camera_accessible` | ✅ 3 passed locally |

## Verification Commands (run on hub VM)

```bash
cd /opt/surv-learn/surv

# Migration head
docker compose exec app alembic -c alembic.ini current
# EXPECT: 0007_mobile_devices (head)

# Org hierarchy
docker compose exec postgres psql -U surv sarvanetra -c "SELECT COUNT(*) FROM organization;"
# If 0: docker compose exec app python scripts/seed_hierarchy.py

# RBAC grep audit
rg "ensure_camera_accessible|get_accessible_camera_ids" app/routers/
# EXPECT: cameras, streams, recordings, motion (+ health already had checks)

# Unit tests (local or in container)
pip install pytest pytest-asyncio
cd app && PYTHONPATH=/code pytest tests/test_access_enforcement.py -v

# Smoke test after rebuild
docker compose build app && docker compose up -d app
```

## Next Phase

Proceed to **Phase B — Complete Edge NVR Core** on a new branch after merging `feature/phaseA`.
