# Sarvanetra Monorepo Layout

| Directory / File | Purpose |
|---|---|
| [`PROJECT_STATE.md`](PROJECT_STATE.md) | **Canonical Project State** — Verified as-built implementation, architecture, services, database, APIs, and known issues |
| [`PROJECT_ROADMAP.md`](PROJECT_ROADMAP.md) | **Canonical Development Roadmap** — Priorities (P0–P3), technical debt, testing, security, and next steps |
| [`DOCUMENTATION_CLEANUP.md`](DOCUMENTATION_CLEANUP.md) | **Documentation Audit Trail** — Record of kept, merged, archived, and deleted historical documentation |
| [`surv/`](surv/) | **Hub** — FastAPI, Kong, Postgres, MinIO, MediaMTX (VLAN cameras), Kafka, React UI |
| [`edge-nvr/`](edge-nvr/) | **Portable edge NVR** — site appliance (MediaMTX + edge-agent). Deploy on a separate VM. |
| [`edge-sim/`](edge-sim/) | **Edge simulation** — ffmpeg fake cameras for testing edge sites against the hub |
| [`docs/setup/`](docs/setup/) | BSNL dedicated network briefing and Pan-India hierarchy architectural models |
| [`docs/archive/`](docs/archive/) | Historical implementation plans, phase notes, and superseded specifications |

---

## Canonical Project Documents

- **What exists now:** [`PROJECT_STATE.md`](PROJECT_STATE.md)
- **What needs to happen next:** [`PROJECT_ROADMAP.md`](PROJECT_ROADMAP.md)

---

## Quick Start

### 1. Central Hub
```bash
cd surv
docker compose up -d --build
docker compose exec app alembic -c alembic.ini upgrade head
docker compose exec app python3 /code/scripts/seed_hierarchy.py
```

### 2. Edge NVR (Separate VM)
```bash
cd edge-nvr
cp .env.example .env   # Configure SITE_CODE, SITE_TOKEN, HUB_API_URL
docker compose up -d --build
```

### 3. Simulate Edge Site
```bash
cd edge-sim
# See edge-sim/README.md for simulation instructions
```
