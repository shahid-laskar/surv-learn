# SARVANETRA — Comprehensive Tender Implementation Roadmap
**Document Version:** 1.0.0  
**Date:** September 22, 2026  
**Strategic Mission:** Elevating SARVANETRA to Full Government & Smart City Tender Readiness  
**Target Benchmarks:** Kerala Police Nilakkal PMS (Tender A) & KELTRON AI Platform EOI (Tender B)

---

## 1. Requirement Prioritization Matrix

Gaps and enhancements across SARVANETRA are categorized by operational criticality and engineering effort:

* **P0: Mandatory to Qualify & Unblock Deployment** (Immediate fixes and fundamental tender prerequisites)
* **P1: Minimum Functional Compliance** (Required to meet core functional tender specifications)
* **P2: Production Operational Excellence** (Required for reliable field operations, SLAs, and audits)
* **P3: Advanced Future Capabilities** (Long-term value-adds, AI analytics, and multi-agency scaling)

| Task ID | Component / Feature | Priority | Effort | Description & Justification |
|---|---|---|---|---|
| **TR-P0-01** | Kong Edge Gateway Bypass | **P0** | **LOW** | Allow `X-Site-Token` edge agent traffic through Kong on `:8000` to unblock edge fleet sync. |
| **TR-P0-02** | MediaMTX `kcat` Installation | **P0** | **LOW** | Install `kcat` in `Dockerfile.mediamtx` so `camera_ready.sh` publishes lifecycle events to Kafka. |
| **TR-P0-03** | Snapshot Worker `latest.jpg` Key Fix | **P0** | **LOW** | Store `{cam_id}/latest.jpg` so API thumbnail presigned URLs resolve with HTTP 200. |
| **TR-P0-04** | Consortium SI & OEM Alignment | **P0** | **HIGH** | Secure lead bidder partnership with Kerala office, ₹10 Cr turnover, and OEM MAF authorizations. |
| **TR-P0-05** | Live Demonstration Testbench | **P0** | **MEDIUM** | Prepare synthetic demonstration environment using `edge-sim` for KELTRON 30-mark evaluation. |
| **TR-P1-01** | Parking Zone & Slot Data Model | **P1** | **LOW** | Alembic migration for `parking_zone`, `parking_lane`, and `parking_session` tables. |
| **TR-P1-02** | Real-Time Parking Occupancy Engine | **P1** | **MEDIUM** | Ingest vehicle counts to compute real-time zone occupancy and dynamic allocation advice. |
| **TR-P1-03** | Handheld Android POS API Bridge | **P1** | **MEDIUM** | Expose REST endpoints for POS login, dynamic zone allocation, and entry slip generation. |
| **TR-P1-04** | ANPR Data Model & Ingestion API | **P1** | **LOW** | Alembic migration for `anpr_transaction` and endpoint `POST /api/v1/anpr/events`. |
| **TR-P1-05** | Watchlist Matching & Instant Alerting | **P1** | **MEDIUM** | Hotlist table ("Wanted", "Stolen") with Kafka stream matching and <2s control room alerts. |
| **TR-P1-06** | Edge LPU ANPR Engine Integration | **P1** | **HIGH** | Deploy containerized OCR pipeline (e.g. DeepStream / Fast-ANPR) on edge industrial LPU. |
| **TR-P1-07** | Fuzzy Plate Search (`pg_trgm`) | **P1** | **LOW** | Implement PostgreSQL trigram index for 1–2 character edit-distance fuzzy searching. |
| **TR-P1-08** | GIS Map Component in Web SPA | **P1** | **MEDIUM** | Integrate Leaflet / MapLibre to display camera markers, status colors, and parking zones. |
| **TR-P1-09** | ICCC Common Operating Picture (COP) | **P1** | **HIGH** | Build composite command dashboard matching Tender B specifications and mockup. |
| **TR-P1-10** | Bi-Lingual GUI (Malayalam & English) | **P1** | **LOW** | Implement `react-i18next` localization for all web dashboard labels and forms. |
| **TR-P2-01** | Evidentiary Clip Export with SHA-256 | **P2** | **MEDIUM** | Generate downloadable MP4 packages with cryptographic checksums and timestamp overlays. |
| **TR-P2-02** | Traffic Analytics & Pilgrim Estimation | **P2** | **MEDIUM** | Daily/monthly traffic reporting APIs and multiplier-based pilgrim estimation. |
| **TR-P2-03** | Line Crossing & People Counting AI | **P2** | **HIGH** | Python/C++ CV worker ingesting RTSP feeds and emitting Kafka count events. |
| **TR-P2-04** | Crowd Density Estimation (Heatmaps) | **P2** | **HIGH** | Density regression inference worker and frontend canvas heatmap rendering. |
| **TR-P2-05** | Incident Lifecycle Ticketing Module | **P2** | **MEDIUM** | Schema, state machine, and UI for incident dispatch, escalation, and resolution. |
| **TR-P2-06** | Automated CERT-In Vulnerability Remediation | **P2** | **HIGH** | Run SAST/DAST, remediate OWASP Top 10 vulnerabilities, obtain audit compliance certificate. |
| **TR-P2-07** | High Availability Database Cluster | **P2** | **HIGH** | Deploy PostgreSQL Patroni cluster with synchronous replication and automated failover. |
| **TR-P3-01** | Facial Recognition / Missing Person | **P3** | **HIGH** | InsightFace feature extraction pipeline with `pgvector` / Milvus vector index. |
| **TR-P3-02** | Predictive Crowd Intelligence (Forecasting) | **P3** | **HIGH** | Time-series forecasting models (Prophet/LSTM) for queue and congestion prediction. |
| **TR-P3-03** | Public Address (SIP) & VMS Integration | **P3** | **MEDIUM** | Audio broadcast bridge to IP horn speakers and NTCIP driver for highway LED signs. |
| **TR-P3-04** | Drone Telemetry & Mission Ingestion | **P3** | **MEDIUM** | MAVLink flight telemetry listener and GIS path visualization. |
| **TR-P3-05** | Mobile Responder Application | **P3** | **VERY HIGH**| Cross-platform React Native app with push notifications and incident workflows. |

---

## 2. Minimum Viable Tender Platform (MVTP)

To win and execute both tenders without unbounded engineering overhead, SARVANETRA must be packaged into clearly scoped modules:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   MINIMUM VIABLE TENDER PLATFORM (MVTP)                │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  [ CORE MODULES - Built Directly in SARVANETRA ]                       │
│  ├── 1. VMS Core (RTSP Ingest, HLS Player, fMP4 Recording, MinIO S3)   │
│  ├── 2. Hierarchy & RBAC (Multi-Site, Org Trees, JWT Sessions)         │
│  ├── 3. Parking Management System (12 Zones, Occupancy Engine, POS API)│
│  ├── 4. ANPR Management Plane (Transactions, Watchlists, Fuzzy Search) │
│  ├── 5. ICCC Dashboard & GIS Map (COP Single Pane, Alerts, Incident UI)│
│  └── 6. Audit & Evidence Engine (Tamper-evident logs, Signed Exports)  │
│                                                                        │
│  [ INTEGRATED EDGE RUNTIME - Containerized on Edge Hardware ]          │
│  ├── 7. Edge NVR Appliance (7-loop agent, local SQLite retention)      │
│  └── 8. Edge AI Worker (TensorRT/ONNX OCR pipeline on LPU)             │
│                                                                        │
│  [ THIRD-PARTY PARTNER INTEGRATIONS - Modular Plugins ]                │
│  ├── 9. Android POS Terminal APK (Thermal printer slip printing)       │
│  ├── 10. Commercial ANPR OCR Engine (ARAI 230 km/h certified)          │
│  ├── 11. IP Public Address System (SIP audio broadcast bridge)         │
│  └── 12. External AI Vision Services (Crowd density, Face search)      │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Recommended Target Architecture

### 3.1 Logical Architecture Diagram

```
                                      FIELD & EDGE TIER
 ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
 │   Fixed / PTZ Cameras   │  │   Dedicated ANPR Cams   │  │  Handheld Android POS   │
 │ (5MP Bullet, 40X PTZ)   │  │   (+ 850nm IR Illum.)   │  │  (Thermal Slip Printer) │
 └────────────┬────────────┘  └────────────┬────────────┘  └────────────┬────────────┘
              │ RTSP                       │ RTSP                       │ HTTPS / JSON
              ▼                            ▼                            ▼
 ┌─────────────────────────────────────────────────────────┐            │
 │           EDGE APPLIANCE / LOCAL PROCESSING UNIT (LPU)  │            │
 │  - MediaMTX: Local RTSP proxy & 7-day circular storage  │            │
 │  - Edge AI Inference: License Plate Detection & OCR     │            │
 │  - Edge Agent: SQLite buffer, Health, Sync to Hub       │            │
 └────────────────────────────┬────────────────────────────┘            │
                              │ Encrypted VPN / WAN                     │
                              ▼                                         │
 ┌──────────────────────────────────────────────────────────────────────┴─────────────┐
 │                         KONG ENTERPRISE API GATEWAY (:8000 / :8443)                │
 │  - Perimeter JWT validation (Web users) | X-Site-Token bypass (Edge appliances)    │
 │  - Rate Limiting, CORS, SSL termination, Load Balancing across App Nodes           │
 └─────────┬────────────────────────────────────────────────────────────┬─────────────┘
           │                                                            │
           ▼ Internal Network                                           ▼
 ┌──────────────────────────────────────────────────────┐     ┌───────────────────────┐
 │         FASTAPI CORE APPLICATION CLUSTER (x2)        │     │    NGINX MEDIA PROXY  │
 │  - Camera & Stream Catalog    - Parking Occupancy    │     │  - HLS Stream Cache   │
 │  - ANPR Search & Watchlists   - ICCC Incidents       │     │  - WebRTC Relay       │
 │  - Dynamic Stream Auth Hook   - Traffic Reporting    │     └───────────┬───────────┘
 └─────────┬──────────────────┬─────────────────────────┘                 │
           │                  │                                           │
           ▼                  ▼                                           ▼
 ┌───────────────────┐  ┌───────────────────────────────┐     ┌───────────────────────┐
 │  PATRONI HA CLUST │  │ APACHE KAFKA 3-NODE KRaft BUS │     │  MediaMTX CLUSTER     │
 │  - PostgreSQL 16  │  │ - camera.motion               │     │  - RTSP/RTMP Ingest   │
 │  - Sync Replicas  │  │ - camera.status               │     │  - 60s fMP4 Slicing   │
 │  - Auto-Failover  │  │ - recording.segments          │     └───────────┬───────────┘
 │  - pg_trgm Search │  │ - vehicle.anpr.detected       │                 │
 └───────────────────┘  │ - crowd.density.alert         │                 ▼
                        └──────────────┬────────────────┘     ┌───────────────────────┐
                                       │                      │  MinIO DISTRIBUTED S3 │
                                       ▼                      │  - 'recordings' (90d) │
                        ┌───────────────────────────────┐     │  - 'snapshots'        │
                        │    ASYNC WORKER SERVICES      │     │  - 'backup_clips'     │
                        │  - Segment DB Consumer        │     └───────────────────────┘
                        │  - Watchlist Alert Matcher    │
                        │  - MinIO Retention Cleaner    │
                        │  - Evidence Packaging Service │
                        └───────────────────────────────┘
                                       │
                                       ▼
 ┌────────────────────────────────────────────────────────────────────────────────────┐
 │               INTEGRATED COMMAND & CONTROL CENTRE (ICCC) PRESENTATION              │
 │  - React 18 / Vite / Tailwind SPA with Bi-Lingual Support (Malayalam / English)    │
 │  - Common Operating Picture (COP) with Interactive GIS Map (Cameras, UAVs, Zones) │
 │  - Real-Time Parking Occupancy Grid & Entry/Exit Flow Gauges                       │
 │  - Video Wall Multi-Grid (Hls.js Low-Latency) & Incident Dispatch Console          │
 └────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Multi-Phase Implementation Roadmap

### Phase A: Stabilize Existing SARVANETRA Baseline (Week 1)
* **Goal:** Eliminate all existing runtime blockers and harden core ingestion.
* **Tasks:**
  1. Fix Kong edge route bypass in `surv/kong/setup-kong-jwt.sh` (P0-01).
  2. Install `kcat` in `surv/Dockerfile.mediamtx` (P0-02).
  3. Align snapshot worker key to `{cam_id}/latest.jpg` (P0-03).
  4. Replace hardcoded `10.44.0.209` across configuration files.
  5. Refactor snapshot worker to query cameras dynamically from PostgreSQL.
* **Verification:** Pytest suite passes; snapshot thumbnails display in UI; edge agent successfully heartbeats through Kong Gateway on port 8000.

### Phase B: Tender Compliance Foundation & Schema Extensions (Weeks 2–3)
* **Goal:** Extend database schema and API contracts for parking and vehicle tracking.
* **Tasks:**
  1. Create Alembic migration `0011_parking_and_anpr.py` adding `parking_zone`, `parking_lane`, `parking_session`, `anpr_transaction`, and `vehicle_watchlist`.
  2. Implement `surv/app/routers/parking.py` (CRUD for 12 zones, occupancy status).
  3. Implement `surv/app/routers/anpr.py` (ANPR event ingest, watchlist CRUD, fuzzy search).
  4. Enable PostgreSQL `pg_trgm` extension for 1- and 2-character edit distance plate searching.
* **Verification:** API unit tests verify zone creation, vehicle transaction ingestion, and trigram fuzzy searching.

### Phase C: Parking Management Engine & POS Terminal Integration (Weeks 4–5)
* **Goal:** Deliver end-to-end automated parking allocation and slip printing flow for Nilakkal.
* **Tasks:**
  1. Build `ParkingAllocationService` with dynamic assignment logic based on live zone vacancy.
  2. Build REST endpoint `POST /api/v1/parking/entry-slip` generating structured JSON payload for Android POS.
  3. Develop lightweight Android POS terminal bridge application (Java/Kotlin) communicating via HTTPS and driving the 58mm thermal printer.
  4. Build real-time Parking Dashboard in React SPA with live zone occupancy bar charts and vacancy meters.
* **Verification:** Simulated vehicle entry triggers POS slip generation, increments zone occupancy, and updates web dashboard within 1 second.

### Phase D: Edge LPU ANPR Engine & Watchlist Matching (Weeks 6–7)
* **Goal:** Connect edge AI license plate detection to SARVANETRA central control plane.
* **Tasks:**
  1. Package containerized ANPR inference worker (YOLO plate detector + CRNN OCR / DeepStream) running on edge LPU hardware.
  2. Configure ANPR worker to push JSON event payloads (`{plate, vehicle_type, color, speed, timestamp}`) to Hub API.
  3. Implement Kafka stream consumer matching plates against `vehicle_watchlist` table.
  4. Add real-time UI notification toaster and audio chime for hotlisted vehicle detections (<2s latency).
* **Verification:** Simulated vehicle video streams trigger plate detection, database logging, and instant UI alert on watchlist match.

### Phase E: ICCC Common Operating Picture & GIS Integration (Weeks 8–9)
* **Goal:** Deliver the executive command and control interface required by Tender B (Page 13).
* **Tasks:**
  1. Integrate Leaflet / MapLibre GIS mapping component into `surv/frontend/src/pages/ICCCPage.tsx`.
  2. Plot camera markers, parking zones, and active incident pins with real-time status color coding.
  3. Build composite COP layout uniting GIS map, 4-grid video wall, live occupancy gauges, and alert stream into a single screen.
  4. Implement `react-i18next` localization for full English and Malayalam UI toggling.
* **Verification:** Operators can navigate GIS map, click camera pin to open live HLS feed in overlay modal, and switch language seamlessly.

### Phase F: Incident Lifecycle Management & Evidence Export (Week 10)
* **Goal:** Provide end-to-end incident management and tamper-proof evidence handling.
* **Tasks:**
  1. Create `incident` and `incident_timeline` models and router (`/api/v1/incidents`).
  2. Build incident dispatch and tracking drawer in ICCC dashboard.
  3. Implement evidence export packaging service generating ZIP bundle containing video MP4, JSON metadata, SHA-256 integrity manifest, and cryptographic watermark.
* **Verification:** Incident creation tracks status transitions (New → Assigned → Resolved), and exported MP4 matches SHA-256 checksum manifest.

### Phase G: Advanced AI Analytics & Drone Ingestion (Weeks 11–12)
* **Goal:** Implement people counting, crowd density heatmaps, and aerial video ingest.
* **Tasks:**
  1. Deploy people counting inference container emitting directional line-crossing events to Kafka.
  2. Build crowd density heatmap renderer in React frontend using canvas coordinate mapping.
  3. Configure MediaMTX RTMP publisher endpoints for drone video ingest (`rtmp://hub:1935/live/drone_01`).
  4. Integrate MAVLink flight telemetry parser plotting drone icon and heading live on GIS map.
* **Verification:** Drone RTMP stream plays smoothly in HLS player; crowd heatmap renders dynamic density gradients.

### Phase H: Security Hardening & CERT-In Audit Readiness (Weeks 13–14)
* **Goal:** Meet DPDP Act 2023 requirements and pass formal third-party CERT-In assessment.
* **Tasks:**
  1. Run automated SAST/DAST scans (Bandit, Trivy, OWASP ZAP) across backend and frontend containers.
  2. Enforce strict TLS 1.3 encryption across all public endpoints and MinIO S3 API.
  3. Implement automated PII retention purging and data redaction policies per DPDP Act guidelines.
  4. Engage CERT-In empaneled security auditing firm for formal penetration testing and certification.
* **Verification:** Zero Critical or High severity vulnerabilities in VAPT report; formal CERT-In compliance letter issued.

### Phase I: High Availability Clustering & Disaster Recovery (Weeks 15–16)
* **Goal:** Satisfy Tender B High Availability (HA) specifications with zero single point of failure.
* **Tasks:**
  1. Deploy 3-node PostgreSQL Patroni cluster with etcd consensus and HAProxy load balancing.
  2. Scale Apache Kafka to 3-node KRaft broker cluster.
  3. Deploy MinIO distributed cluster across 4 independent storage drives.
  4. Configure Kong Gateway in Active-Active mode behind an external network load balancer.
* **Verification:** Simulated sudden kill of primary database container results in automated failover within 10 seconds without video stream interruption.

### Phase J: Site Commissioning, Training & O&M Handover (Weeks 17+)
* **Goal:** Physical site execution at Nilakkal/Pampa and project handover.
* **Tasks:**
  1. Supervise OFC ring network splicing, switch configuration, and camera pole mounting.
  2. Calibrate ANPR camera angles and 850nm IR illuminator focus for day/night glare elimination.
  3. Train Kerala Police personnel at Nilakkal Control Room on dashboard and incident workflows.
  4. Deploy resident Site Engineer and maintain 24x7 spares depot for 36-month SLA.
* **Verification:** Successful end-to-end dry run prior to Sabarimala pilgrimage season; sign-off on Final Handover Certificate.

---

## 5. What Should I Build First? (Immediate 5 Concrete Milestones)

If you are resuming development on SARVANETRA today to make the platform progressively tender-ready, follow this exact milestone sequence:

```
MILESTONE 1: Clear Ingestion & Perimeter Blockers (Hours 1–4)
  ├── 1. Edit 'surv/kong/setup-kong-jwt.sh' to bypass '/api/v1/fleet' & '/api/v1/motion/edge'
  ├── 2. Add 'kcat' to 'surv/Dockerfile.mediamtx'
  └── 3. Update 'surv/workers/snapshot_worker.py' to save '{cam_id}/latest.jpg'

MILESTONE 2: Parking & ANPR Relational Schema (Days 1–2)
  ├── 1. Generate Alembic migration for 'parking_zone', 'parking_lane', 'anpr_transaction'
  ├── 2. Implement 'surv/app/routers/parking.py' (Zone CRUD & live occupancy API)
  └── 3. Implement 'surv/app/routers/anpr.py' (OCR transaction ingest & pg_trgm fuzzy search)

MILESTONE 3: Live Parking Management Dashboard (Days 3–4)
  ├── 1. Build 'ParkingDashboardPage.tsx' in React frontend
  ├── 2. Render live occupancy bar gauges for Nilakkal Zones 1 to 12
  └── 3. Add dynamic allocation advice panel ("Direct next vehicles to Zone 4")

MILESTONE 4: Watchlist Matching & Alert Notification (Days 5–6)
  ├── 1. Add 'vehicle_watchlist' database table and API
  ├── 2. Build Kafka consumer matching incoming ANPR transactions against hotlist
  └── 3. Add real-time UI alert popup and audible notification chime in frontend

MILESTONE 5: Interactive GIS Common Operating Picture (Days 7–10)
  ├── 1. Integrate Leaflet / MapLibre into 'surv/frontend/src/pages/ICCCPage.tsx'
  ├── 2. Overlay camera pins (green=up, red=down) and parking zone polygons
  └── 3. Wire pin click to open live HLS video stream modal
```
Following these five milestones immediately establishes a working, demonstrable core that directly addresses the functional requirements of both government tenders.
