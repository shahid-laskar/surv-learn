# Sarvanetra Monorepo Layout

| Directory | Purpose |
|-----------|---------|
| [`surv/`](surv/) | **Hub** — FastAPI, Kong, Postgres, MinIO, MediaMTX (VLAN cameras), React UI |
| [`edge-nvr/`](edge-nvr/) | **Portable edge NVR** — site appliance (MediaMTX + edge-agent). Deploy on a separate VM. |
| [`edge-sim/`](edge-sim/) | **Edge simulation** — ffmpeg fake cameras for testing edge sites against the hub |
| [`docs/status/`](docs/status/) | Implementation plans and phase completion notes |

**Authoritative plan:** [docs/status/sarvanetra_final_implementation_plan.md](docs/status/sarvanetra_final_implementation_plan.md)

## Quick start

**Hub:** `cd surv && docker compose up -d`

**Edge NVR (separate VM):** `cd edge-nvr && cp .env.example .env && docker compose up -d --build`

**Simulate edge site:** `cd edge-sim && see README.md`
