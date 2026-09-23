# SARVANETRA — Comprehensive Tender Readiness & Gap Analysis
**Document Version:** 1.0.0  
**Date:** September 22, 2026  
**Auditor:** Senior Surveillance Solutions & AI Video Analytics Architect  
**Codebase Baseline:** Commit `8fa82fd` (Branch `dev`)  
**Target Tenders:**  
1. **Tender A:** Kerala Police Pathanamthitta (GeM Ref: `G1-42272/2025/N`, ₹300 Lakh) — *Sabarimala Pilgrim Parking Management & CCTV Surveillance System*  
2. **Tender B:** KELTRON EOI (Ref: `KSEDC/KEC/PUR/SSG/EOI/003/2026-27`) — *AI Integrated Public Safety, Crowd Management, Mobility Management, and Command & Control Platform*

---

## 1. Executive Readiness Summary

| Dimension | Tender A (Police Parking / CCTV) | Tender B (KELTRON AI / ICCC) |
|---|---|---|
| **Core VMS & Ingest (RTSP/HLS/Rec)** | **90% READY** (MediaMTX + MinIO + FastAPI) | **85% READY** (Rock-solid ingestion & playback core) |
| **ANPR & Vehicle Management** | **15% READY** (Schema/UI not built; needs AI OCR engine) | **10% READY** (Architecture supports events, AI engine missing) |
| **Parking Management (PMS)** | **20% READY** (Multi-site hierarchy exists; slots/POS missing) | **15% READY** (Zone concept exists; parking engine missing) |
| **AI Video Analytics (Crowd/Pose)** | **5% READY** (Only basic ONVIF motion exists) | **5% READY** (No CV/ML models implemented in repo) |
| **Integrated Command Centre (ICCC)** | **40% READY** (React SPA dashboards, needs GIS map) | **30% READY** (Needs Common Operating Picture + GIS) |
| **Edge Appliance Architecture** | **85% READY** (7-loop Edge Agent + SQLite persistence) | **75% READY** (Edge agent ready for AI event forwarder) |
| **Infrastructure & Redundancy** | **50% READY** (Dockerized, but lacks Patroni/HA cluster) | **40% READY** (Requires active-active HA clustering) |
| **Bidder / Commercial Qualifications** | **0% SOFTWARE** (Requires Partner SI with ₹8–10Cr turnover) | **0% SOFTWARE** (Requires Partner SI + ISO/CMMI + 100 AI licenses) |

---

## 2. Deep Codebase Audit (What Exists vs. What is Scaffolded)

### 2.1 Verified Working Systems
1. **MediaMTX Camera Ingestion:**
   - [`surv/mediamtx/mediamtx.yml`](file:///opt/surv-learn/surv/mediamtx/mediamtx.yml): Ingests RTSP, RTSPS, and RTMP streams.
   - Dynamic path registration via REST API in [`surv/app/services/mediamtx_client.py`](file:///opt/surv-learn/surv/app/services/mediamtx_client.py).
   - Dynamic per-viewer authentication webhook via [`surv/app/routers/stream_auth.py`](file:///opt/surv-learn/surv/app/routers/stream_auth.py).
2. **Continuous & Sliced Recording Pipeline:**
   - 60-second fMP4 segment generation in MediaMTX.
   - Segment completion hook triggers [`surv/workers/upload_to_minio.py`](file:///opt/surv-learn/surv/workers/upload_to_minio.py).
   - Generates `.mp4` video chunk and `.json` metadata sidecar in MinIO bucket `recordings`.
   - Emits Kafka message on `recording.segments`.
   - [`surv/app/workers/segment_db_consumer.py`](file:///opt/surv-learn/surv/app/workers/segment_db_consumer.py) inserts metadata into `survapp_video_segment` with time-window classification (`full`, `motion`, `guard`).
3. **Multi-Tenant Hierarchy & RBAC:**
   - Database tables `organization` and `organization_closure` in [`surv/app/models/organization.py`](file:///opt/surv-learn/surv/app/models/organization.py) support infinite recursive tree traversal (ROOT → Circle → BA → SSA → Site).
   - Scoped camera access enforcement in [`surv/app/services/access_service.py`](file:///opt/surv-learn/surv/app/services/access_service.py).
4. **Edge NVR Appliance:**
   - [`edge-nvr/edge-agent/main.py`](file:///opt/surv-learn/edge-nvr/edge-agent/main.py): Operates 7 concurrent background loops (Heartbeat, Config Sync, Motion Forwarder, Status Monitor, Backup Clip Uploader, Retention Cleaner, Periodic Sync).
   - Uses local SQLite database (`edge_nvr.db`) to ensure zero event loss during network outages.
5. **Frontend Application:**
   - 13 production pages in React 18 / TypeScript 5 / Vite 5 / Tailwind CSS v4 in [`surv/frontend/src/`](file:///opt/surv-learn/surv/frontend/src/).
   - Live HLS player with low-latency buffering, 24-hour visual recording timeline, camera health monitor, audit log viewer.

### 2.2 Scaffolded or Missing Subsystems
1. **AI / ML Computer Vision Engine:**
   - **Current State:** Zero neural network models (no YOLO, no PyTorch, no TensorRT, no ONNX Runtime) exist in the codebase.
   - The only "motion detection" is raw ONVIF XML event polling from physical cameras in [`surv/onvif_producer/onvif_motion_producer.py`](file:///opt/surv-learn/surv/onvif_producer/onvif_motion_producer.py).
2. **ANPR & Vehicle Identification:**
   - No license plate recognition, OCR, vehicle classification, color detection, or speed calculation code exists anywhere in `surv/`, `edge-nvr/`, or `edge-sim/`.
3. **Parking Management System (PMS):**
   - No entities for parking zones, parking slots, POS handheld transactions, dynamic allocation logic, or parking slip generation.
4. **Integrated Command & Control Centre (ICCC) / GIS:**
   - No interactive GIS map engine (no Leaflet/Mapbox/OpenLayers) is integrated in the frontend; camera geolocation (`latitude`, `longitude`) is stored in the database but rendered only as text.
5. **High Availability (HA) Clustering:**
   - PostgreSQL runs as a single container without streaming replication, Patroni, or Pgpool. MinIO runs in single-node gateway mode.

---

## 3. SARVANETRA Capability Map

```
SARVANETRA PLATFORM CAPABILITY MAP
|
+-- 1. Video Management & Streaming (VMS Core)
|   |-- RTSP / RTSPS Ingest [ACTIVE] ................. surv/app/services/mediamtx_client.py
|   |-- RTMP Publisher Ingest (Drone/Broadcaster) [ACTIVE]  surv/app/services/mediamtx_client.py
|   |-- Low-Latency HLS Delivery (fMP4) [ACTIVE] ....... surv/nginx/conf.d/hls.conf
|   |-- WebRTC Live Streaming [ACTIVE] ................ surv/mediamtx/mediamtx.yml
|   |-- Token-Based Stream Authorization [ACTIVE] ...... surv/app/routers/stream_auth.py
|   +-- Dynamic Camera Management [ACTIVE] ............. surv/app/routers/cameras.py
|
+-- 2. Storage & Recording Pipeline
|   |-- 60s fMP4 Slicing [ACTIVE] ...................... surv/mediamtx/mediamtx.yml
|   |-- MinIO S3 Object Upload [ACTIVE] ................ surv/workers/upload_to_minio.py
|   |-- Metadata JSON Sidecar Creation [ACTIVE] ........ surv/workers/upload_to_minio.py
|   |-- Kafka Segment Event Dispatch [ACTIVE] .......... surv/workers/upload_to_minio.py
|   |-- Segment DB Ingestion & Tagging [ACTIVE] ........ surv/app/workers/segment_db_consumer.py
|   |-- Retention Purge Worker [ACTIVE] ................ surv/workers/minio_cleaner.py
|   +-- Timeline Playback Presigned URLs [ACTIVE] ...... surv/app/routers/recordings.py
|
+-- 3. Edge Appliance Control Plane (Edge NVR)
|   |-- Multi-Loop Edge Agent [ACTIVE] ................. edge-nvr/edge-agent/main.py
|   |-- Offline SQLite Event Persistence [ACTIVE] ...... edge-nvr/edge-agent/db.py
|   |-- Hub Configuration Sync [ACTIVE] ................ edge-nvr/edge-agent/config_sync.py
|   |-- Heartbeat & Telemetry [ACTIVE] ................. edge-nvr/edge-agent/heartbeat.py
|   |-- Selective Backup Clip Push to Hub [ACTIVE] ..... edge-nvr/edge-agent/backup_uploader.py
|   +-- Multi-Site Docker Simulation [ACTIVE] .......... edge-sim/docker-compose.yml
|
+-- 4. Event Bus & Messaging
|   |-- Kafka KRaft Event Hub [ACTIVE] ................. surv/docker-compose.yml
|   |-- Topic: camera.motion [ACTIVE] .................. surv/onvif_producer/
|   |-- Topic: recording.segments [ACTIVE] ............. surv/workers/upload_to_minio.py
|   +-- Topic: camera.status [ORPHAN TOPIC] ............ surv/scripts/camera_ready.sh
|
+-- 5. Multi-Tenancy & Access Control
|   |-- Recursive BSNL Hierarchy [ACTIVE] .............. surv/app/models/organization.py
|   |-- Closure Table Tree Traversal [ACTIVE] .......... surv/app/services/access_service.py
|   |-- Granular RBAC Permissions [ACTIVE] ............. surv/app/models/role.py
|   +-- JWT Session Security in Postgres [ACTIVE] ...... surv/app/services/auth_service.py
|
+-- 6. Command Center & User Interface
|   |-- Single Page Web Application [ACTIVE] ........... surv/frontend/src/App.tsx
|   |-- Multi-Grid Camera Wall [ACTIVE] ................ surv/frontend/src/pages/LiveViewPage.tsx
|   |-- Interactive Recording Timeline [ACTIVE] ........ surv/frontend/src/pages/RecordingsPage.tsx
|   |-- Fleet Appliance Dashboard [ACTIVE] ............. surv/frontend/src/pages/FleetManagementPage.tsx
|   +-- User & Audit Logs [ACTIVE] ..................... surv/frontend/src/pages/AuditLogsPage.tsx
|
+-- 7. Analytics & AI (GAPS)
|   |-- Camera-Native ONVIF Motion Polling [ACTIVE] .... surv/onvif_producer/onvif_motion_producer.py
|   |-- Automated Stale Event Closer [ACTIVE] .......... surv/app/routers/motion.py
|   |-- ANPR / License Plate OCR [MISSING]
|   |-- Vehicle Classification & Color [MISSING]
|   |-- Crowd Density & Estimation [MISSING]
|   |-- People Counting & Directional Flow [MISSING]
|   |-- Facial Recognition & Re-ID [MISSING]
|   +-- Predictive Congestion Analytics [MISSING]
|
+-- 8. Domain Extensions (GAPS)
|   |-- Parking Zone & Slot Management [MISSING]
|   |-- Handheld Android POS Printing Bridge [MISSING]
|   |-- GIS Map Common Operating Picture [MISSING]
|   |-- Public Address (PA) Audio Dispatch [MISSING]
|   +-- Drone Flight Telemetry & Missions [MISSING]
```

---

## 4. Tender-to-Code Mapping Matrix

### Compliance Status Legend:
* **GREEN:** Currently satisfied in existing codebase.
* **YELLOW:** Partially satisfied; scaffolding, models, or basic flows exist.
* **ORANGE:** Implementable within SARVANETRA architecture, but code must be written.
* **BLUE:** Requires specialized third-party product, external AI engine, or integration partner.
* **RED:** Architectural incompatibility or fundamentally outside platform capabilities.
* **GRAY:** Not a software platform requirement (hardware supply, civil works, bidder financials, OEM qualifications).
* **BLACK:** Unknown / Requires physical verification on-site.

| Req ID | Requirement | Tender Source | SARVANETRA Status | Evidence in Code | Identified Gap | Required Work | External Dependency |
|---|---|---|---|---|---|---|---|
| **T1-PMS-001** | 12 Parking Grounds Monitoring | Tender A (p1, 2) | **YELLOW** | [`models/organization.py`](file:///opt/surv-learn/surv/app/models/organization.py) | Sites exist, but no specialized "parking zone" entity | Add `parking_zone` model with capacity and zone-type metadata | None |
| **T1-PMS-002** | Automated Parking Ground Allocation | Tender A (p2) | **ORANGE** | None | No allocation logic or occupancy tracking engine | Build `ParkingAllocationService` computing real-time zone delta | Inflow/Outflow sensors |
| **T1-PMS-003** | Handheld Android POS Parking Slip | Tender A (p2, 13) | **BLUE** | [`routers/mobile.py`](file:///opt/surv-learn/surv/app/routers/mobile.py) | No POS terminal application or thermal printing service | Build Android POS APK communicating with Hub REST API | Android POS Hardware OEM |
| **T1-PMS-004** | Zone-wise Real-Time Occupancy | Tender A (p2) | **ORANGE** | None | No vehicle counter or occupancy accumulator | Implement Redis/PostgreSQL counters updated by ANPR/POS events | None |
| **T1-PMS-005** | Live Dashboards at CCR & Aid Posts | Tender A (p2) | **YELLOW** | [`pages/DashboardPage.tsx`](file:///opt/surv-learn/surv/frontend/src/pages/DashboardPage.tsx) | General stats exist; no parking occupancy widgets | Create dedicated Parking Dashboard with live zone occupancy bar charts | Client PC / Displays |
| **T1-PMS-006** | Future Bay-by-Bay Sensors & Paid Ops | Tender A (p3, 4) | **ORANGE** | None | Data models lack slot-level geometry and tariff rules | Design extensible slot entity and billing ledger tables | IoT Bay Sensors |
| **T1-PMS-007** | 26-Lane PMS Software Licensing | Tender A (p12) | **ORANGE** | None | SARVANETRA has no license tiering or lane limits | Add license enforcement module or deploy as enterprise edition | None |
| **T1-ANPR-001** | ANPR License Plate OCR | Tender A (p3, 34) | **BLUE** | None | Zero OCR or license plate detection code | Integrate edge ANPR inference pipeline (TensorRT / DeepStream / OpenALPR) | ANPR Engine / LPU |
| **T1-ANPR-002** | Vehicle Classification (LMV/HMV/etc.) | Tender A (p3, 34) | **BLUE** | None | No vehicle classifier model in repo | Deploy multi-class vehicle detection model (YOLOv8x) | GPU / LPU |
| **T1-ANPR-003** | Make, Brand, and Color Detection | Tender A (p3, 34) | **BLUE** | None | No color or vehicle brand classifier | Deploy secondary vehicle attribute recognition model | GPU / LPU |
| **T1-ANPR-004** | Hotlist / Watchlist Matching & Alerts | Tender A (p3, 34) | **ORANGE** | [`models/motion.py`](file:///opt/surv-learn/surv/app/models/motion.py) | Alerting exists for camera offline, but no plate watchlist | Create `vehicle_watchlist` table and Kafka stream matcher | None |
| **T1-ANPR-005** | Parked Vehicle Zone Tracking | Tender A (p3) | **ORANGE** | None | No correlation between plate reads and parking zones | Implement parking session tracking table (`parking_session`) | Entry/Exit ANPR cameras |
| **T1-ANPR-006** | Day/Night/Rain/Fog ANPR Capability | Tender A (p3, 38) | **GRAY** | None | Camera hardware optics and IR illumination requirement | Procure compliant ANPR cameras with 850nm IR illuminator | Camera OEM |
| **T1-ANPR-007** | 230 km/h ARAI Speed Certification | Tender A (p34, 40) | **GRAY / BLUE** | None | Official ARAI / Rule 126 CMVR test certificate required | Partner with ARAI-certified ANPR OEM | Certified ANPR OEM |
| **T1-ANPR-008** | Local LPU Processing (Network Resilient) | Tender A (p34, 38) | **YELLOW** | [`edge-nvr/edge-agent/`](file:///opt/surv-learn/edge-nvr/edge-agent/) | Edge agent exists, but runs no local AI inference | Port lightweight ANPR worker to edge LPU stack | Industrial LPU PC |
| **T1-ANPR-009** | 90–95% Recognition Accuracy | Tender A (p35) | **BLUE** | None | Accuracy depends on model training on Indian plates | Integrate pretrained Indian HSRP-trained OCR model | Specialized CV Model |
| **T1-ANPR-010** | Helmet & Triple Riding Violations | Tender A (p35, 41) | **BLUE** | None | No 2-wheeler rider violation model | Deploy rider pose & helmet detection model | GPU Inference |
| **T1-ANPR-011** | Damaged Number Plate Detection | Tender A (p34) | **BLUE** | None | No plate damage segmentation model | Add anomaly classifier to ANPR pipeline | CV Model |
| **T1-ANPR-012** | Plate & JPEG Storage in PostgreSQL | Tender A (p34, 41) | **ORANGE** | [`models/base.py`](file:///opt/surv-learn/surv/app/models/base.py) | Schema lacks vehicle transaction table | Add `anpr_transaction` table + MinIO JPEG bucket storage | None |
| **T1-ANPR-013** | Fuzzy Plate Search (Edit Distance 1-2) | Tender A (p35, 42) | **ORANGE** | None | Standard SQL ILIKE search only | Enable PostgreSQL `pg_trgm` and `levenshtein()` queries | None |
| **T1-ANPR-014** | Tamper-Proof Date/Time Watermarking | Tender A (p42) | **ORANGE** | None | Snapshots stored without cryptographic overlay | Add Pillow/FFmpeg overlay filter with SHA-256 digital signature | None |
| **T1-ANPR-015** | Bi-Lingual GUI (English & Malayalam) | Tender A (p42) | **ORANGE** | [`frontend/package.json`](file:///opt/surv-learn/surv/frontend/package.json) | UI strings are hardcoded in English | Integrate `i18next` and add Malayalam translation bundle | Localization |
| **T1-ANPR-016** | Pre/Post Clip Slicing on Hotlist Match | Tender A (p42) | **ORANGE** | [`workers/upload_to_minio.py`](file:///opt/surv-learn/surv/workers/upload_to_minio.py) | Slices fixed 60s chunks; cannot slice custom event windows | Implement FFmpeg trimmer worker extracting [-15s, +15s] window | None |
| **T1-ANPR-017** | Manual Plate Correction & Audit Trail | Tender A (p42) | **ORANGE** | [`models/audit.py`](file:///opt/surv-learn/surv/app/models/audit.py) | Generic audit log exists; no vehicle plate edit flow | Add `corrected_plate_number` field and log correction in audit | None |
| **T1-ANPR-018** | Vehicle-Based Pilgrim Estimation | Tender A (p3, 34) | **ORANGE** | None | No passenger multiplier calculation | Add configurable seating capacity multipliers to traffic API | None |
| **T1-ANPR-019** | Traffic Reports (Hourly/Daily/Monthly) | Tender A (p3, 38) | **ORANGE** | None | No traffic aggregation SQL views or report downloads | Add `reporting.py` router aggregating vehicle transactions | None |
| **T1-ANPR-020** | State Police HQ & Pathanamthitta Feed | Tender A (p9, 37) | **YELLOW** | [`services/mediamtx_client.py`](file:///opt/surv-learn/surv/app/services/mediamtx_client.py) | MediaMTX supports RTSP re-streaming; no direct API bridge | Expose standardized REST/WebSocket/RTSP feeds to State PHQ | State PHQ Network |
| **T1-ANPR-021** | 2 Nos 5MP ANPR Bullet Cameras | Tender A (p9, 25) | **GRAY** | None | Physical camera procurement and mounting | Partner with OEM (Honeywell, Uniview, CP PLUS, Axis) | Camera OEM |
| **T1-ANPR-022** | 2 Nos External 850nm IR Illuminators | Tender A (p9, 35) | **GRAY** | None | Physical hardware supply (IEC-62471 eye safety) | Procurement | Hardware Vendor |
| **T1-ANPR-023** | 1 No Field Server / LPU (MIL-STD-810G) | Tender A (p9, 36) | **GRAY** | None | Physical industrial PC supply | Procurement (Advantech, Neousys, Lanner) | Industrial PC OEM |
| **T1-CCTV-001** | 51 CCTV Cameras Deployment (Nilakkal) | Tender A (p4) | **GRAY** | None | Physical supply of 25 PMS, 16 bullet, 10 PTZ cameras | Procurement & Installation | Camera OEM / SI |
| **T1-CCTV-002** | 90-Day CCTV Recording Retention | Tender A (p3) | **YELLOW** | [`workers/minio_cleaner.py`](file:///opt/surv-learn/surv/workers/minio_cleaner.py) | Cleaner supports retention days, but requires enterprise storage | Configure `retention_days=90` in DB; size storage cluster (80TB+) | Enterprise Storage |
| **T1-CCTV-003** | Evidentiary Video Export (Signed) | Tender A (p3) | **YELLOW** | [`routers/recordings.py`](file:///opt/surv-learn/surv/app/routers/recordings.py) | Presigned download exists, lacks digital signature/hash | Add SHA-256 checksum and digital watermark to exported MP4 | None |
| **T1-CCTV-004** | 7-Day Edge / 90-Day Central ANPR Store | Tender A (p3) | **YELLOW** | [`edge-agent/db.py`](file:///opt/surv-learn/edge-nvr/edge-agent/db.py) | Edge SQLite supports retention, central MinIO supports retention | Set SQLite TTL to 7 days and central DB/MinIO retention to 90 days | None |
| **T1-CCTV-005** | STQC / BIS Certified Bullet Cameras | Tender A (p10, 22) | **GRAY** | None | Hardware certification compliance | Procure STQC/BIS certified models | Camera OEM |
| **T1-CCTV-006** | STQC / BIS Certified PTZ Cameras | Tender A (p14, 28) | **GRAY** | None | Hardware certification compliance | Procure STQC/BIS certified models | Camera OEM |
| **T1-CCTV-007** | 32-Channel 4K NVR with TPM Chipset | Tender A (p14, 31) | **GRAY** | None | Physical hardware NVR supply | Procure standalone hardware NVR | Hardware NVR OEM |
| **T1-CCTV-008** | Visual Shifting (Police Stn to Control Rm)| Tender A (p2, 6) | **GREEN** | [`pages/LiveViewPage.tsx`](file:///opt/surv-learn/surv/frontend/src/pages/LiveViewPage.tsx) | Web-based HLS/WebRTC streaming runs from any authorized browser | Simply log into browser at Nilakkal Control Room | None |
| **T1-NET-001** | 6-Core OFC Redundant Network | Tender A (p4, 50) | **GRAY** | None | Physical cable laying, trenching, HDPE ducting | Civil / Fiber execution | OFC Contractor |
| **T1-NET-002** | High-Speed Redundant Ring Topology | Tender A (p4) | **GRAY** | None | Switch configuration (ERPS / RSTP / MSTP) | Switch network engineering | Network Engineer |
| **T1-NET-003** | 2 Nos 10G/25G Layer-3 Core Switches | Tender A (p15, 47) | **GRAY** | None | Enterprise switch hardware supply | Procure MTCTE certified switches | Switch OEM |
| **T1-NET-004** | 13 Nos 8-Port PoE+ Field Switches | Tender A (p15, 46) | **GRAY** | None | Industrial field switch hardware supply | Procure Layer-2+ PoE+ switches | Switch OEM |
| **T1-PWR-001** | Sabarimala CCTV UPS Revamp (Pampa/Sanni)| Tender A (p5, 58) | **GRAY** | None | Electrical UPS hardware and battery bank supply | Procure 3kVA/6kVA online UPS + battery banks | Electrical OEM |
| **T1-PWR-002** | 12 Nos Field Pole UPS (6-Hr Backup) | Tender A (p11, 16) | **GRAY** | None | 1000VA UPS + 120AH battery procurement | Procure outdoor pole UPS | UPS OEM |
| **T1-PA-001** | IP Public Address Console & Speakers | Tender A (p3, 18) | **BLUE** | None | Audio streaming and IP horn speaker integration | Add SIP/VoIP audio dispatch module or integrate third-party PA | PA System OEM |
| **T1-CIVIL-001** | 33 Poles, Gantry, Excavation, Barricades | Tender A (p12, 15) | **GRAY** | None | Civil engineering, STAAD PRO design, fabrication | Civil contracting | Civil Contractor |
| **T1-CCR-001** | Video Wall Displays & Workstations | Tender A (p4, 45) | **GRAY** | None | Hardware procurement (55" 4K displays, i7 client PCs) | IT Hardware supply | Display / PC OEM |
| **T1-SLA-001** | 36-Month Onsite Warranty & 24hr MTTR | Tender A (p6, 7) | **GRAY** | None | Contractual SLA commitment | Provide field service engineering team | System Integrator |
| **T1-SLA-002** | 24x7 Resident Site Engineer Deployment | Tender A (p7) | **GRAY** | None | Dedicated manpower deployment at Nilakkal | Station qualified engineer on-site | SI Manpower |
| **T1-QUAL-001**| Turnver >= ₹10 Cr, Solvency ₹10 Cr | Tender A (p8, 21) | **GRAY** | None | Prime bidder financial qualification | Bid via qualified consortium lead / prime contractor | Bidder Finance |
| **T1-QUAL-002**| Past Govt Work: 1x ₹10Cr / 2x ₹5Cr | Tender A (p8, 21) | **GRAY** | None | Bidder past performance qualification | Submit qualifying work completion certificates | Prime SI Partner |
| **T1-QUAL-003**| Active Office in Kerala with GST | Tender A (p8, 21) | **GRAY** | None | Statutory entity registration in Kerala | Provide Kerala GST certificate | Prime Bidder |
| **T1-QUAL-004**| Non-Chinese Origin / GFR 144(xi) | Tender A (p19, 20) | **GRAY** | None | Hardware country of origin declarations | Procure TAA/Indian compliant cameras & switches | OEMs |
| **T1-QUAL-005**| ANPR OEM in India >10y, R&D in India | Tender A (p21) | **GRAY / BLUE** | None | ANPR software OEM credentials | Partner with qualified Indian ANPR vendor (e.g. Vehant, Videonetics) | ANPR Partner |
| **T1-QUAL-006**| Parking OEM Installed >=3000 Lots in PSU| Tender A (p22) | **GRAY / BLUE** | None | Parking software reference credentials | Partner with proven parking OEM or bid as custom development | Parking Partner |
| **T1-SEC-001** | CERT-In Vulnerability Assessment Cert | Tender A (p35, 40) | **ORANGE / L** | None | Application security hardening and formal audit | Perform SAST/DAST, remediate CVEs, undergo CERT-In audit | CERT-In Auditor |
| **T2-VMS-001** | Centralized VMS Live & Recording | Tender B (p10, 11) | **GREEN** | [`surv/mediamtx/`](file:///opt/surv-learn/surv/mediamtx/), [`surv/app/`](file:///opt/surv-learn/surv/app/) | Full live streaming, recording, and MinIO storage operational | Close P0 blocking issues (kcat, snapshot mismatch) | None |
| **T2-VMS-002** | Event-Based Recording & Smart Search | Tender B (p11) | **YELLOW** | [`workers/segment_db_consumer.py`](file:///opt/surv-learn/surv/app/workers/segment_db_consumer.py) | Segments tagged with `motion`; lacking AI event tags | Add AI event labels to segment schema | None |
| **T2-VMS-003** | Camera Health Monitoring & Alerting | Tender B (p11) | **GREEN** | [`workers/status_monitor.py`](file:///opt/surv-learn/surv/workers/status_monitor.py), [`workers/notifier.py`](file:///opt/surv-learn/surv/workers/notifier.py) | Dynamic MediaMTX and TCP polling, DB/webhook notification | Add UI notification toaster | None |
| **T2-AI-001** | Perimeter Intrusion Detection | Tender B (p7) | **BLUE** | None | No computer vision polygon intrusion model | Deploy edge/central CV inference service with RTSP pipeline | GPU / CV Model |
| **T2-AI-002** | Line Crossing / Tripwire Detection | Tender B (p7) | **BLUE** | None | No tripwire vector math or object tracking | Implement directional line-crossing algorithm | CV Model |
| **T2-AI-003** | Loitering Detection | Tender B (p7) | **BLUE** | None | No trajectory dwell-time accumulator | Implement ByteTrack/DeepSORT + polygon dwell timer | CV Model |
| **T2-AI-004** | Abandoned / Unattended Object Detection| Tender B (p7) | **BLUE** | None | No stationary object segmentation | Deploy background subtraction / dual-time segmentation model | CV Model |
| **T2-AI-005** | Fall Detection | Tender B (p7) | **BLUE** | None | No human pose estimation | Deploy YOLOv8-pose / RTMPose keypoint model | GPU Inference |
| **T2-AI-006** | Suspicious / Abnormal Behavior | Tender B (p7) | **BLUE** | None | No spatio-temporal action recognition | Deploy action recognition network (SlowFast / VideoMAE) | GPU Inference |
| **T2-AI-007** | Multi-Class Object Classification | Tender B (p7) | **BLUE** | None | No general detector running in pipeline | Deploy YOLOv10/RT-DETR inference container | GPU / LPU |
| **T2-AI-008** | Multi-Camera Person/Vehicle Re-ID | Tender B (p7) | **BLUE** | None | No feature vector extractor or vector index | Deploy OSNet / FastReID + Milvus vector database | Vector DB / GPU |
| **T2-FLOW-001**| Entry / Exit Counting Across Lines | Tender B (p8) | **BLUE** | None | No directional counting algorithm | Deploy line crossing counter emitting Kafka count events | CV Model |
| **T2-FLOW-002**| Real-Time Area Occupancy & Throughput | Tender B (p8) | **ORANGE** | None | No occupancy state machine | Implement occupancy aggregator consuming entry/exit counts | None |
| **T2-FLOW-003**| Queue Length & Wait-Time Estimation | Tender B (p8) | **BLUE** | None | No queue clustering algorithm | Implement spatial bounding-box queue detector | CV Model |
| **T2-FLOW-004**| Flow Visualization & Movement Heatmaps | Tender B (p8) | **ORANGE** | None | No spatial trajectory accumulator | Implement coordinate accumulator + canvas heatmap generator | None |
| **T2-CROWD-001**| Continuous Crowd Density (persons/m²) | Tender B (p8, 13) | **BLUE** | None | No density map regression model | Deploy CSRNet / DM-Count crowd density model | GPU Server |
| **T2-CROWD-002**| Congestion Alert & Threshold Rules | Tender B (p8) | **ORANGE** | [`routers/motion.py`](file:///opt/surv-learn/surv/app/routers/motion.py) | Motion event pipeline exists; needs threshold rules | Build threshold evaluation engine on Kafka crowd events | None |
| **T2-PRED-001**| Predictive Crowd Build-Up & Queue Trend| Tender B (p8) | **BLUE** | None | No predictive ML models | Deploy time-series forecaster (Prophet / LSTM) on historical counts | Data Science |
| **T2-PRED-002**| Demand & Capacity Risk Forecasting | Tender B (p8) | **BLUE** | None | No statistical risk modeling | Implement risk calculation service | Data Science |
| **T2-JOURNEY-001**| End-to-End Journey Intelligence | Tender B (p9) | **ORANGE** | [`models/organization.py`](file:///opt/surv-learn/surv/app/models/organization.py) | Has location hierarchy; lacks visitor tracking session | Design `visitor_journey` schema linking ANPR, flow, and gates | Multi-modal data |
| **T2-ANPR-001**| AI ANPR (Tracking, Whitelist, Search) | Tender B (p9) | **BLUE / ORANGE**| None | ANPR engine missing; database/API implementable | Deploy ANPR OCR service + SARVANETRA vehicle search API | ANPR Engine |
| **T2-PARK-001**| Smart Parking Management & Guidance | Tender B (p9) | **ORANGE** | None | No parking domain logic | Build parking allocation and occupancy microservice | None |
| **T2-MISSING-001**| Face-Based Search & Last-Seen Location | Tender B (p9, 10)| **BLUE** | None | No face detection, feature extraction, or gallery | Deploy InsightFace / ArcFace + `pgvector` / Milvus | GPU / Vector DB |
| **T2-DRONE-001**| Drone Video Stream Ingest (RTMP/RTSP) | Tender B (p10) | **GREEN** | [`services/mediamtx_client.py#L68-L77`](file:///opt/surv-learn/surv/app/services/mediamtx_client.py#L68-L77) | MediaMTX RTMP publisher mode natively ingests drone video | Add UI preset for drone feeds | None |
| **T2-DRONE-002**| Drone Telemetry, Mission & GIS Overlay | Tender B (p10) | **BLUE** | None | No MAVLink or drone telemetry parser | Implement MAVLink listener and map coordinate tracker | Drone SDK / Pilot |
| **T2-OPRESP-001**| Automated SOP & Crowd Regulation | Tender B (p10) | **ORANGE** | None | No workflow execution engine | Implement rule/action workflow engine (Temporal or Celery) | None |
| **T2-OPRESP-002**| PA, VMS, and Digital Signage Push | Tender B (p10) | **BLUE** | None | No hardware broadcast integration | Implement NTCIP/TCP driver for VMS and SIP for PA | VMS/PA Hardware |
| **T2-ICCC-001**| Common Operating Picture (COP) ICCC UI | Tender B (p11, 13)| **YELLOW** | [`frontend/src/pages/`](file:///opt/surv-learn/surv/frontend/src/pages/) | Individual pages exist; lacks single-pane unified COP | Build composite executive dashboard matching Tender B mockup (p13) | None |
| **T2-ICCC-002**| GIS Map Overlay (Cameras, Sensors, UAV) | Tender B (p11, 13)| **ORANGE** | None | Cameras have lat/long, but no map component in UI | Integrate MapLibre/Leaflet with dynamic GeoJSON entity pins | Map Tile Server |
| **T2-ICCC-003**| Incident Lifecycle Management & Audit | Tender B (p11) | **ORANGE** | [`models/audit.py`](file:///opt/surv-learn/surv/app/models/audit.py) | Audit logs exist; no incident ticketing or workflow | Build `incident` and `incident_update` database models and API | None |
| **T2-ICCC-004**| Mobile App for Field Responders | Tender B (p11) | **BLUE** | [`routers/mobile.py`](file:///opt/surv-learn/surv/app/routers/mobile.py) | Endpoints return 501; no mobile app exists | Develop React Native / Expo cross-platform mobile client | Mobile Dev |
| **T2-ARCH-001**| Open Standards, Modular Microservices | Tender B (p11, 12)| **GREEN** | [`surv/app/main.py`](file:///opt/surv-learn/surv/app/main.py) | Clean FastAPI routers, OpenAPI 3.0 specs, Kafka event bus | Continue modular microservice pattern | None |
| **T2-ARCH-002**| Cloud, On-Premises, and Hybrid Deploy | Tender B (p12) | **GREEN** | [`surv/docker-compose.yml`](file:///opt/surv-learn/surv/docker-compose.yml) | 100% containerized; portable across cloud VMs and on-prem | Maintain docker / K8s manifests | None |
| **T2-ARCH-003**| High Availability (No Single Point of Fail)| Tender B (p12) | **YELLOW** | Docker Compose single nodes | Architecture supports HA; compose currently runs 1 instance | Upgrade to 3-node Kafka KRaft, MinIO Distributed, Kong HA | Cloud/Baremetal HA |
| **T2-ARCH-004**| Database Clustering & Auto Failover | Tender B (p12) | **ORANGE** | Single Postgres container | PostgreSQL 16 is standard; no Patroni/pgpool cluster | Configure Patroni + etcd + HAProxy for PostgreSQL | HA Infrastructure |
| **T2-SEC-001** | DPDP Act 2023 Compliance & Privacy | Tender B (p12) | **ORANGE** | None | No face/plate auto-blurring or user consent tracking | Implement automated video redaction pipeline and retention limits | Legal Counsel |
| **T2-SEC-002** | Secure SDLC based on OWASP Top 10 | Tender B (p12) | **YELLOW** | Alembic, Pydantic, Bcrypt, JWT | Solid baseline; lacks automated security scanning in CI/CD | Add Bandit, Trivy, and GitHub Actions SAST pipeline | CI/CD Runner |
| **T2-SEC-003** | Third-Party CERT-In Security Audit | Tender B (p12) | **ORANGE / L** | None | Must undergo formal penetration testing prior to Go-Live | Execute vulnerability remediation and schedule audit | CERT-In Auditor |
| **T2-DELIV-001**| Full Source Code & IP Transfer | Tender B (p12, 18)| **GREEN / L** | Complete proprietary codebase | SARVANETRA is custom Python/React code, easily transferable | Ensure zero proprietary third-party IP lock-in | Legal Agreement |
| **T2-DELIV-002**| 5-Year Comprehensive Warranty & SLA | Tender B (p12, 18)| **GRAY** | None | Commercial support commitment | Negotiate SLA back-to-back with consortium partners | Consortium Partners |
| **T2-MANPOWER-001**| 12 Named Expert Manpower Staffing | Tender B (p14) | **GRAY** | None | Mandatory CVs of qualified personnel (Architect, Leads, DBAs)| Form consortium with experienced IT staffing partner | Consortium HR |
| **T2-QUAL-001**| Turnover >= ₹8 Cr, Positive Net Worth | Tender B (p4) | **GRAY** | None | Prime bidder financial qualification | Lead bidder with audited balance sheets | Prime Bidder |
| **T2-QUAL-002**| Past Experience: ₹3 Cr + 100 AI Licenses| Tender B (p5, 6) | **GRAY** | None | Past government project credentials | Partner with experienced Indian AI Surveillance SI | Lead SI Partner |
| **T2-QUAL-003**| ISO 9001, ISO 27001, CMMI Level 3 | Tender B (p5, 7) | **GRAY** | None | Company process certifications | Submit certificates of Lead Bidder / Consortium | Prime Bidder |
| **T2-QUAL-004**| Live Technical Demo (30 Marks) | Tender B (p7) | **GREEN** | Working Codebase & Simulation | SARVANETRA live streaming, UI, and edge simulation run today | Stage polished live demo environment using `edge-sim` | None |

---

## 5. Platform vs. Product Distinction (What SARVANETRA Owns vs. What it Needs)

A critical error in surveillance tender responses is claiming the software platform can do everything natively. SARVANETRA must be positioned as the **Central Intelligent Platform and Operating Core**, seamlessly integrating specialized hardware and OEM engines:

| Functional Area | SARVANETRA Platform Scope (Owns) | Required External Product / OEM (Needs) |
|---|---|---|
| **Video Ingestion & Playback** | RTSP/RTSPS/RTMP ingest, fMP4 chunking, HLS streaming, token auth, timeline UI | Physical IP Bullet/PTZ cameras (STQC/BIS certified), NVR appliances |
| **Storage & Retention** | S3 object routing, metadata sidecars, retention lifecycle cleaner, presigned URLs | Enterprise Server Storage (RAID 10 SSD/HDD), SAN/NAS physical enclosures |
| **ANPR & Traffic Analysis** | Transaction database, watchlist matcher, fuzzy search, traffic dashboards, alerts | Certified ANPR Camera with 850nm IR, ARAI-certified ANPR OCR inference engine |
| **Parking Management (PMS)** | Dynamic zone allocation logic, occupancy accumulator, central dashboards | Handheld Android POS terminals with thermal printers, physical parking barriers |
| **AI Video Analytics** | Event ingestion schema, Kafka distribution, rule engine, alert notifications, UI overlay | Edge LPU (i7/NVIDIA GPU), Computer Vision models (Intrusion, Pose, Crowd Density) |
| **Command Centre (ICCC)** | Unified Common Operating Picture, GIS layer rendering, incident workflow, audit logs | 55" 4K Video Wall, operator workstations, GIS map tile provider (Google/Mapbox) |
| **Public Safety Dispatch** | Event trigger rule execution, notification dispatch, action audit trails | IP Horn Speakers, PA Console, Variable Message Signs (VMS), SMS Gateway |
| **Perimeter & Security** | RBAC, recursive org tenancy, JWT sessions, API gateway routing, non-tamperable logs | CERT-In empaneled security audit agency, formal ISO/CMMI company credentials |

---

## 6. Tender A (Pathanamthitta Police) Specific Evaluation

### Detailed Technical Audit against the 34 Key Requirements:
1. **12 Parking Zones:** **PARTIALLY SATISFIED (YELLOW).** Hierarchy supports unlimited sites via [`models/organization.py`](file:///opt/surv-learn/surv/app/models/organization.py), but needs a specialized `parking_zone` entity to track vehicle capacity, current count, and overflow status.
2. **Automated Parking Allocation:** **IMPLEMENTABLE (ORANGE).** Requires an allocation algorithm that checks real-time occupancy across Zones 1–12 and assigns incoming vehicles to the nearest available zone with capacity.
3. **Parking Occupancy Calculation:** **IMPLEMENTABLE (ORANGE).** Needs counter logic: `Occupancy = Initial_Seed + Σ(Entries) - Σ(Exits)` per zone.
4. **Dynamic Vacancy Information:** **IMPLEMENTABLE (ORANGE).** Simple API endpoint `GET /api/v1/parking/zones/vacancy` exposing capacity minus occupancy.
5. **Parking Dashboards:** **PARTIALLY SATISFIED (YELLOW).** Frontend architecture easily supports adding new widgets; dashboard currently shows camera counts, needs parking occupancy charts.
6. **POS-Generated Parking Slips:** **REQUIRES THIRD-PARTY (BLUE).** Mandates handheld Android POS terminals (Quad-core ARM, Android 13, 58mm thermal printer). SARVANETRA must provide a lightweight Android app connecting to `POST /api/v1/parking/entry-slip`.
7. **ANPR Entry/Exit Tracking:** **REQUIRES THIRD-PARTY / DEVELOPMENT (BLUE/ORANGE).** Requires edge ANPR camera or LPU running OCR to send JSON payloads (`{plate, vehicle_type, timestamp, direction, image_url}`) to the Hub API.
8. **Vehicle Classification:** **REQUIRES THIRD-PARTY (BLUE).** LMV, HMV, Cars, Buses, 2/3-wheelers must be classified by an AI vision model running on the LPU or camera.
9. **Vehicle Make / Brand:** **REQUIRES THIRD-PARTY (BLUE).** Requires a secondary vehicle attribute classification model.
10. **Vehicle Color:** **REQUIRES THIRD-PARTY (BLUE).** Daytime vehicle color detection requires an AI attribute classifier.
11. **Hotlist / Watchlist:** **IMPLEMENTABLE (ORANGE).** Database table `vehicle_watchlist` with status ("Wanted", "Stolen", "Suspicious") and Kafka alert trigger.
12. **Event Alerts (<2–3s):** **CURRENTLY SATISFIED (GREEN).** Kafka event pipeline propagates events from producer to consumer in under 100 milliseconds.
13. **90-Day CCTV Retention:** **CURRENTLY SATISFIED (GREEN).** [`workers/minio_cleaner.py`](file:///opt/surv-learn/surv/workers/minio_cleaner.py) enforces configurable retention days; hardware storage must be sized to hold 90 days.
14. **7-Day Local ANPR Storage:** **CURRENTLY SATISFIED (GREEN).** [`edge-nvr/edge-agent/db.py`](file:///opt/surv-learn/edge-nvr/edge-agent/db.py) retains local records in SQLite; cleanup worker can purge records older than 7 days.
15. **90-Day Central ANPR Storage:** **CURRENTLY SATISFIED (GREEN).** PostgreSQL relational tables retain historical transactions indefinitely or per retention policy.
16. **Historical Analytics:** **IMPLEMENTABLE (ORANGE).** SQL aggregation queries by date, hour, zone, and vehicle type.
17. **Vehicle Volume Analytics:** **IMPLEMENTABLE (ORANGE).** Time-series volume charting on frontend.
18. **Traffic Trends:** **IMPLEMENTABLE (ORANGE).** Peak-hour trend charts comparing day-over-day or week-over-week traffic.
19. **Pilgrim Estimation:** **IMPLEMENTABLE (ORANGE).** Arithmetic calculation: `Pilgrims = (Buses * 50) + (Cars * 5) + (2-Wheelers * 2)`.
20. **IP Public Address:** **REQUIRES THIRD-PARTY (BLUE).** Hardware horn speakers and touch announcing console required; software can integrate via SIP/VoIP.
21. **Live Monitoring:** **CURRENTLY SATISFIED (GREEN).** Low-latency HLS and WebRTC multi-grid live monitoring working in [`pages/LiveViewPage.tsx`](file:///opt/surv-learn/surv/frontend/src/pages/LiveViewPage.tsx).
22. **PTZ Control:** **PARTIALLY SATISFIED (YELLOW).** MediaMTX and ONVIF support PTZ commands; frontend needs PTZ joystick/directional buttons wired to ONVIF PTZ service.
23. **Centralized CCTV:** **CURRENTLY SATISFIED (GREEN).** Multi-camera ingestion and central monitoring operational.
24. **Video Export:** **CURRENTLY SATISFIED (GREEN).** Segments downloadable as standard MP4 files via presigned S3 URLs.
25. **Redundant Network:** **NOT A SOFTWARE REQUIREMENT (GRAY).** Dual 6-core OFC ring network and managed switches.
26. **Control Room Modernization:** **NOT A SOFTWARE REQUIREMENT (GRAY).** Supply of 55" video wall displays and operator workstations.
27. **Seasonal Camera-View Relocation:** **CURRENTLY SATISFIED (GREEN).** Web-based architecture allows instant monitoring from Nilakkal Police Station or Nilakkal Control Room by opening the web browser URL.
28. **UPS Integration:** **NOT A SOFTWARE REQUIREMENT (GRAY).** Physical 3kVA/6kVA UPS and battery banks.
29. **Health Monitoring:** **CURRENTLY SATISFIED (GREEN).** Automated status monitor and alerting in [`workers/status_monitor.py`](file:///opt/surv-learn/surv/workers/status_monitor.py).
30. **Audit Logs:** **CURRENTLY SATISFIED (GREEN).** Non-tamperable audit log tracking in [`models/audit.py`](file:///opt/surv-learn/surv/app/models/audit.py).
31. **Role-Based Access:** **CURRENTLY SATISFIED (GREEN).** Granular RBAC and hierarchical scoping in [`services/access_service.py`](file:///opt/surv-learn/surv/app/services/access_service.py).
32. **Reporting:** **IMPLEMENTABLE (ORANGE).** PDF/CSV export of traffic, occupancy, and camera health logs.
33. **API / Integration:** **CURRENTLY SATISFIED (GREEN).** Clean FastAPI REST APIs with OpenAPI documentation.
34. **Warranty / O&M Support:** **NOT A SOFTWARE REQUIREMENT (GRAY).** 36-month onsite warranty and resident engineer deployment.

---

## 7. Tender B (KELTRON EOI) Specific Evaluation

### Detailed Technical Audit across the 10 Core Subsystems:
1. **AI Video Analytics (Intrusion, Loitering, Objects, Fall, Anomaly):**
   - **Status: REQUIRES THIRD-PARTY / DEVELOPMENT (BLUE/ORANGE).**
   - No CV inference models are currently packaged in SARVANETRA. To satisfy this, SARVANETRA must be paired with an AI video analytics worker service running YOLOv8/v10 (intrusion, objects), pose estimation (fall detection), and ByteTrack (loitering).
2. **People Counting & Flow Analytics (Queues, Heatmaps, Dwell Time):**
   - **Status: REQUIRES THIRD-PARTY / DEVELOPMENT (BLUE/ORANGE).**
   - Requires overhead/angled line-crossing counting model. SARVANETRA can easily ingest count events over Kafka and generate heatmaps and throughput charts in the React frontend.
3. **Crowd Intelligence & Density Estimation:**
   - **Status: REQUIRES THIRD-PARTY / DEVELOPMENT (BLUE/ORANGE).**
   - Density estimation (persons/m²) requires a deep learning density map model (CSRNet/DM-Count). Predictive crowd intelligence requires time-series forecasting (Prophet/LSTM) based on historical ingestion data.
4. **Journey Intelligence (Multi-Modal Tracking):**
   - **Status: IMPLEMENTABLE (ORANGE).**
   - Architectural framework exists in SARVANETRA's hierarchical data model. Requires a dedicated correlation engine to link parking entry, turnstile access, and queue progression into a unified visitor journey timeline.
5. **Mobility Management (ANPR & Smart Parking):**
   - **Status: IMPLEMENTABLE (ORANGE).**
   - Vehicle database, watchlist matching, and parking optimization can be built directly into SARVANETRA as a core module, ingesting OCR events from edge ANPR cameras.
6. **Missing Person Identification:**
   - **Status: REQUIRES THIRD-PARTY (BLUE).**
   - Facial recognition requires a specialized biometric pipeline (InsightFace / ArcFace) with a high-dimensional vector search index (Milvus or PostgreSQL `pgvector`).
7. **Drone Surveillance:**
   - **Status: PARTIALLY SATISFIED (YELLOW).**
   - MediaMTX natively accepts RTMP push streams from drone controllers (`rtmp://hub:1935/live/drone_01`). Full mission telemetry and GIS tracking require MAVLink parser integration.
8. **Operational Response & Automated SOPs:**
   - **Status: IMPLEMENTABLE (ORANGE).**
   - Requires an event-driven workflow engine (e.g., Celery/Temporal) triggered by Kafka alerts to dispatch PA announcements, update VMS signs, and notify field officers.
9. **Integrated Command & Control Centre (ICCC) & Common Operating Picture (COP):**
   - **Status: PARTIALLY SATISFIED (YELLOW).**
   - SARVANETRA has a modern React 18 SPA with live grids and audit logs, but lacks the unified GIS Command Dashboard depicted in the tender mockup (p13). Integrating Leaflet/MapLibre will elevate the UI to a full COP.
10. **High Availability, Disaster Recovery & Clustering:**
    - **Status: REQUIRES INFRASTRUCTURE WORK (ORANGE/D).**
    - The software is stateless and containerized, but production deployment requires setting up PostgreSQL Patroni clustering, Kafka multi-broker KRaft, and MinIO distributed clustering.

---

## 8. AI Capability Gap Analysis Matrix

| AI Use Case | In-Camera Edge | LPU Edge AI | Central Server AI | Third-Party OEM | SARVANETRA Current Code | Dev Effort | Tender Compatibility |
|---|---|---|---|---|---|---|---|
| **Simple Motion Detection** | Yes (ONVIF Profile S) | Yes | Yes | Optional | **IMPLEMENTED** (`onvif_motion_producer.py`) | NONE | Full |
| **Perimeter Intrusion** | High-end only | Preferred | Alternative | Available | **NOT IMPLEMENTED** | MEDIUM | Requires CV Model |
| **Line Crossing / Tripwire** | High-end only | Preferred | Alternative | Available | **NOT IMPLEMENTED** | LOW | Requires CV Model |
| **Loitering Detection** | High-end only | Preferred | Alternative | Available | **NOT IMPLEMENTED** | MEDIUM | Requires Tracker + Zone |
| **Abandoned / Missing Object** | Rare | Feasible | Preferred | Available | **NOT IMPLEMENTED** | HIGH | Requires Dual-Time Model |
| **Fall Detection** | No | Feasible | Preferred | Available | **NOT IMPLEMENTED** | HIGH | Requires Pose Estimation |
| **Abnormal Behavior** | No | No | Required | Available | **NOT IMPLEMENTED** | VERY HIGH | Requires Temporal Action Model |
| **ANPR License Plate OCR** | Dedicated ANPR Cam | Preferred (LPU) | Alternative | Highly Recommended | **NOT IMPLEMENTED** | HIGH | Recommend OEM Partner |
| **Vehicle Make / Brand / Color**| Dedicated ANPR Cam | Preferred (LPU) | Alternative | Highly Recommended | **NOT IMPLEMENTED** | MEDIUM | Requires Attribute Model |
| **Helmet & Triple Riding** | Dedicated ITMS Cam | Preferred (LPU) | Alternative | Available | **NOT IMPLEMENTED** | HIGH | Requires Rider Model |
| **People Counting (Line)** | Supported in some | Preferred | Alternative | Available | **NOT IMPLEMENTED** | LOW | Directional Line Model |
| **Crowd Density (persons/m²)**| No | Feasible | Preferred | Available | **NOT IMPLEMENTED** | HIGH | Requires Density Model |
| **Predictive Crowd Build-up** | No | No | Required | Custom Data Science | **NOT IMPLEMENTED** | HIGH | Time-series forecasting |
| **Facial Search / Missing Person**| No | Feature Extract | Vector Match | Highly Recommended | **NOT IMPLEMENTED** | HIGH | InsightFace + pgvector |

---

## 9. Data Model Gap Analysis

To support both tenders, the current PostgreSQL database schema must be extended:

```
EXISTING DATABASE SCHEMA (22 Tables - Alembic 0001–0010)
├── organization, organization_closure, customer, customer_site
├── survapp_user, role, permission, user_role, role_permission, user_session
├── survapp_camera_master, camera_group, camera_group_membership
├── camera_user_access, camera_role_access, camera_status_log
├── survapp_motion_event, survapp_video_segment, backup_clip
├── notification, mobile_device, password_reset_token

REQUIRED EXTENSIONS FOR TENDER COMPLIANCE:
│
├── PARKING MANAGEMENT SYSTEM (Tender A & B)
│   ├── parking_zone (id, site_id, name, total_capacity, current_occupancy, overflow_threshold)
│   ├── parking_lane (id, zone_id, lane_name, lane_type [ENTRY/EXIT], camera_id, is_active)
│   ├── parking_session (id, vehicle_number, zone_id, entry_time, exit_time, slip_id, status)
│   └── parking_slip_transaction (id, session_id, pos_device_id, issued_by_user, print_status)
│
├── ANPR & VEHICLE SURVEILLANCE (Tender A & B)
│   ├── vehicle_transaction (id, camera_id, site_id, plate_number, confidence, vehicle_type,
│   │                        vehicle_make, vehicle_color, speed_kmh, image_s3_key, plate_s3_key,
│   │                        timestamp, is_hotlisted, hotlist_category, is_corrected, corrected_by)
│   └── vehicle_watchlist (id, plate_number, category [WANTED/STOLEN/SUSPICIOUS], notes, created_by)
│
├── ADVANCED AI & CROWD ANALYTICS (Tender B)
│   ├── ai_event (id, camera_id, event_type [INTRUSION/FALL/LOITERING/OBJECT], confidence,
│   │             bounding_box_json, trajectory_json, snapshot_s3_key, timestamp, status)
│   ├── crowd_density_sample (id, camera_id, zone_id, density_per_m2, estimated_headcount, timestamp)
│   └── flow_count_sample (id, camera_id, in_count, out_count, interval_start, interval_end)
│
└── ICCC & INCIDENT MANAGEMENT (Tender B)
    ├── incident (id, incident_type, severity [CRITICAL/HIGH/MEDIUM], title, description,
    │             location_geojson, status [NEW/ASSIGNED/ESCALATED/RESOLVED/CLOSED], assigned_user_id)
    ├── incident_timeline (id, incident_id, user_id, action_taken, comment, timestamp)
    └── sop_action_rule (id, trigger_event, condition_json, action_payload, is_active)
```

---

## 10. API Gap Analysis

| Missing API Endpoint | HTTP Method | Target Subsystem | Purpose | Complexity |
|---|---|---|---|---|
| `/api/v1/parking/zones` | GET, POST, PUT | Parking Module | CRUD for 12 parking grounds, capacity, thresholds | LOW |
| `/api/v1/parking/occupancy` | GET | Parking Module | Live occupancy summary across all zones for dashboards | LOW |
| `/api/v1/parking/entry-slip` | POST | Mobile POS | Handheld POS terminal issues entry slip & records allocation | MEDIUM |
| `/api/v1/parking/exit` | POST | Mobile POS / Gate | Records vehicle exit and frees parking capacity | LOW |
| `/api/v1/anpr/events` | POST | Edge Ingest | Ingests ANPR OCR JSON payload from edge LPU/cameras | LOW |
| `/api/v1/anpr/search` | GET | ANPR Search | Fuzzy plate search (`pg_trgm`), date range, color, make | MEDIUM |
| `/api/v1/anpr/watchlist` | GET, POST, DELETE | Watchlist | Manage stolen/wanted vehicles with instant alerting | LOW |
| `/api/v1/anpr/corrections/{id}`| PUT | ANPR Audit | Manual correction of misread plate with audit log entry | LOW |
| `/api/v1/traffic/analytics` | GET | Traffic Analytics | Volume, hourly trends, pilgrim estimation calculation | MEDIUM |
| `/api/v1/analytics/crowd/density` | GET, POST | Crowd Intelligence | Ingest and query crowd density per m² | LOW |
| `/api/v1/analytics/flow/counts` | GET, POST | Flow Analytics | Ingest and query directional entry/exit counts | LOW |
| `/api/v1/incidents/` | GET, POST, PUT | ICCC Command | Incident ticketing, dispatch, escalation, resolution | MEDIUM |
| `/api/v1/gis/features` | GET | GIS / Map | GeoJSON feature collection of cameras, zones, and alerts | LOW |
| `/api/v1/integrations/phq/export`| GET | State Integration | Stream/metadata export bridge to State Police HQ | MEDIUM |

---

## 11. Security, Privacy & Compliance Evaluation

### 11.1 Technical Security Capabilities in Code:
- **Authentication & RBAC:** PBKDF2/Bcrypt password hashing, JWT perimeter enforcement at Kong, server-side session revocation in PostgreSQL.
- **Hierarchical Access Isolation:** Strict org-closure scoping prevents unauthorized operators from viewing unauthorized district/site cameras.
- **Audit Logging:** Database-backed non-tamperable action tracking in `survapp_audit_log`.

### 11.2 Compliance Dependencies (Outside Application Code):
- **Digital Personal Data Protection Act (DPDP Act, 2023):** Mandates data minimization and privacy by design. Requires automated face/number-plate blurring on non-evidentiary exported video, explicit retention limits, and secure data deletion logs.
- **CERT-In Vulnerability Assessment:** Both tenders mandate certification by a CERT-In empaneled security testing agency before Go-Live. Requires formal penetration testing (VAPT), fixing OWASP Top 10 vulnerabilities, and securing API endpoints.
- **Government Procurement Guidelines (GFR Rule 144(xi)):** Tender A strictly bans equipment and components having country of origin as China or complying with Chinese national surveillance standards (GB28181 / CCC). All physical cameras and switches must be compliant with STQC/BIS-ER and MTCTE guidelines.

---

## 12. Bidder & Commercial Readiness ("NOT SOLVABLE BY CODE")

The following mandatory qualification criteria cannot be resolved by software engineering and mandate bidding as a **Consortium with an experienced Prime Contractor / System Integrator**:

1. **Financial Turnover & Net Worth:**
   - Tender A requires average annual turnover >= ₹10 Crore for the last 3 financial years and a ₹10 Crore Bank Solvency Certificate.
   - Tender B requires average annual turnover >= ₹8 Crore for the last 3 financial years and positive net worth.
2. **Prior Government Experience & Track Record:**
   - Tender A requires past completion of similar PSU/Govt CCTV/VMS projects: 1 contract worth ₹10 Cr, 2 worth ₹5 Cr, or 3 worth ₹3.75 Cr within the last 3 years.
   - Tender B requires AI surveillance / Safe City / TMS project experience worth >= ₹3 Cr and cumulative deployment of >= 100 AI video analytics licenses.
3. **Local State Presence:**
   - Both tenders require an active registered office in Kerala with a valid Kerala GST number.
4. **Corporate Quality Certifications:**
   - ISO 9001:2015 (QMS), ISO 27001:2022 (ISMS), and CMMI Level 3 corporate certifications.
5. **Manufacturer Authorization Forms (MAF):**
   - Formal MAF letters from Camera OEMs, Server OEMs, Switch OEMs, UPS OEMs, and Display OEMs.
6. **Onsite Manpower & 36–60 Month O&M SLA:**
   - Deployment of resident site engineers at Nilakkal during Sabarimala pilgrimage seasons, 24x7 support, and continuous spares management.
