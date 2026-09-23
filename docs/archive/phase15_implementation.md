> **Superseded:** See [sarvanetra_final_implementation_plan.md](sarvanetra_final_implementation_plan.md) for the authoritative implementation plan. This document is retained as historical reference.

# Edge NVR Simulation — Same VM (10.44.0.209)

Create a fully self-contained edge NVR simulation on the existing hub VM using Docker Compose isolated projects (`-p sim_site_XX`). Simulated cameras stream via ffmpeg + RTSP into per-site MediaMTX instances. Each site has its own edge-agent enrolling into Headscale. All traffic flows through the existing hub stack.

---

## User Review Required

> [!IMPORTANT]
> **No separate VM available.** Per `test_simulation.md §2`, a separate VM is recommended for true NAT-traversal testing. Since we're on the same VM, the Tailscale containers will join the overlay from `localhost` — the WireGuard tunnel still forms correctly (same host, loopback path), but DERP fallback and real NAT traversal won't be exercised until a second VM is added later. Everything else (edge-agent heartbeat, config-sync, MediaMTX recording, motion injection, ACL isolation) is fully testable this way.

> [!IMPORTANT]
> **Headscale TLS.** The existing `HEADSCALE_DOMAIN=10.44.0.209` uses a bare IP. Tailscale clients **require HTTPS with a valid cert** for `--login-server`. We'll re-configure headscale to serve over `vpn.sarvanetra.bsnl.co.in` using your `*.bsnl.co.in` cert (already in `certs/`). The Caddy reverse proxy will be updated to use the BSNL cert instead of its current self-signed `tls internal`. The DERP container already has cert support. DNS resolution for `vpn.sarvanetra.bsnl.co.in` → `10.44.0.209` is handled by the existing `dnsmasq` container.

> [!WARNING]
> **Port budget.** Each simulated site needs its own MediaMTX RTSP port (avoid collision with hub's `:8554`). We'll use ports `9554`, `9555`, `9556` for sites 01, 02, 03 respectively (only 3 sites for the initial simulation, matching §5.5 "single site, functional depth" then §5.6 scaling to all 3).

---

## Proposed Changes

### Component 1: Hub — Headscale TLS Fix (BSNL Cert)

#### [MODIFY] [Caddyfile](file:///opt/surv-learn/surv/caddy/Caddyfile)
Replace `tls internal` with the real BSNL wildcard cert so Tailscale clients can register.
Use `vpn.sarvanetra.bsnl.co.in` as the Headscale domain.

#### [MODIFY] [headscale/config.yaml](file:///opt/surv-learn/surv/headscale/config.yaml)
- Change `server_url` to `https://vpn.sarvanetra.bsnl.co.in`
- Enable `magic_dns: true` (per Phase 15 plan §6)

#### [MODIFY] [.env](file:///opt/surv-learn/surv/.env)
- Set `HEADSCALE_DOMAIN=vpn.sarvanetra.bsnl.co.in`
- Set `DERP_DOMAIN=vpn.sarvanetra.bsnl.co.in`

#### [MODIFY] [docker-compose.yml](file:///opt/surv-learn/surv/docker-compose.yml)
- Mount BSNL certs into Caddy container
- Mount certs into derp container (already done)

---

### Component 2: Sample Video Clip (for simulated cameras)

#### [NEW] `sim/clips/` directory
- Script `sim/generate_clips.sh`: uses `ffmpeg` to generate 3 sample clips (30s each, 480p, H.264), one per site with a burned-in site label (`SITE-01`, `SITE-02`, `SITE-03`) using `drawtext` filter. No re-encoding at runtime — each ffmpeg camera process just does `-c copy` loop from its site's clip.

---

### Component 3: Edge MediaMTX Config (per-site)

#### [NEW] `mediamtx/mediamtx-edge.yml`
A stripped-down MediaMTX config for edge sites:
- No MinIO upload (edge records locally)
- RTSP on `:8554` (per-container, host-mapped to `955X`)
- HLS on `:8888`
- API on `:9997`
- No auth (edge-internal only)
- `record: true` with `/recordings/%path/...` path

---

### Component 4: Per-Site Simulation Docker Compose

#### [NEW] `sim/docker-compose.sim.yml`
A parameterized compose file for one simulated edge site:
- `tailscale` container — enrolls into headscale at `vpn.sarvanetra.bsnl.co.in`
- `mediamtx-edge` — MediaMTX with edge config, host port `${RTSP_PORT}:8554`
- `edge-agent` — existing edge-agent image, `HUB_API_URL=http://10.44.0.209:8002/api/v1`
- `cam-01..cam-N` — one ffmpeg container per simulated camera, each doing:  
  `ffmpeg -stream_loop -1 -re -i /clips/site-XX.mp4 -c copy -f rtsp rtsp://mediamtx-edge:8554/SIMCAM-SITEXX-NN`
- `local_cleaner` — existing local_retention.py

#### [NEW] `sim/site-01.env`, `sim/site-02.env`, `sim/site-03.env`
Per-site `.env` files:
- `SITE_CODE=SITE01`
- `RTSP_PORT=9554`
- `CAMERAS_PER_SITE=3`  (3 cameras per site initially, matches Phase §5.5)
- `ENROLLMENT_PREAUTH_KEY=<generated>`
- `SITE_CLIP=site-01.mp4`

---

### Component 5: Headscale Pre-Auth Keys + Namespace

#### [NEW] `sim/setup_sim.sh`
Bootstrap script that:
1. Creates a `sim` namespace in headscale (if not exists)
2. Generates reusable pre-auth keys for each site
3. Writes keys into `sim/site-XX.env` files
4. Registers simulated cameras in the hub DB (via `POST /api/v1/cameras/` for each `SIMCAM-SITEXX-NN`)
5. Creates `nvr_node` entries via `POST /api/v1/fleet/register` (or equivalent)

---

### Component 6: Motion Event Injector

#### [NEW] `sim/inject_motion.py`
Script to inject synthetic motion events into the hub DB:
- Accepts `--site SITE01 --camera SIMCAM-SITE01-01 --interval 30`
- Writes directly to `motion_event` table (skips Kafka for simplicity)
- Runs as a one-shot or continuous loop

---

### Component 7: Simulation Management Script

#### [NEW] `sim/sim_manage.sh`
Convenience wrapper:
```
./sim_manage.sh up          # bring up all 3 sites
./sim_manage.sh down        # tear down all sites
./sim_manage.sh status      # show compose ps for all sites
./sim_manage.sh logs SITE01 # tail logs for one site
./sim_manage.sh chaos pause SITE01  # pause tailscale for WAN-drop test
./sim_manage.sh chaos unpause SITE01
```

---

## Verification Plan

### Automated Checks
```bash
# 1. Headscale sees all simulated NVR nodes online
docker compose exec headscale headscale nodes list

# 2. Hub heartbeat table updated
docker compose exec postgres psql -U surv sarvanetra -c "SELECT site_code, last_heartbeat FROM nvr_node ORDER BY last_heartbeat DESC;"

# 3. Cameras show as online in the hub
curl http://10.44.0.209:8000/api/v1/cameras/ | python3 -m json.tool | grep -E "(cam_id|is_online)"

# 4. HLS stream accessible for a simulated camera
curl -I http://10.44.0.209:8080/hls/SIMCAM-SITE01-01/index.m3u8

# 5. Recordings directory growing at each site
docker compose -p sim_site_01 exec mediamtx-edge ls /recordings/
```

### Manual Verification
- Open `http://10.44.0.209:3000` → NVR Fleet page → confirm 3 simulated sites appear with heartbeat timestamps
- Live view a simulated camera → confirm HLS stream plays with the burned-in `SITE-01` label
- Run WAN-drop test: `./sim_manage.sh chaos pause SITE01` → confirm local recording continues, hub shows stale heartbeat

---

## Open Questions

> [!IMPORTANT]
> How many cameras per site to start? Plan suggests 3 cameras × 3 sites = 9 total. This is conservative and fits on the same VM. We can scale to 10 cameras × 3 sites later. **Confirm or adjust.**

> [!IMPORTANT]
> The hub's `edge-agent` in `docker-compose.edge.yml` uses `HUB_API_URL: http://100.64.0.1:8000/api/v1` (the headscale overlay IP). Since we're on the same VM and not using the overlay for the hub side, we should use `http://10.44.0.209:8002/api/v1` (the FastAPI direct port). The edge-agent will still register its Tailscale IP as the NVR's overlay IP. **This is the correct approach — confirm.**

> [!IMPORTANT]
> Does `nvr_node` registration exist as an API endpoint yet? The plan references `POST /api/v1/fleet/register` — need to verify this exists or create the simulated nodes directly via SQL for the first pass.
