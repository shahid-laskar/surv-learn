# Edge NVR Simulation

Simulates customer-site edge NVRs with **ffmpeg RTSP cameras** against a remote Sarvanetra hub. Uses the portable stack from [`../edge-nvr/`](../edge-nvr/).

## Prerequisites

- Hub running at `HUB_API_URL` (e.g. `http://10.44.0.209:8000/api/v1`)
- Docker Compose v2

## Setup

1. **Provision NVR on hub** (NVR Fleet UI) → copy `site_code` and `site_token`.

2. **Create site env files** (one per simulated site):

```bash
cp site-envs/site-01.env.example site-envs/site-01.env
# Edit SITE_CODE, SITE_TOKEN, HUB_API_URL, unique RTSP/HLS/MGMT ports
```

3. **Generate sample video clips** (once):

```bash
./generate_clips.sh
```

4. **Register simulated cameras on hub** and assign to NVR (via hub API or SQL).

5. **Start a site** (on this VM or a separate LAN VM):

```bash
./sim_manage.sh up SITE01
```

## Multi-VM testing

Copy the entire `edge-nvr/` + `edge-sim/` directories to another machine on the same LAN. Point `HUB_API_URL` at the hub's LAN IP. No hub code required on the edge VM.

## Commands

```bash
./sim_manage.sh up SITE01      # start one site
./sim_manage.sh down           # stop all
./sim_manage.sh status
./sim_manage.sh logs SITE01 edge-agent
./sim_manage.sh verify         # query hub nvr_node table
```

Optional VPN: `docker compose --profile vpn --env-file site-envs/site-01.env up -d`
