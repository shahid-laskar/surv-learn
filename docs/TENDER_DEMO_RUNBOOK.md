# SARVANETRA — Master Tender Demonstration Runbook
**Document ID:** `RUNBOOK-DEMO-001`  
**Classification:** Client Demonstration / Technical Defense  
**Revision:** 1.0  
**Target Audience:** Solution Architects, Pre-Sales Engineers, Evaluation Committees  

---

## 1. Demonstration Overview

This runbook guides an engineer through a live, end-to-end technical demonstration of SARVANETRA for evaluation committees (Kerala Police / KELTRON). Every step executes against genuine API endpoints, microservices, and database tables—no mock UI screenshots or fabricated metrics.

---

## 2. Pre-Requisites & Environment Launch

### 2.1 Start Central Hub Infrastructure
In terminal 1:
```bash
cd /opt/surv-learn/surv
docker compose up -d
```
Verify all core services are running and healthy:
```bash
docker compose ps
# Expected: postgres, surv_kafka, minio, mediamtx, kong, app, surv_status_consumer
```

### 2.2 Verify Database Migrations
```bash
docker compose exec app alembic upgrade head
```

### 2.3 Start Frontend Web Application
In terminal 2:
```bash
cd /opt/surv-learn/surv/frontend
npm run dev
# Accessible at: http://localhost:3000
```

---

## 3. Step-by-Step Live Demonstration Script

### Step 1: Authentication & RBAC Hierarchy
1. Open `http://localhost:3000/login` in the browser.
2. Sign in with standard Super Admin credentials:
   - **Username:** `admin`
   - **Password:** `admin1234`
3. Point out:
   - High-entropy HS256 JWT issued with scoped roles (`SUPER_ADMIN`, `POLICE_OFFICER`).
   - Tenant context bound to state, district, or customer site.

### Step 2: Multi-Site Dashboard & Single Pane of Glass
1. Navigate to `/dashboard`.
2. Demonstrate real-time system metrics:
   - Total Provisioned Cameras vs Online Cameras.
   - Active Parking Grounds (Nilakkal Ground 1 to 12).
   - Hotlist / Watchlist Alarms count.
   - Real-time event ingestion throughput.

### Step 3: Camera Status & Live Video Feeds
1. Navigate to `/cameras`.
2. Point out multi-protocol camera support (RTSP, RTSPS, RTMP).
3. Click on camera `CAMKRTVM0001` to open the live player:
   - Token-gated WebRTC feed (<500ms latency) and HLS fallback.
   - PTZ controls and stream health indicator.

### Step 4: Continuous Recording, Timeline Playback & Snapshots
1. Navigate to `/recordings`.
2. Inspect the multi-channel timeline bar:
   - 60-second video segments stored in MinIO S3 bucket `recordings`.
   - Click any timestamp segment: verified MP4 playback via presigned S3 URL.
3. Click "Capture Snapshot":
   - Presigned URL loads the high-resolution JPEG (`latest.jpg`) captured by `snapshot_worker.py`.

### Step 5: Motion Ingestion & Edge Synchronization
1. From terminal 3, simulate an edge camera motion trigger:
```bash
cd /opt/surv-learn/surv
PYTHONPATH=. .venv/bin/python3 workers/status_monitor.py --once
```
2. Navigate to `/motion` in the browser:
   - Observe immediate event update with bounding coordinates and timestamp.

### Step 6: ANPR Event Ingestion & High-Speed OCR Simulation
1. From terminal 3, fire synthetic license plate events matching standard Indian RTO formats:
```bash
cd /opt/surv-learn/surv
PYTHONPATH=. .venv/bin/python3 workers/synthetic_anpr.py --burst 5
```
2. Navigate to `/anpr` in the UI:
   - View newly ingested plates (e.g. `KL01AB1234`), confidence score, vehicle type, and captured timestamp.
3. Demonstrate **Fuzzy Search**:
   - Type `KLO1AB1234` (with OCR substitution letter 'O' instead of digit '0').
   - The PostgreSQL `pg_trgm` GIN index resolves the exact vehicle record in <5ms.

### Step 7: Hotlist / Watchlist Instant Alerting
1. Trigger a wanted/stolen vehicle detection:
```bash
PYTHONPATH=. .venv/bin/python3 workers/synthetic_anpr.py --watchlist
```
2. Observe UI notification drawer:
   - Critical alarm pop-up: **"WANTED VEHICLE DETECTED: KL07BH9999"**.
   - Associated case number and reporting authority details displayed.

### Step 8: Nilakkal Smart Parking Allocation Engine
1. Execute the concurrent parking allocation simulation:
```bash
PYTHONPATH=surv surv/.venv/bin/python3 surv/scripts/simulate_parking_traffic.py --standalone
```
2. Navigate to `/parking` in the UI:
   - Inspect live zone occupancy bars: Invariant strictly verified ($0 \le \text{occupancy} \le \text{capacity}$).
   - Inspect generated entry slip with UUID barcode and vehicle class.

### Step 9: GIS Common Operating Picture & Bilingual UI
1. Navigate to `/gis`:
   - Interactive Leaflet map displaying Sabarimala / Nilakkal geographic area.
   - Status-colored camera markers (Green: Online, Red: Offline, Amber: Motion).
   - Parking zone polygons with real-time vacancy badges.
2. Click the language toggle button in the top navigation bar:
   - Toggle from **English** to **മലയാളം (Malayalam)**.
   - Demonstrate complete UI translation across menus, headers, and status labels without reload.

### Step 10: Incident Management & Cryptographic Evidence Sealing
1. Navigate to `/incidents`:
   - Promote the Hotlist Watchlist detection into a formal case: `INC-2026-0001`.
   - Assign to Duty Officer and set priority to `HIGH`.
2. Navigate to `/evidence`:
   - Export official Evidence Package for court submission.
   - Point out computed SHA-256 checksum and digital manifest.
   - Demonstrate integrity verification: altering any bit in the manifest immediately flags **"EVIDENCE TAMPER DETECTED"**.

### Step 11: Immutable Audit Trail
1. Navigate to `/audit`:
   - Review append-only chronological log of all administrator operations: login, stream access, plate modifications, and evidence exports.

---

## 4. Teardown
```bash
cd /opt/surv-learn/surv
docker compose down
```
