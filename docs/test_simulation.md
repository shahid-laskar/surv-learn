# Sarvanetra — Test Plan: Edge NVR, VPN Overlay & Simulated 100-Camera Fleet
## Validating Phases 0–15 Without Physical Cameras or Physical Edge Hardware

*Hub: `10.44.0.209` (existing). This plan assumes no physical IP cameras and no physical edge NVR boxes are available yet — everything below is designed to be tested with software simulation on infrastructure you already control, with a clear upgrade path to real hardware once the software path is proven.*

---

## 1. Testing Goals

1. Prove the **edge NVR** software (Phase 12) works correctly for one site before trusting it at scale.
2. Prove it **still works correctly at ~100-camera / multi-site scale** — this is a different risk profile (DB row volume, heartbeat throughput, Headscale node count, MinIO ingestion rate) than correctness on one site.
3. Prove the **VPN overlay** (Phase 14) and the **admin/customer remote-access model** (Phase 15) route traffic correctly and, just as importantly, **fail to route traffic where they shouldn't** (ACL isolation is a security boundary now, not just a convenience).
4. Do all of this **without physical cameras or physical edge boxes**, using simulation that's realistic enough that the results transfer to real hardware.

---

## 2. Test Topology (Separate VM for Simulated Edge Sites — Recommended Default)

Run simulated edge sites on genuinely separate VM(s)/server(s), on a different network/provider than the hub. This is better than same-host simulation, not just more convenient: each simulated site dials outbound to the hub's Headscale over the real public internet, exactly like a real customer premises — no inbound ports needed on either side — and you get real NAT traversal / DERP relay behavior validated as a side effect, instead of needing a separate fake-NAT test later.

### 2.1 Setup
- On the remote VM: confirm outbound internet works, it can reach/resolve the Headscale domain (a self-signed cert is fine for testing — trust it manually on that box), and it has enough CPU for however many simulated cameras you assign to it.
- Deploy the exact `docker-compose.edge.yml` stack from Phase 12 there, unmodified. Its `tailscale`/edge container enrolls into Headscale the same way a real box would.
- One VM can host several simulated "sites" as separate Compose project instances (`-p sim_site_01`, `-p sim_site_02`, …) if you don't want to provision one VM per site — each still registers as its own distinct Headscale node.

### 2.2 Scaling this out
Add more remote VMs (different providers/regions ideally) as you scale toward the full 18-site / 100-camera distribution in §4, so the peer/NAT diversity resembles real deployments rather than everything sitting behind one network's NAT.

### 2.3 What stays real throughout
The hub itself (`10.44.0.209`), Headscale, and all hub-side services are never simulated — only the "camera" and "edge site" sides are.

---

## 3. Simulating Cameras Without Hardware

### 3.1 Video source: stream-copy a looped sample clip, don't re-encode 100 times

Re-encoding a test pattern (`testsrc2`) 100 times simultaneously will pin every CPU core on the VM for no good reason. Instead:

1. Prepare a handful (3–5) of short, realistic sample clips (a few minutes each, one with visible motion in-frame for motion-detection testing, one mostly static for a "quiet camera" baseline) encoded once as H.264 in an MP4 container.
2. For each simulated camera, run `ffmpeg` with `-stream_loop -1 -re -i sample.mp4 -c copy -f rtsp rtsp://<mediamtx-host>:8554/<cam_path>` — **`-c copy` means no re-encoding**, ffmpeg just repackages already-encoded frames into RTSP. This is dramatically cheaper than encoding and is what makes 100 concurrent simulated streams practical on one VM.
3. Give each simulated camera its own RTSP path name matching your naming convention (e.g. `SIMCAM-SITE01-01` … `SIMCAM-SITE10-10`).

### 3.2 Resource sizing — pick a profile before you scale up

| Profile | Resolution/bitrate | Per-stream CPU (stream-copy) | 100-stream aggregate bandwidth | Use for |
|---|---|---|---|---|
| **Low** | 480p, ~300 kbps | Negligible (no re-encode) | ~30 Mbps | The full 100-camera scale test (§5.5) — proves the *pipeline*, not video quality |
| **Realistic** | 1080p, ~2 Mbps | Negligible (still stream-copy) | ~20 Mbps for a 10-camera subset | A smaller subset (10–20 cameras) to sanity-check actual playback/recording quality end-to-end |

Recommendation: run the **Low** profile for all 100 simulated cameras for the scale/load test, and separately keep a **Realistic**-profile subset of ~10–20 cameras running continuously through every test phase so you always have something that looks and plays like a real camera for manual/visual verification (HLS playback, timeline scrubbing, live view grid).

### 3.3 Simulating ONVIF motion events (ffmpeg alone won't do this)

`ffmpeg` only pushes video — it doesn't run an ONVIF event service, so a stream-copied fake camera won't generate real motion events the way a physical camera does. Two options, use both:

- **Direct event injection (recommended primary method):** build a small test harness script that calls the same code path the ONVIF producer / edge-agent's `motion_loop.py` would call on a real event — i.e. write directly into the relevant `motion_event` table (hub-native) or the edge SQLite `motion_event` table (edge-agent), on a timer or randomized schedule per simulated camera. This is the most reliable way to generate realistic motion-event *volume* for load testing without needing a real ONVIF stack.
- **A minimal fake-ONVIF responder (optional, for testing the actual ONVIF client code path):** if you want to exercise the real `onvif_motion_producer.py`/edge motion loop's SOAP client code (not just its downstream effects), stand up a lightweight mock ONVIF device service that answers `CreatePullPointSubscription`/`PullMessages` with synthetic motion payloads on a schedule. This is more faithful but more work to build — do it for a small subset of cameras (2–3) to confirm the ONVIF client code itself works, and rely on direct injection (above) for volume/load testing.

---

## 4. Distributing 100 Simulated Cameras

Recommended split, so you exercise every path the architecture actually has:

| Group | Count | Purpose |
|---|---|---|
| Hub-native (existing BSNL-VLAN-style) cameras | 10 | Confirm the original Phase 0–11 pipeline is completely unaffected by everything added since — regression baseline |
| Simulated edge sites, wired-style | 8 sites × 10 cameras = 80 | Bulk of the Phase 12 edge/fleet scale test |
| Simulated edge sites, single-camera "temporary site" pattern | 10 sites × 1 camera = 10 | Exercises the low-camera-count edge case and a higher site-count-to-camera-count ratio, which stresses `nvr_node`/heartbeat/ACL-sync row counts differently than a few big sites would |

Total: 100 cameras across 19 total sites (10 hub-native "not a site" + 18 simulated edge sites). This mix is deliberately lopsided toward *many sites* rather than *few sites with many cameras each*, because heartbeat volume, Headscale peer count, and ACL sync cost scale with **site/peer count**, not camera count — that's the dimension most likely to surprise you at real commercial scale, so it's worth over-representing in the test.

---

## 5. Phase-by-Phase Test Procedures

### 5.1 Regression: Phases 0–8 (run first, before adding any load)
- Confirm one hub-native simulated camera streams live (HLS), records, appears in the timeline API, and generates motion events exactly as the real camera did during original Phase 0–8 verification.
- This is your **baseline** — if something regresses later in the test, you'll know it's from the new load/features, not a pre-existing issue.

### 5.2 Phase 9 (Health Monitoring) Under Scale
- Bring up all 100 simulated cameras (§4). Confirm `/api/v1/health/cameras/` returns correct `is_online`/`offline_minutes` for all of them, and that the health dashboard renders without pagination/timeout issues at 100 rows.
- Kill 10 simulated cameras' ffmpeg processes (simulating them going offline) and confirm `camera_status_log` records the transition and the dashboard reflects it within the expected polling interval.

### 5.3 Phase 10 (Retention) Under Scale
- Let recordings accumulate across all 100 simulated cameras for at least one full cleaner cycle.
- Manually set a short `retention_days` (e.g. 1) on a handful of cameras and confirm `minio_cleaner.py` correctly identifies and removes only the expected objects, with correct pagination behavior once object counts are in the thousands (100 cameras × many short segments adds up fast — this is a good real test of the `list_objects_v2` pagination path, which is easy to get subtly wrong and hard to notice at low object counts).

### 5.4 Phase 11 (Hardening) Sanity
- Confirm CORS, non-root containers, and TLS are unaffected by the new load (these don't scale with camera count, but re-verify they weren't accidentally loosened while standing up test infrastructure — e.g. don't leave a `--internal` flag off a test Docker network by mistake and accidentally exposed it).

### 5.5 Phase 12 (Edge NVR) — Functional Test (single site, deep)
Before scaling out, prove one simulated edge site works correctly end-to-end:
- [ ] `edge-agent` heartbeat arrives at the hub every 30s and `nvr_node.last_heartbeat` updates
- [ ] Config sync pulls the correct camera list and `retention_days` for that site
- [ ] A simulated motion event (§3.3) triggers a critical-clip upload to the hub's `backup_clips` bucket, and `backup_clip` gets the correct row
- [ ] Local retention cleaner enforces retention against the simulated site's local recordings volume
- [ ] **WAN-drop resilience (important, do this explicitly):** pause the simulated site's `tailscale` container (`docker pause`) to sever its overlay connection, confirm local recording **continues uninterrupted** (check the local `/recordings` volume is still growing), then unpause and confirm heartbeat resumes and the hub's "last heartbeat" staleness clears.
- [ ] Decommission flow: remove the site via the admin UI, confirm its `nvr_node` row and Headscale peer are both cleaned up

### 5.6 Phase 12 — Scale Test (all 18 simulated sites / 100 cameras)
- Bring up all simulated sites simultaneously. Watch hub-side resource use (Postgres connections, CPU) while 18 sites all heartbeat concurrently.
- Confirm the NVR Fleet page renders and stays responsive with 18+ nodes and 100 mapped cameras.
- **Reconnect storm test:** pause and then simultaneously unpause *all* simulated sites' `tailscale` containers at once (simulating "hub came back after a regional outage and every site reconnects at the same moment") — confirm the hub doesn't fall over from a burst of simultaneous heartbeats/config-sync requests, and confirm Headscale handles the reconnection burst cleanly.
- Record: heartbeat p50/p95 latency, Postgres connection count, and hub CPU/memory under this load — these are your baseline capacity numbers for deciding how many real sites the current hub sizing can support before it needs scaling.

### 5.7 Phase 14 (VPN Overlay) — Correctness & Isolation
- Confirm every simulated site registers as a distinct Headscale node (`headscale nodes list`) with a distinct overlay IP.
- **Stream branching test:** for a hub-native camera, confirm the HLS URL returned is unchanged (points at the hub); for a simulated-edge camera, confirm the returned URL points at that site's overlay IP and that requesting it actually plays video **sourced from that specific simulated site's MediaMTX**, not the hub's — the clearest way to check this is to make each simulated site's sample clip visually distinguishable (e.g. burn a text overlay "SITE 07" into that site's sample video) so you can eyeball which backend actually served the stream.
- **DERP fallback test:** from a simulated-site VM, block direct UDP paths (e.g. a restrictive `iptables` rule simulating symmetric NAT) and confirm the connection still succeeds via the self-hosted DERP relay rather than failing outright.

### 5.8 Phase 15 (VPN Remote Access) — Persona & ACL Tests
- **Admin peer:** issue an admin pre-auth key, join a genuinely separate test device (a laptop, or another VM) to the tailnet with the official Tailscale client, confirm it can reach Kong Admin, Konga, MinIO console, and at least one simulated site's SSH/MediaMTX API port.
- **Customer peer — the important negative test:** issue a `group:customer:<id>` peer scoped to one specific simulated customer/site. From that joined device, confirm it **can** reach that customer's dashboard/camera, and — just as important — **cannot** reach: (a) any admin-only port, (b) any *other* customer's simulated site, (c) any hub-native camera not assigned to it. Do this test explicitly and don't skip it; this is the security boundary the whole plan depends on.
- **Revocation test:** revoke a customer peer from the admin "VPN Access" UI and confirm the joined test device loses connectivity on its next handshake attempt (no need to touch the device itself).
- **Hardening validation (§5 of the Phase 15 plan):** after binding Kong Admin/Konga/MinIO console/Kafka UI to tailnet-only, confirm they are genuinely unreachable from a device that is *not* on the tailnet (test from a plain browser on a network with no Tailscale client running) and still reachable from one that is.

---

## 6. Chaos / Resilience Scenarios to Run Deliberately

| Scenario | How to trigger (simulated) | Expected result |
|---|---|---|
| Single site WAN outage | `docker pause` that site's `tailscale` container | Local recording continues; hub shows stale-heartbeat alert after threshold; resumes cleanly on `unpause` |
| Mass reconnect after hub outage | Restart the hub's `headscale`/`app` containers while all sites are up, then observe reconnection | All sites re-establish within a reasonable window; no duplicate `nvr_node` rows created |
| Hub Postgres restart mid-load | Restart `postgres` container during the 100-camera scale test | Workers/edge-agents retry and recover without manual intervention (per the existing reconnect-on-`OperationalError` pattern already in the worker code) |
| Peer revocation during active stream | Revoke a customer peer while their device is actively watching a live stream | Existing stream may continue briefly (depending on token TTL) but no *new* connection/handshake succeeds |
| Disk pressure at a simulated site | Fill the simulated site's `/recordings` volume artificially (e.g. `fallocate`) close to full | Local retention cleaner reacts (deletes oldest first) before disk fills completely; heartbeat's `disk_used_pct` reflects the pressure and (if wired) triggers an alert |

---

## 7. Metrics to Capture From This Round of Testing

Treat this test pass as your first real capacity-planning data point, not just a pass/fail exercise. Record, at minimum:

- Heartbeat request rate and latency at 18 concurrent sites
- Postgres connection count and query latency for `fleet.py` endpoints under load
- MinIO backup-clip ingestion rate (clips/minute) the hub can sustain
- Headscale node/peer count and ACL-policy-reload time with ~120 total peers (100+ cameras' worth of sites + admin/customer test peers)
- Hub CPU/RAM headroom remaining after all of the above is running simultaneously

These numbers directly answer "how many real sites can this VM's current sizing support before we need to scale the hub," which is a question you'll need answered before real commercial rollout regardless of this specific test.

---

## 8. What This Plan Deliberately Does Not Cover

- **Phase 13 (4G/SIM support)** — not confirmed built per your last update; simulating cellular signal degradation is out of scope here and should get its own focused test pass once that phase is implemented.
- **Mobile app** — deferred per your instruction; nothing here tests the embedded WireGuard SDK or camera-scan flow, since that work hasn't started.
- **Real customer data / real cameras** — this entire plan is about proving the software is correct and knowing its capacity limits *before* the first real site is onboarded, not a substitute for a pilot with one real, physical edge box once you're confident in the simulated results.

---

## 9. Suggested Execution Order

1. §5.1 regression baseline (hub-native, no new load)
2. §5.5 single simulated edge site, functional depth
3. §5.7 stream-branching correctness (still just 1–2 sites)
4. Scale up to full §4 distribution (100 cameras / 18 sites) → §5.2, §5.3, §5.6
5. §5.8 persona/ACL tests (can run in parallel with step 4 once sites are up)
6. §6 chaos scenarios, deliberately, one at a time
7. DERP fallback test (§5.7) via `iptables`-restricted UDP on a simulated-site VM — do this last, right before considering a real pilot site

---

## 10. Open Decisions

> [!IMPORTANT]
> **Test Headscale TLS.** A production Headscale needs a real, resolvable domain + valid certificate (per Phase 14). For this test round, a self-signed certificate (trusted manually on test devices) or a local DNS entry is sufficient — don't block testing on acquiring a real domain yet, but don't test the real-customer-pilot step without one either.

> [!IMPORTANT]
> **Simulated-site VM count/provider.** Any small VM(s) at a different provider/network from the hub work — recommend at least one to start; add more as you scale toward the full 18-site distribution (§2.2).

> [!NOTE]
> **Sample clip content.** Burning a visible site-identifier into each simulated camera's looped clip (§5.7) is a small effort that pays for itself repeatedly during manual verification — you'll use it constantly to eyeball "is this actually coming from where I think it's coming from" throughout the rest of this test plan.