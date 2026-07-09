> **Superseded:** See [sarvanetra_final_implementation_plan.md](sarvanetra_final_implementation_plan.md) for the authoritative implementation plan. This document is retained as historical reference.

# Sarvanetra — Distributed Edge NVR & Secure Remote Access
## Extension Plan: Phases 12–14
*Building on the Phase 0–11 as-built platform and the multi-tenant backbone*

---

## 0. Why This Extension Exists

Everything built so far (Phases 0–11, multi-tenant A–I) assumes **one thing**: every camera can reach the central Sarvanetra server directly, over a network you control (the BSNL VLAN 200 intranet). That's correct for BSNL-owned sites. It breaks down for the next stage of the product:

1. **Customer premises** — a shop, office, or residence with its own internet connection (not on VLAN 200). You don't control their LAN, and their uplink is a normal, sometimes-flaky FTTH/4G internet line, not a private backbone.
2. **Continuity** — if the WAN link to the central server drops, cameras at that site must keep recording locally. A commercial NVR product that stops recording when the internet blips is not sellable.
3. **Remote/mobile viewing** — customers and BSNL staff want to open a phone app from anywhere and see live video or clips. Doing this by exposing Kong/HLS/RTSP on the public internet directly contradicts the "surveillance traffic never touches the public internet" principle that's central to the BSNL VLAN design (see `sarvanetra_technical_network_bf.md`).

The answer to all three is the same architectural move: **push a lightweight version of the stack to the edge (a "site NVR"), and connect every site NVR and every mobile client back to the central server over a private, encrypted overlay network (WireGuard) instead of the raw public internet.** The central server becomes a **fleet control plane + regional aggregator**, not the only place video ever lives.

This document is additive — nothing in Phases 0–11 needs to be re-architected. We are adding a new tier below the existing server, and a new access tier above it.

---

## 1. Target Architecture (End State)

```
                                   ┌───────────────────────────────────────────┐
                                   │            SARVANETRA HUB                 │
                                   │      (existing Phase 0-11 stack)          │
                                   │                                           │
                                   │  Kong · FastAPI · Postgres · Redis        │
                                   │  Kafka · MinIO (central/backup) · MediaMTX│
                                   │  (for BSNL-VLAN-native cameras, unchanged)│
                                   │                                           │
                                   │  + NEW: Overlay Control Plane             │
                                   │    - Headscale (self-hosted WireGuard     │
                                   │      coordination server)                 │
                                   │    - fleet_service (NVR registry, health) │
                                   │    - relay/broker for on-demand streaming │
                                   └───────────────┬───────────────┬───────────┘
                                                   │               │
                              WireGuard overlay    │               │  WireGuard overlay
                              (100.64.x.x tailnet) │               │  (100.64.x.x tailnet)
                    ┌──────────────────────────────┘               └───────────────────────────┐
                    │                                                                           │
        ┌───────────▼────────────┐                                              ┌───────────────▼──────────────┐
        │   SITE NVR (customer   │   ...repeat per site (10s–1000s)...          │   MOBILE APP (remote viewer)  │
        │   premises, on THEIR   │                                              │                               │
        │   internet connection) │                                              │  WireGuard client embedded    │
        │                        │                                              │  (or companion Headscale app) │
        │  MediaMTX (RTSP ingest,│                                              │  Talks ONLY to hub overlay IP │
        │   local record+HLS)    │                                              │  or, when authorized, directly│
        │  Local Postgres/SQLite │                                              │  to a site NVR's overlay IP   │
        │  (camera cfg, motion,  │                                              │                               │
        │   segment index)       │                                              │  No public-internet exposure  │
        │  Local retention       │                                              │  of RTSP/HLS at any point —   │
        │  cleaner (Phase 10     │                                              │  all video traverses the      │
        │   logic, local disk)   │                                              │  encrypted overlay only       │
        │  edge-agent:           │                                              └───────────────────────────────┘
        │   - heartbeat/health   │
        │   - config sync        │
        │   - critical-clip      │
        │     backup uploader    │
        │  ONVIF motion detector │
        │  (local, no Kafka      │
        │   dependency)          │
        └────────────────────────┘
                    │
             RTSP / ONVIF (LAN only,
             never leaves the site)
                    │
        ┌───────────▼────────────┐
        │      IP Cameras         │
        └─────────────────────────┘
```

**Key principle carried over from the BSNL brief:** raw camera video (RTSP/HLS) never rides the open internet in cleartext, and never rides it *at all* unless a viewer is actively watching. The WireGuard overlay is the only path in or out of a site NVR. There is no port-forwarding, no public IP requirement, and no inbound firewall rule needed at the customer's router — WireGuard/Headscale peers always dial *out* to the hub.

---

## 2. Component 1 — The Site NVR ("Edge Node")

### 2.1 What it is

A cut-down version of the existing Docker Compose stack, designed to run unattended on a small box (Intel N100 mini-PC, or a Raspberry Pi 5 / Jetson-class device for smaller sites) at the customer's premises.

| Existing Hub Service | Edge Equivalent | Notes |
|---|---|---|
| MediaMTX | **Same image**, same config pattern (`runOnRecordSegmentComplete` hook) | Ingests local cameras, records to local disk, serves local HLS/WebRTC |
| PostgreSQL | **PostgreSQL (lightweight) or SQLite** | Local-only schema: `camera_master`, `motion_event`, `video_segment`, `camera_status_log` — same table shapes as the hub, so sync logic is trivial |
| Kafka | **Removed.** Too heavy for a 1–8 camera edge box | Replaced with direct function calls / SQLite writes inside a single `edge-agent` process (see 2.3) |
| ONVIF Producer + Motion Consumer | Folded into `edge-agent` as one in-process loop | No message bus needed at this scale |
| MinIO Cleaner (Phase 10) | Same retention logic, pointed at local disk instead of a bucket | Runs against local `/recordings`, same `retention_days`-per-camera field |
| Kong | **Not needed locally.** The edge NVR has no public listener at all | Its only network egress is the outbound WireGuard tunnel to the hub |
| Nginx HLS proxy | Optional locally (LAN-only viewing at the site itself, e.g. a wall-mounted monitor) | Same config as `nginx/conf.d/hls.conf` |

### 2.2 Docker Compose footprint (edge)

```yaml
# docker-compose.edge.yml — deployed to the site box
services:
  wireguard-agent:      # headscale/tailscale client — brings up the overlay
    image: tailscale/tailscale:latest
    hostname: nvr-${SITE_CODE}
    environment:
      TS_AUTHKEY: ${ENROLLMENT_PREAUTH_KEY}     # one-time, issued by hub
      TS_EXTRA_ARGS: --login-server=https://vpn.sarvanetra.internal
    cap_add: [NET_ADMIN, NET_RAW]
    volumes: [ts_state:/var/lib/tailscale]
    restart: unless-stopped

  mediamtx:
    build: { context: ., dockerfile: Dockerfile.mediamtx }   # same image as hub
    network_mode: "service:wireguard-agent"   # optional: route via overlay netns
    volumes: [./mediamtx/mediamtx.yml:/mediamtx.yml:ro, recordings:/recordings, hls:/var/hls]

  edge-agent:
    build: { context: ./edge-agent }
    environment:
      SITE_CODE: ${SITE_CODE}
      HUB_API_URL: http://100.64.0.1:8000/api/v1     # hub's overlay IP, never public IP
      LOCAL_DATABASE_URL: sqlite:////data/edge.db
    volumes: [edge_data:/data, recordings:/recordings]
    depends_on: [mediamtx]

  local_cleaner:
    build: { context: ./workers, dockerfile: Dockerfile.worker }
    command: python minio_cleaner_local.py     # same retention algorithm, local FS target
    volumes: [recordings:/recordings, edge_data:/data]
```

Total footprint: 4 small containers, no Kafka/Zookeeper, no MinIO, no Postgres server process (SQLite file). Comfortably runs on 4GB RAM.

### 2.3 `edge-agent` — the one new piece of software

This is the only genuinely new backend service. Responsibilities:

1. **ONVIF motion loop** — same logic as `onvif_producer/onvif_motion_producer.py`, but writes directly to the local SQLite/Postgres `motion_event` table instead of publishing to Kafka.
2. **Status loop** — same logic as `workers/status_monitor.py`, writes to local `camera_status_log`.
3. **Heartbeat** — every 30s, `POST {HUB_API_URL}/fleet/heartbeat` over the WireGuard overlay with: site code, per-camera online/offline, disk usage %, uptime, agent version. This is the *only* thing that must reach the hub in real time.
4. **Config sync (pull)** — every few minutes, `GET {HUB_API_URL}/fleet/{site_code}/config` to pick up camera additions/edits, retention changes, and RBAC-driven "who can view this site" rules made centrally through the existing multi-tenant UI (Organizations/Customers/Camera Groups pages already built).
5. **Critical-clip backup (push)** — on a motion event, optionally upload a short clip (configurable: e.g. 15s pre/post-roll) to the hub's central MinIO `backup_clips` bucket, so a stolen/destroyed NVR box doesn't mean losing evidence of the incident that took it out. This is throttled and low-bandwidth — full recordings stay local; only flagged clips travel.
6. **Local retention enforcement** — reuses the Phase 10 `minio_cleaner.py` algorithm verbatim, just pointed at a local filesystem walk instead of an S3 `list_objects_v2` call.

### 2.4 Data model additions (Hub side)

New Alembic migration `0006_edge_fleet.py`:

```sql
CREATE TABLE nvr_node (
  id              SERIAL PRIMARY KEY,
  site_code       VARCHAR(50) UNIQUE NOT NULL,
  customer_site_id INTEGER REFERENCES customer_site(id),   -- ties into existing multi-tenant model
  overlay_ip      VARCHAR(50),           -- assigned by Headscale, e.g. 100.64.x.x
  wg_node_key     VARCHAR(200),          -- headscale node identifier
  hardware_label  VARCHAR(100),          -- "Intel N100", "RPi5", etc.
  agent_version   VARCHAR(50),
  last_heartbeat  TIMESTAMPTZ,
  disk_used_pct   NUMERIC(5,2),
  is_provisioned  BOOLEAN DEFAULT false,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE nvr_camera_map (
  nvr_node_id     INTEGER REFERENCES nvr_node(id),
  camera_id       INTEGER REFERENCES survapp_camera_master(id),
  PRIMARY KEY (nvr_node_id, camera_id)
);

CREATE TABLE backup_clip (
  id              BIGSERIAL PRIMARY KEY,
  nvr_node_id     INTEGER REFERENCES nvr_node(id),
  camera_id       INTEGER REFERENCES survapp_camera_master(id),
  object_key      VARCHAR(500),          -- in hub's MinIO backup_clips bucket
  reason          VARCHAR(50),           -- 'motion', 'manual', 'tamper'
  captured_at     TIMESTAMPTZ,
  uploaded_at     TIMESTAMPTZ DEFAULT NOW()
);
```

`survapp_camera_master` gains one column: `nvr_node_id INTEGER NULL REFERENCES nvr_node(id)` — NULL means "hub-native camera" (existing BSNL-VLAN behavior, unchanged), non-NULL means "lives behind this edge NVR."

### 2.5 Provisioning flow (zero-touch onboarding)

1. Admin creates a `customer_site` (already exists in the multi-tenant model) and clicks "Add NVR" in the (new) **NVR Fleet** page.
2. Hub calls Headscale's API to mint a **reusable, time-limited pre-auth key** scoped to that site's Headscale "user"/namespace.
3. Admin flashes/ships the box with a boot script that reads `SITE_CODE` + the pre-auth key from a USB drive or a QR code scanned during setup, and the box self-registers into the tailnet on first boot — no manual IP configuration, no port forwarding, no VPN config file to email around.
4. Once the overlay tunnel is up, `edge-agent` calls the hub once to fetch its camera list and register itself, flips `is_provisioned = true`.

---

## 3. Component 2 — The Overlay Network (Remote Access Backbone)

### 3.1 Choice of technology

**Recommendation: Headscale**, a self-hosted, open-source re-implementation of the Tailscale coordination server, using standard WireGuard as the actual data-plane protocol. This gives you:

- **You own the control plane.** No third-party operator ever holds your fleet's key material or network map — important for a surveillance product where "who can see which camera" is the whole security model.
- **Official Tailscale clients work unmodified** on Linux (edge boxes), iOS, and Android (mobile app), so you get NAT traversal, automatic reconnection, and mesh routing for free instead of hand-rolling WireGuard peer management.
- **Subnet routing** lets a site NVR advertise its LAN (e.g. `192.168.10.0/24`) into the tailnet if you ever need direct camera-level access for diagnostics, without exposing every camera as its own peer.
- Traffic between peers (edge ↔ hub, mobile ↔ hub, mobile ↔ edge) flows **directly, peer-to-peer, end-to-end WireGuard-encrypted**; the coordination server only brokers key exchange, not video bytes. When a direct path isn't reachable (both sides behind strict NAT), traffic falls back to a DERP relay — self-host your own DERP node inside your infrastructure to guarantee that fallback traffic never leaves infrastructure you control either.

**Alternative worth flagging:** [NetBird](https://netbird.io) — also self-hosted, also WireGuard-based, but built specifically around group-based zero-trust access policies and SSO (Keycloak/Azure AD) rather than a Tailscale-clone API. If the RBAC-over-network-access requirement grows more granular than "which site can this user reach," NetBird's native ACL engine may reduce custom glue code versus layering ACLs on top of Headscale yourself. Both are 2026-current, actively maintained, and roughly equal in raw data-plane performance since both ultimately use WireGuard.

> [!IMPORTANT]
> **Decision needed:** Headscale (Tailscale-protocol clone, lighter, you build the ACL/RBAC bridge yourself) vs. NetBird (built-in group ACLs, SSO-ready, slightly heavier control plane). Recommendation: **Headscale**, because the fine-grained "who sees which camera" authorization already lives in your existing `roles`/`permissions`/`camera_groups` system — you don't need the overlay network itself to know about business-level RBAC, you only need it to know "is this peer allowed to reach that peer at all," which Headscale's ACL policy file handles adequately.

### 3.2 Where it runs

- **Headscale server**: a new container on the Hub, fronted by the existing Kong/Nginx or a dedicated small Nginx+Certbot reverse proxy, since Headscale needs a stable HTTPS endpoint for peer registration. This is the **only new internet-facing surface** the whole plan introduces — and it's a metadata/coordination endpoint, not a video endpoint. Camera video never flows through it.
- **DERP relay**: self-hosted alongside Headscale so that even NAT-fallback relayed traffic stays inside infrastructure you operate.
- **Tailscale client** on every edge NVR box (as a container, per §2.2) and embedded/companion on every mobile app installation.

### 3.3 Addressing plan

| Peer type | Overlay CIDR | Example |
|---|---|---|
| Hub (fleet control plane) | fixed | `100.64.0.1` |
| Site NVRs | dynamic, assigned by Headscale per node | `100.64.0.10` – `100.64.0.250`+ |
| Mobile clients | dynamic, ephemeral per login session | `100.64.100.x` |

ACL policy (Headscale `acl.hcl`-equivalent) restricts mobile-tagged peers to only reach the specific site-tagged peers their organization/customer scope allows — tags are synced from the existing `organization_id`/`customer_id`/`camera_group` assignments whenever a role or camera-group changes, via a small `acl_sync` job on the hub.

---

## 4. Component 3 — Mobile Remote Viewing

### 4.1 UX/engineering options (pick one to start, upgrade later)

| Approach | UX | Engineering cost | Recommendation |
|---|---|---|---|
| **A. Companion app** — user installs the official Tailscale app alongside the Sarvanetra app; Sarvanetra deep-links a QR/pre-auth key into it once at setup | One extra app install, but zero VPN code to write or maintain | Low | **Start here** |
| **B. Embedded WireGuard SDK** — bundle `wireguard-go` via Android `VpnService` / iOS `NetworkExtension`, fully invisible to the user | Seamless, single-app experience | High (per-platform VPN entitlements, App Store review considerations for VPN extensions) | Phase 2, once volumes justify it |

Either way, the mobile app's own traffic model doesn't change: it still calls the same `/api/v1/streams/{cam_id}/hls-url` endpoint it always did — the only difference is that endpoint, and the HLS/RTSP traffic that follows it, are now reached at an **overlay IP** (`100.64.x.x`) instead of a public IP, because the app's network stack routes that CIDR block through the WireGuard tunnel and everything else (normal browsing) stays on the phone's regular internet connection (split tunneling — only the `100.64.0.0/10` range is routed into the tailnet).

### 4.2 Live-view request flow (remote mobile)

```
1. Mobile app: user logs in → Kong/FastAPI auth (unchanged, existing JWT flow)
   reached over the overlay at hub 100.64.0.1:8000 (not a public IP)
2. Mobile app: GET /api/v1/streams/{cam_id}/hls-url
3. FastAPI: looks up which nvr_node owns this camera (nvr_camera_map)
     - if NULL (hub-native camera): return the existing hub HLS URL, unchanged
     - if edge camera: return http://<nvr overlay ip>:8080/hls/<path>/index.m3u8?token=<jwt>
4. Mobile app's HLS.js/native player requests that URL — routed automatically
   over the WireGuard tunnel straight to the site NVR's local Nginx/MediaMTX
5. Video flows: Site NVR → (WireGuard, E2E encrypted) → Mobile device
   The hub is NOT in the video data path at all for this case — it only
   brokered the URL. This keeps hub egress bandwidth flat regardless of
   how many people are watching edge cameras.
```

For hub-native (BSNL VLAN) cameras, nothing changes — video still flows Hub → Kong → Nginx → viewer, exactly as today, just now the "viewer" can also be a mobile device reaching the hub over the overlay rather than only from inside VLAN 200.

### 4.3 Why this satisfies the "no video over the public internet" principle

The BSNL brief's core requirement was never literally "no packets ever traverse internet-owned fiber" — physically that's often unavoidable once you leave the BSNL backbone. The requirement, correctly generalized, is: **no CCTV stream is ever reachable by an unauthenticated party sniffing traffic, and no camera or NVR ever needs an inbound-open port on the public internet.** WireGuard/Headscale satisfies both: every packet is encrypted end-to-end regardless of which physical network carries it, and every device — mobile phone included — only ever dials *outward* to the coordination server; nothing needs a public IP or a forwarded port.

---

## 5. Phasing

### Phase 12 — Edge NVR (Site Recording)
1. Build `edge-agent` (motion loop + status loop + heartbeat + config sync)
2. Package `docker-compose.edge.yml` + install script for the target hardware (N100/RPi5)
3. Migration `0006_edge_fleet.py` on the hub (`nvr_node`, `nvr_camera_map`, `backup_clip`, `camera_master.nvr_node_id`)
4. Hub endpoints: `POST /fleet/heartbeat`, `GET /fleet/{site_code}/config`, `POST /fleet/{site_code}/backup-clip`
5. Frontend: **NVR Fleet** page (list sites, health, disk usage, last heartbeat, "Add NVR" provisioning wizard)
6. Local retention cleaner reusing Phase 10 logic against local filesystem

### Phase 13 — Overlay Network & Remote Access
1. Deploy Headscale + self-hosted DERP on the hub, behind its own TLS-terminating reverse proxy (the one new internet-facing endpoint)
2. `acl_sync` job: mirror `organization`/`customer`/`camera_group` scoping into Headscale ACL tags whenever RBAC changes
3. Edge boxes: add `wireguard-agent` container, wire provisioning flow (pre-auth key issuance from hub UI)
4. Mobile: ship companion-app-based VPN onboarding (Option A from §4.1); QR-code enrollment screen in the Sarvanetra app
5. Extend `GET /streams/{cam_id}/hls-url` to branch on `nvr_camera_map` and return an overlay-IP URL for edge cameras
6. Extend `stream_auth` webhook so a site NVR's local MediaMTX also validates the same JWT scheme as the hub (shared `KONG_JWT_SECRET`-equivalent distributed to edge boxes at provisioning time)

### Phase 14 — Commercial Hardening on Top of the Fleet
1. Per-site + per-organization bandwidth/storage metering (`nvr_node.disk_used_pct`, plus a `usage_daily` rollup table) to support tiered billing
2. Alerting: extend the existing `notifier.py` (Phase 9) to also fire on `last_heartbeat` staleness (site went dark) and `disk_used_pct` thresholds
3. Embedded WireGuard SDK in the mobile app (Option B from §4.1) once companion-app friction shows up in support tickets
4. Multi-region hub: if the customer base spreads beyond one city, add a second Headscale-joined hub and route sites to their nearest one — the tailnet model supports this without re-architecting anything above it

---

## 6. Open Questions / Decisions Needed

> [!IMPORTANT]
> **Q1 — Overlay technology.** Headscale (recommended, lighter, you own ACL-to-RBAC bridge) vs. NetBird (built-in group ACLs + SSO, slightly heavier). See §3.1.

> [!IMPORTANT]
> **Q2 — Edge hardware baseline.** What's the target unit cost/spec for a site NVR appliance? An Intel N100 mini-PC (4 cores, 8–16GB RAM, NVMe + one HDD bay) comfortably runs MediaMTX + edge-agent + local retention for up to ~8 cameras. A Raspberry Pi 5 works for 1–3 cameras at lower bitrate but will struggle with more than a couple of simultaneous local HLS viewers.

> [!IMPORTANT]
> **Q3 — Critical-clip backup policy.** What triggers a backup upload to the hub (motion only? tamper/offline event only? all of the above?), what's the clip length, and what's the retention on the hub's `backup_clips` bucket? This directly drives hub storage sizing across a large fleet.

> [!IMPORTANT]
> **Q4 — Mobile VPN UX.** Companion app now, embedded SDK later (recommended), or embedded SDK from day one if there's already mobile engineering capacity budgeted?

> [!WARNING]
> **Local database choice for edge boxes.** SQLite is simplest to ship (single file, zero admin) but has weaker concurrent-write characteristics than Postgres. Given an edge box's write load is just one `edge-agent` process, SQLite should be fine — but if you anticipate running additional local services that also need DB access (e.g. a local web UI for on-site technicians), lightweight Postgres is safer. Recommend: **start with SQLite, revisit if a local admin UI is added.**

> [!WARNING]
> **Headscale's own availability is now a dependency for new enrollments and remote access**, even though existing peer-to-peer WireGuard tunnels keep working if it's briefly down (coordination is only needed for registration/rekeying, not steady-state data flow — confirmed by Headscale's architecture). Recommend running Headscale + its Postgres/SQLite backing store with the same backup discipline as the main hub database.

> [!NOTE]
> **Backward compatibility.** Existing hub-native cameras on the BSNL VLAN are completely unaffected. `camera_master.nvr_node_id` defaults to `NULL`, and every existing endpoint (`/streams/*`, `/recordings/*`, `/motion/*`) keeps working exactly as built in Phases 0–11. This extension is purely additive.

---

## 7. Summary Table — New Files by Phase

| Phase | New/Modified Files |
|---|---|
| 12 | `edge-agent/` (new service: `motion_loop.py`, `status_loop.py`, `heartbeat.py`, `config_sync.py`, `backup_uploader.py`), `docker-compose.edge.yml`, `workers/minio_cleaner_local.py`, `app/alembic/versions/0006_edge_fleet.py`, `app/models/nvr.py`, `app/routers/fleet.py`, `app/schemas/fleet.py`, `frontend/src/pages/NvrFleet.tsx` |
| 13 | `docker-compose.yml` (+ `headscale`, `derp` services), `headscale/config.yaml`, `headscale/acl.hcl`, `app/services/acl_sync_service.py`, `app/routers/streams.py` (branch on `nvr_camera_map`), edge `mediamtx.yml` (`authHTTPAddress` pointed at hub over overlay), mobile app enrollment screen |
| 14 | `app/models/usage.py`, `app/routers/usage.py`, `workers/notifier.py` (staleness + disk-threshold alerts), mobile VPN SDK integration, second-hub join scripts |

---

*This plan extends, and does not replace, `sarvanetra_architecture.md`, `sarvanetra_status_plan.md`, and `implementation_plan_phase9+.md`. It should be read alongside the multi-tenant RBAC model (`implementation_plan_frontend.md`) since camera-level and site-level access control for remote/edge viewing reuses that model rather than duplicating it in the overlay network layer.*
