# SARVANETRA — Three-Way Tender Comparison & Common Platform Strategy
**Document Version:** 1.0.0  
**Date:** September 22, 2026  
**Comparative Targets:**  
1. **Tender A:** Kerala Police, Pathanamthitta (GeM Ref: `G1-42272/2025/N`, PAC ₹300 Lakh) — *Nilakkal Pilgrim Parking & CCTV Surveillance*  
2. **Tender B:** KELTRON EOI (Ref: `KSEDC/KEC/PUR/SSG/EOI/003/2026-27`) — *AI Integrated Public Safety, Crowd Management, Mobility Management, and ICCC Platform*  
3. **Current Codebase:** SARVANETRA (Branch `dev`, Commit `8fa82fd`)

---

## 1. Executive Summary

A strategic examination of both tenders reveals that treating them as separate, siloed software projects would be a critical architectural mistake.
- **Tender A (Kerala Police)** is a project-specific deployment requiring an intelligent Parking Management System (PMS) across 12 parking grounds, entry/exit ANPR tracking, CCTV surveillance, an armored OFC ring network, and substation UPS revamps.
- **Tender B (KELTRON EOI)** is an expansive Expression of Interest for an enterprise AI-powered Video Management System (VMS) and Integrated Command & Control Centre (ICCC), encompassing crowd density estimation, flow analytics, journey intelligence, facial recognition, and drone surveillance.

When stripped of their procurement wrappers, **both tenders require the exact same foundational core**:
1. A rock-solid, multi-protocol video ingestion engine (RTSP, RTSPS, RTMP).
2. Low-latency, token-authenticated live streaming (HLS, WebRTC).
3. Automated multi-tier continuous and event-based video chunk recording to S3-compliant object storage with retention lifecycles.
4. A distributed, asynchronous event bus (Apache Kafka) coordinating detections and metadata.
5. Multi-tenant hierarchical access control (State → District/Circle → Site/Zone → Camera) with granular RBAC and non-tamperable audit logs.
6. A centralized command dashboard for live monitoring, alerts, and evidentiary video export.

**SARVANETRA's Current Position:**  
SARVANETRA already implements this exact foundational core to an exceptional standard. However, SARVANETRA is currently a **pure VMS and ingestion fabric**, completely lacking:
- Neural network computer vision models (zero AI/ML inference code in repo).
- Parking management and vehicle transaction data models.
- Interactive GIS mapping in the frontend.
- High Availability (HA) database clustering.

By adopting a **Core Platform + Modular Plugin** architecture, SARVANETRA can serve as the common software engine for both tenders—and future government surveillance bids—without branching or fracturing the codebase.

---

## 2. Tender A Overview (Kerala Police)
- **Tender Inviting Authority:** Office of the District Police Chief, Pathanamthitta, Home Department, Government of Kerala.
- **Location:** Nilakkal, Pampa, and Sannidhanam (Sabarimala pilgrimage base camps).
- **Core Scope:** Supply, installation, and 36-month O&M of an integrated ANPR and AI-based Parking Management System across 12 parking grounds at Nilakkal; 51 IP CCTV cameras (25 PMS fixed, 16 bullet, 10 PTZ); handheld Android POS terminals for entry slip generation; 6-core armored OFC ring network; revamp of 3kVA/6kVA UPS and battery banks at Pampa and Sannidhanam; and modernization of the Nilakkal Control Room.
- **Operational Cadence:** 24x7x365 operation with peak surge during the 3-month annual Mandalam-Makaravilakku festival and monthly pooja days, requiring on-site resident engineers and visual feed shifting between Nilakkal Police Station and Nilakkal Control Room.

---

## 3. Tender B Overview (KELTRON EOI)
- **Tender Inviting Authority:** Kerala State Electronics Development Corporation Limited (KELTRON).
- **Scope:** Selection of an End-to-End Custom Development, Implementation, and Financing Partner for AI-Based Surveillance Projects.
- **Core Scope:** Development and commissioning of an AI Integrated Public Safety, Crowd Management, Mobility Management, and Command & Control Platform (ICCC). Encompasses AI video analytics (intrusion, loitering, fall, objects), crowd density monitoring (heatmaps, risk indices), journey intelligence, ANPR, smart parking, missing person search (facial recognition), drone surveillance, automated SOP execution, PA/VMS signage dispatch, and 5-year SLA support.
- **Statutory & Architecture Mandates:** DPDP Act 2023 compliance, CERT-In empaneled security audit before Go-Live, High Availability (HA) active-active clustering with zero single point of failure, and full source code & intellectual property transfer to KELTRON upon project completion.

---

## 4. Tender A vs. Tender B Requirement Comparison

Every capability is evaluated across both tenders and classified into:
* **COMMON TO BOTH:** Identical or directly compatible functional expectations.
* **TENDER A ONLY:** Specific to Nilakkal Sabarimala site conditions or physical civil/electrical scope.
* **TENDER B ONLY:** Specific to statewide multi-agency public safety, biometrics, or predictive analytics.
* **RELATED BUT DIFFERENT:** Same domain, but different technical depth, scale, or operational objective.
* **NOT COMPARABLE:** Fundamentally distinct administrative or commercial mechanisms.

| Capability | Tender A (Police) | Tender B (KELTRON) | Classification | Engineering Distinction |
|---|---|---|---|---|
| **CCTV / VMS Core** | 51 cameras, live view, 90-day retention, full HD export | Centralized VMS managing all streams, UAVs, and AI events | **COMMON TO BOTH** | Both mandate RTSP/ONVIF ingestion, live streaming, 90-day retention, and evidence export. |
| **Live Streaming** | Control room & police station monitoring, 55" video wall | Common Operating Picture, video wall, multi-grid layout | **COMMON TO BOTH** | Standard low-latency HLS / WebRTC web playback. |
| **Video Recording** | Continuous 24/7 + event-triggered recording, 90-day retention | Intelligent recording, event-based recording, secure storage | **COMMON TO BOTH** | Segment chunking (fMP4) with metadata tagging. |
| **Playback & Timeline** | Timeline search, digital zoom, snapshot export | Video playback, smart search, rapid evidence retrieval | **COMMON TO BOTH** | Multi-channel synchronized timeline playback with presigned URLs. |
| **Evidence Export** | Exportable outside CCTV system for investigation | Evidence export, tamper-evident investigation records | **COMMON TO BOTH** | Cryptographically signed MP4 exports with SHA-256 integrity checksums. |
| **Camera Protocols** | ONVIF Profiles S, G, T, M; RTSP / RTP / RTCP | Open standards, open APIs, ONVIF Profile compliance | **COMMON TO BOTH** | Universal camera protocol support. |
| **ANPR / Number Plates** | 230 km/h speed OCR, 90–95% accuracy, LPU edge inference | Vehicle identification, tracking, entry/exit monitoring | **RELATED BUT DIFFERENT** | Tender A requires formal ARAI speed certification; Tender B expects ANPR as part of city-wide mobility intelligence. |
| **Vehicle Classification** | LMV, HMV, Cars, Bikes, 2/3 Wheelers | Vehicle classification, pedestrian vs vehicle tracking | **COMMON TO BOTH** | Multi-class object detection CNN. |
| **Vehicle Make / Color** | Detect make/brand and color during daytime | Not explicitly listed in text (vehicle tracking emphasized) | **TENDER A ONLY** | Secondary attribute classification head required for Tender A. |
| **Watchlist / Hotlist** | "Wanted", "Suspicious", "Stolen" (<2-3s alert) | Blacklist and whitelist vehicle management | **COMMON TO BOTH** | Database watchlist table with instant Kafka stream alerting. |
| **Parking Management** | 12 specific zones, dynamic allocation, POS slip print | Smart parking, occupancy, overflow detection, guidance | **RELATED BUT DIFFERENT** | Tender A requires physical lane allocation & POS thermal printing; Tender B requires general city parking analytics. |
| **Parking Occupancy** | Real-time zone-wise vacancy calculation and CCR display | Real-time occupancy monitoring and availability metrics | **COMMON TO BOTH** | Shared occupancy state engine: Inflow - Outflow = Occupancy. |
| **Parking Allocation** | Automated dynamic ground allocation upon vehicle entry | Vehicle guidance and parking optimization | **RELATED BUT DIFFERENT** | Tender A has deterministic allocation logic; Tender B has general guidance. |
| **POS Slip Generation** | Handheld Android POS terminal printing 58mm thermal slips | None (not required) | **TENDER A ONLY** | External hardware bridge module for Android POS devices. |
| **People Counting** | Indirect estimation via vehicle passenger capacity multiplier | Direct AI video line-crossing entry/exit counting | **RELATED BUT DIFFERENT** | Tender A calculates pilgrim count mathematically; Tender B measures actual footfalls with computer vision. |
| **Queue Analytics** | None | Queue length estimation, wait-time progression analysis | **TENDER B ONLY** | Computer vision spatial bounding-box queue clustering. |
| **Crowd Density** | None | Continuous density (persons/m²), congestion alerts | **TENDER B ONLY** | Deep learning crowd density regression models (CSRNet/DM-Count). |
| **Heat Maps** | Camera-native heat map noted in camera specs | Spatial flow visualization and crowd density heatmaps | **RELATED BUT DIFFERENT** | Tender A relies on camera-native analytics; Tender B requires centralized platform-generated heatmaps. |
| **Traffic Analytics** | Peak-hour trends, daily/monthly reports, pilgrim trends | Traffic analytics, congestion optimization, transit sync | **COMMON TO BOTH** | Time-series traffic aggregation and reporting. |
| **Predictive Analytics** | Basic peak-hour prediction from historical trends | Predictive crowd build-up, queue forecasting, demand | **RELATED BUT DIFFERENT** | Tender A uses historical curve fitting; Tender B expects ML time-series forecasting (Prophet/LSTM). |
| **Missing Persons / Face**| None | Face-based search, camera correlation, last-seen location | **TENDER B ONLY** | Biometric facial recognition and high-dimensional vector search. |
| **AI Video Analytics** | Camera-native intrusion, tripwire, loitering, scene tamper| Server/Edge AI intrusion, fall, abnormal behavior, objects | **RELATED BUT DIFFERENT** | Tender A specifies in-camera analytics; Tender B mandates platform-level server/edge AI inference. |
| **Incident Management** | Basic fault reporting and alarm logs | Full incident lifecycle (New, Assigned, Escalated, Closed)| **TENDER B ONLY** | Ticketing state machine, workflow automation, and SLA tracking. |
| **Alerts & Notifications**| Control room alarms, email, push notification | Real-time multi-channel alerts, SOP action triggers | **COMMON TO BOTH** | Real-time event notifications via WebSockets, Kafka, and webhooks. |
| **GIS / Mapping** | Basic display of alarms on third-party maps (Google) | Deep GIS integration, Common Operating Picture overlay | **RELATED BUT DIFFERENT** | Tender A requires simple map pins; Tender B requires interactive GIS layers (cameras, drones, heatmaps). |
| **Command Centre (ICCC)** | Nilakkal Control Room modernization (monitors, client PCs)| Statewide ICCC platform uniting CCTV, AI, UAV, PA, IoT | **RELATED BUT DIFFERENT** | Tender A is a physical control room fit-out; Tender B is an executive enterprise software platform. |
| **Public Address (PA)** | IP announcing touch console + 5x 30W IP horn speakers | Public announcement integration for crowd regulation | **COMMON TO BOTH** | Audio dispatch integration (SIP/VoIP bridge to IP speakers). |
| **Variable Message Signs** | None | VMS and digital signage automated message dispatch | **TENDER B ONLY** | NTCIP / TCP display protocol integration. |
| **Drone Surveillance** | None | Live UAV streaming, telemetry, GIS overlay, missions | **TENDER B ONLY** | MediaMTX RTMP ingestion + MAVLink telemetry parser. |
| **IoT Sensor Integration** | Future bay-by-bay sensors mentioned | IoT sensor data ingestion and event correlation | **COMMON TO BOTH** | MQTT / HTTP telemetry ingestion pipeline. |
| **Mobile Application** | Handheld Android POS terminal for parking slips | Mobile app for field responders and decision-makers | **RELATED BUT DIFFERENT** | Tender A needs a rugged POS slip app; Tender B needs an officer situational awareness app. |
| **Reporting & Export** | Daily, weekly, monthly traffic and audit reports | Advanced operational analytics, CSV/PDF reports | **COMMON TO BOTH** | Relational SQL aggregation and reporting services. |
| **Audit Logging** | Non-tamperable user login and plate correction audit | Comprehensive non-tamperable audit logs across actions | **COMMON TO BOTH** | Immutable append-only audit trail schema. |
| **RBAC & Multi-Tenancy** | Role-based + location-based access (State->Dist->Site) | Role-based access control, privacy, and user scoping | **COMMON TO BOTH** | Hierarchical organizational tenancy and granular permission sets. |
| **APIs & Interoperability**| State Police PHQ Trivandrum & Pathanamthitta sync | Open standards, open REST/WebSocket APIs, modularity | **COMMON TO BOTH** | OpenAPI 3.0 documented microservice architecture. |
| **High Availability (HA)** | Redundant switch ring, N+1 core switch, UPS backup | Active-Active clustering, zero single point of failure | **RELATED BUT DIFFERENT** | Tender A focuses on network/electrical HA; Tender B focuses on software & database clustering. |
| **Disaster Recovery (DR)**| LPU 7-day edge retention during network disconnect | Automated failover, database replication, multi-site DR | **COMMON TO BOTH** | Edge-autonomous buffering + central database replication. |
| **Cloud / On-Prem / Hybrid**| Dedicated on-prem servers at Nilakkal Control Room | Cloud, on-premises, or hybrid deployment models | **COMMON TO BOTH** | Containerized microservice deployment (Docker / K8s). |
| **Cybersecurity & Hardening**| Disabled Telnet, TPM 2.0 chipset, secure boot | OWASP Top 10, encryption in transit/rest, secure SDLC | **COMMON TO BOTH** | TLS 1.3, API rate limiting, perimeter JWT, container hardening. |
| **Privacy & Regulations** | Tamper-proof date/time watermarks | Digital Personal Data Protection Act 2023 (DPDP Act) | **RELATED BUT DIFFERENT** | Tender B strictly enforces statutory PII privacy and consent rules. |
| **Security Certification** | CERT-In empaneled agency vulnerability certificate | Third-party CERT-In security audit before Go-Live | **COMMON TO BOTH** | Formal VAPT audit and closure certification. |
| **Source Code / IP** | Standard Government procurement terms | Complete source code and IP rights transferred to buyer | **TENDER B ONLY** | Mandatory contractual handover of custom source code. |
| **Warranty & SLA** | 36 months comprehensive onsite warranty; 24hr MTTR | 5 years comprehensive warranty, SLA, and maintenance | **RELATED BUT DIFFERENT** | 3-year vs. 5-year support term. |
| **Civil Works & Trenching**| 33 poles, 1 gantry, trenching, barricades, conduits | None (Software & integration focus) | **TENDER A ONLY** | Physical civil contracting. |
| **Optical Fiber Network** | 6-core/12-core/24-core armored OFC ring network | None (Uses existing/provided network) | **TENDER A ONLY** | Physical fiber optic infrastructure. |
| **Power & Substation UPS** | 3kVA/6kVA online UPS + battery bank revamp | Standard server room UPS | **TENDER A ONLY** | Physical electrical revamp. |

---

## 5. Common Requirements (The Shared Platform Foundation)

Across both tenders, the following core software capabilities are **100% common**:
1. **Multi-Protocol Video Ingest & Management:** RTSP, RTSPS, and RTMP ingestion with ONVIF camera discovery and dynamic stream authentication.
2. **Low-Latency Streaming:** Delivering smooth live feeds to browser-based control room workstations via fMP4 HLS and WebRTC.
3. **Multi-Tier Recording & S3 Storage:** 60-second video slicing, upload verification, JSON sidecar generation, and automated retention cleaning.
4. **Hierarchical Multi-Tenancy & Scoped RBAC:** Multi-level administrative hierarchy (State → District → Site → Camera) with location-scoped access.
5. **Vehicle Transaction Processing:** Ingesting license plate strings, snapshots, timestamps, and vehicle classification into relational SQL storage.
6. **Watchlist / Hotlist Matching:** Real-time checking of detected plates against hotlists with sub-2-second alert generation.
7. **Audit Trails & Tamper Resistance:** Immutable logging of logins, stream views, record exports, and manual edits.
8. **Asynchronous Event Bus:** Kafka-backed event coordination decoupling high-throughput detections from database persistence.
9. **Cybersecurity Hardening:** TLS 1.3 encryption, perimeter API gateway protection, OWASP alignment, and CERT-In audit readiness.

---

## 6. Tender-Specific Requirements

### 6.1 Tender A Only (Nilakkal Sabarimala Specifics)
- **12 Designated Parking Grounds:** Hardcoded physical site layout at Nilakkal.
- **Handheld Android POS Integration:** Driving field POS thermal printers to issue physical paper parking slips to vehicle drivers.
- **ARAI 230 km/h ANPR Certification:** Formal automotive research association certificate for speed enforcement.
- **Physical Civil & Electrical Infrastructure:** 33 poles, 1 cantilever gantry, STAAD PRO civil calculations, HDPE trenching, 6-core armored OFC ring, and 3kVA/6kVA substation UPS revamp at Pampa and Sannidhanam.
- **Seasonal Operations:** Shifting camera visual monitoring from Nilakkal Police Station to Nilakkal Control Room during Mandalam-Makaravilakku festival.

### 6.2 Tender B Only (KELTRON Enterprise / ICCC Specifics)
- **Advanced AI Computer Vision:** Fall detection, abandoned object segmentation, abnormal behavior recognition, and loitering analysis.
- **Crowd Intelligence:** Persons/m² density estimation, dynamic heatmaps, and ML predictive congestion forecasting.
- **Biometric Face Search:** Missing person gallery matching and multi-camera re-identification (Re-ID).
- **Interactive GIS Common Operating Picture (COP):** Unified multi-layer map dashboard integrating cameras, drones, IoT, and alerts.
- **Drone Surveillance & Mission Tracking:** Live RTMP drone video ingest paired with MAVLink aerial telemetry.
- **Incident Lifecycle Workflow:** End-to-end incident dispatch, SLA escalation, and multi-agency coordination.
- **Statutory DPDP Act Compliance & Full IP Transfer:** Automatic PII blurring/redaction and legal handover of source code to KELTRON.

---

## 7. Common Platform Architecture (The Reusable Core)

To satisfy both tenders, SARVANETRA must be modularized into four functional tiers:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    SARVANETRA COMMON PLATFORM ARCHITECTURE                 │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  [ TIER 1: CORE REUSABLE PLATFORM (CORE COMMON) ]                          │
│  ├── 1. Video Ingestion & Path Registry (MediaMTX REST Client)             │
│  ├── 2. Live Media Proxy (Nginx fMP4 HLS & WebRTC Relay)                   │
│  ├── 3. Continuous & Sliced Recording Pipeline (60s Chunks + MinIO S3)     │
│  ├── 4. Asynchronous Event Bus (Apache Kafka KRaft Message Bus)            │
│  ├── 5. Hierarchical Multi-Tenancy (State -> District -> Site -> Camera)   │
│  ├── 6. Granular RBAC & User Session Management (FastAPI + PostgreSQL)     │
│  ├── 7. Immutable Audit Engine (Tamper-evident activity logs)              │
│  ├── 8. Perimeter API Gateway (Kong Gateway JWT & Site Token Router)       │
│  ├── 9. Base Web SPA Console (React 18 / Vite / Tailwind Multi-Grid Wall)  │
│  └── 10. Edge NVR Appliance Stack (7-loop agent + offline SQLite buffer)   │
│                                                                            │
│  [ TIER 2: SPECIALIZED DOMAIN ENGINES (PLUGINS) ]                          │
│  ├── 11. ANPR Management Plane [CORE COMMON] (Watchlists, Search, Alerts)  │
│  ├── 12. Parking Management Engine [PROJECT-SPECIFIC] (Occupancy, Zones)   │
│  ├── 13. ICCC & GIS Map Engine [CORE COMMON] (COP Single Pane, Incidents)  │
│  └── 14. Evidence Packaging Engine [CORE COMMON] (Signed MP4 + Checksums)  │
│                                                                            │
│  [ TIER 3: THIRD-PARTY INTEGRATION CONNECTORS (OPTIONAL / ADAPTERS) ]      │
│  ├── 15. Android POS Slip Printer Bridge [TENDER A ONLY]                   │
│  ├── 16. External AI Inference Ingest Adapter (DeepStream / YOLO / TensorRT)│
│  ├── 17. Biometric Face Search & Vector Adapter [TENDER B ONLY]            │
│  ├── 18. Drone RTMP & MAVLink Telemetry Adapter [TENDER B ONLY]            │
│  ├── 19. IP Public Address (SIP) & VMS Signage Connector                   │
│  └── 20. State Police HQ Stream & Data Bridge                              │
│                                                                            │
│  [ TIER 4: INFRASTRUCTURE & PHYSICAL DEPLOYMENT ]                          │
│  ├── 21. High Availability Clustering (Patroni Postgres, Kafka KRaft x3)  │
│  └── 22. Turnkey Field Hardware (Cameras, Switches, OFC, UPS, Poles) [OEM] │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Current SARVANETRA Position (What System Is It Today?)

Based strictly on the actual codebase in `/opt/surv-learn`:

### Primary Identification:
SARVANETRA is currently a **High-Performance Video Ingestion, Live Streaming, and Multi-Tier Recording Platform with Hierarchical Access Control**.

### What It IS:
- **A Very Capable VMS Core:** Ingests RTSP/RTMP, slices 60s fMP4 video, uploads to MinIO S3 with JSON metadata sidecars, coordinates via Kafka, and serves low-latency HLS streams to a clean React 18 web UI.
- **A Robust Multi-Tenant Control Plane:** Implements recursive organizational hierarchy indexing via closure tables ([`surv/app/models/organization.py`](file:///opt/surv-learn/surv/app/models/organization.py)) with strict camera visibility enforcement ([`surv/app/services/access_service.py`](file:///opt/surv-learn/surv/app/services/access_service.py)).
- **A Resilient Edge Appliance Fabric:** Operates a complete Edge NVR stack with local SQLite queuing and automated synchronization loops ([`edge-nvr/edge-agent/main.py`](file:///opt/surv-learn/edge-nvr/edge-agent/main.py)).

### What It IS NOT:
- **It is NOT an AI Video Analytics Platform:** It contains zero machine learning models, zero computer vision inference pipelines, zero weights, and zero OCR logic.
- **It is NOT a Parking Management System:** It has no data models or logic for parking grounds, lanes, occupancy counters, or POS slips.
- **It is NOT an ICCC Common Operating Picture:** It has no interactive GIS mapping component, no incident management ticketing, and no situational command layout.

---

## 9. SARVANETRA vs. Common Requirements

| Common Capability | Current Code Status | Source File Evidence | Identified Gap | Required Work |
|---|---|---|---|---|
| **RTSP / RTSPS Ingest** | **CURRENTLY IMPLEMENTED** | [`surv/app/services/mediamtx_client.py#L36-L67`](file:///opt/surv-learn/surv/app/services/mediamtx_client.py#L36-L67) | None | Production testing with physical cameras |
| **Low-Latency Streaming** | **CURRENTLY IMPLEMENTED** | [`surv/nginx/conf.d/hls.conf`](file:///opt/surv-learn/surv/nginx/conf.d/hls.conf), [`frontend/HLSPlayer.tsx`](file:///opt/surv-learn/surv/frontend/src/components/HLSPlayer.tsx) | Direct port 8080 bypasses Kong | Optional: route HLS through Kong |
| **S3 Video Recording** | **CURRENTLY IMPLEMENTED** | [`surv/workers/upload_to_minio.py`](file:///opt/surv-learn/surv/workers/upload_to_minio.py), [`surv/mediamtx/mediamtx.yml`](file:///opt/surv-learn/surv/mediamtx/mediamtx.yml) | None | Size physical S3 disks for 90 days |
| **Kafka Event Bus** | **CURRENTLY IMPLEMENTED** | [`surv/docker-compose.yml#L107-L135`](file:///opt/surv-learn/surv/docker-compose.yml#L107-L135) | Single-node KRaft broker | Scale to 3-node broker cluster for HA |
| **Camera Health Monitor** | **CURRENTLY IMPLEMENTED** | [`surv/workers/status_monitor.py`](file:///opt/surv-learn/surv/workers/status_monitor.py), [`surv/workers/notifier.py`](file:///opt/surv-learn/surv/workers/notifier.py) | Needs UI notification toaster | Add toast popups in web SPA |
| **Hierarchical Multi-Tenancy**| **CURRENTLY IMPLEMENTED** | [`surv/app/models/organization.py`](file:///opt/surv-learn/surv/app/models/organization.py), [`surv/app/services/access_service.py`](file:///opt/surv-learn/surv/app/services/access_service.py) | None | Fully satisfies multi-layer scoping |
| **Granular RBAC & Audit** | **CURRENTLY IMPLEMENTED** | [`surv/app/models/role.py`](file:///opt/surv-learn/surv/app/models/role.py), [`surv/app/models/audit.py`](file:///opt/surv-learn/surv/app/models/audit.py) | None | Fully satisfies non-tamperable audit |
| **ANPR Ingestion & Storage** | **NOT IMPLEMENTED** | None | No vehicle transaction table or API | Add `anpr_transaction` schema & API |
| **Watchlist / Alert Matching**| **ARCHITECTURALLY PRESENT** | [`surv/app/models/motion.py`](file:///opt/surv-learn/surv/app/models/motion.py), Kafka topics | Alert pipeline exists, no plate table | Add `vehicle_watchlist` table & matcher |
| **Parking Occupancy Engine** | **ARCHITECTURALLY PRESENT** | [`surv/app/models/organization.py`](file:///opt/surv-learn/surv/app/models/organization.py) | Sites exist, no parking zone logic | Build `parking_zone` model & counter logic |
| **GIS Map Common Operating Pic**| **NOT IMPLEMENTED** | None | Lat/Long in DB, no map in UI | Integrate Leaflet / MapLibre in React SPA |
| **Incident Management Ticketing**| **NOT IMPLEMENTED** | None | No incident state machine in DB | Add `incident` model and workflow API |
| **AI Computer Vision Inference**| **NOT IMPLEMENTED** | None | Zero ML models or inference services | Integrate external AI worker service |
| **High Availability Clustering** | **ARCHITECTURALLY PRESENT** | Docker Compose single nodes | No streaming replication / failover | Deploy Patroni PostgreSQL HA cluster |

---

## 10. Build vs. Integrate (Architectural Boundaries)

To maximize code reuse while remaining compliant with government certifications, SARVANETRA must enforce clear architectural boundaries:

| Capability | Strategy | Rationale & Architectural Responsibility |
|---|---|---|
| **VMS Ingestion & Streaming** | **BUILD & OWN** | SARVANETRA core competence. Fully controlled via MediaMTX, Nginx, and FastAPI. |
| **S3 Storage & Retention** | **BUILD & OWN** | Chunking, JSON sidecars, Kafka dispatch, and minio cleaner retention are fully owned. |
| **ANPR Event Management** | **BUILD & OWN** | Transaction schemas, plate search, watchlist matching, and control room alerts owned by SARVANETRA. |
| **ANPR OCR / Inference Engine**| **INTEGRATE** | ARAI 230 km/h certification mandates partnering with a certified Indian ANPR OEM (Vehant/Videonetics). |
| **Parking Occupancy & Allocation**| **BUILD & OWN** | Zone calculation, occupancy delta, and dynamic advice engine built directly in SARVANETRA. |
| **Handheld Android POS Printer** | **INTEGRATE** | Hardware POS device with thermal printer. Build lightweight Android bridge APK connecting to SARVANETRA API. |
| **GIS Map Visualization (COP)** | **BUILD & OWN** | Embed Leaflet / MapLibre directly into React SPA; consume standard GeoJSON from SARVANETRA API. |
| **Incident Management & SOPs** | **BUILD & OWN** | Incident schemas, state transitions, dispatching, and audit logging built natively in SARVANETRA. |
| **Advanced AI Analytics (Crowd/Pose)**| **INTEGRATE** | Computer vision inference (YOLO/CSRNet) should run in decoupled microservice workers pushing to Kafka. |
| **Drone Video & Telemetry** | **ORCHESTRATE** | RTMP video ingested natively via MediaMTX; MAVLink flight coordinates parsed and displayed on GIS map. |
| **Public Address & VMS Signage** | **ORCHESTRATE** | SARVANETRA triggers alerts; dispatches commands to external PA/VMS controllers via SIP/TCP. |
| **Physical Cameras & Switches** | **LEAVE TO OEM** | Procurement of STQC/BIS-ER cameras and MTCTE switches handled by Consortium SI. |
| **Civil Infrastructure & UPS** | **LEAVE TO OEM** | Poles, gantries, OFC ring trenching, and substation UPS revamp executed by Prime Contractor. |

---

## 11. Architecture Gaps & Remediation

```
┌────────────────────────┬─────────────────────────────┬─────────────────────────────┬────────────┐
│ Subsystem Gap          │ Current State               │ Required State              │ Difficulty │
├────────────────────────┼─────────────────────────────┼─────────────────────────────┼────────────┤
│ A. Video Platform      │ Static snapshot env var;    │ Dynamic DB camera querying; │ LOW        │
│                        │ missing kcat in MediaMTX    │ kcat installed in image     │            │
│ B. AI / Analytics      │ Only ONVIF motion polling   │ Decoupled Python/C++ CV     │ HIGH       │
│                        │ exists                      │ workers emitting to Kafka   │            │
│ C. Event Architecture  │ 3 Kafka topics; no status   │ Full event taxonomy:        │ MEDIUM     │
│                        │ consumer worker             │ camera, vehicle, crowd, alert│           │
│ D. ANPR                │ Absent                      │ anpr_transaction schema,    │ MEDIUM     │
│                        │                             │ pg_trgm fuzzy search, alert │            │
│ E. Parking Management  │ Absent                      │ parking_zone model, live    │ MEDIUM     │
│                        │                             │ occupancy accumulator, API  │            │
│ F. Investigation       │ Segments downloadable via   │ Tamper-evident ZIP bundle   │ MEDIUM     │
│                        │ presigned S3 URLs           │ with SHA-256 manifest & watermark│       │
│ G. ICCC / COP          │ Separate list/grid pages    │ Single-pane executive COP   │ MEDIUM     │
│                        │                             │ uniting GIS, video, alerts  │            │
│ H. GIS Mapping         │ Lat/Long stored in DB only  │ Interactive Leaflet map with│ MEDIUM     │
│                        │                             │ GeoJSON camera/zone layers  │            │
│ I. Third-Party Integr. │ Mobile endpoints return 501;│ Handheld POS bridge, PA SIP │ HIGH       │
│                        │ no POS/PA/VMS connectors    │ audio, State PHQ feed       │            │
│ J. Security Hardening  │ Solid JWT baseline; lacks   │ Automated SAST/DAST in CI;  │ HIGH       │
│                        │ formal CERT-In audit        │ DPDP Act consent/redaction  │            │
│ K. HA / Clustering     │ Single-node Docker Compose  │ Patroni Postgres 3-node;    │ HIGH       │
│                        │ containers                  │ Kafka KRaft x3; MinIO Dist. │            │
│ L. Reporting           │ Basic audit logs in DB      │ Automated daily/monthly PDF │ LOW        │
│                        │                             │ and CSV traffic reports     │            │
│ M. Operations / O&M    │ Manual peer management in   │ Automated telemetry alerts, │ MEDIUM     │
│                        │ Headscale VPN               │ remote firmware/config push │            │
└────────────────────────┴─────────────────────────────┴─────────────────────────────┴────────────┘
```

---

## 12. Data Model Implications

To maintain a single unified codebase across both tenders, extend the PostgreSQL schema via a new Alembic migration:

```sql
-- 1. Parking Management Extension (Tenders A & B)
CREATE TABLE parking_zone (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID NOT NULL REFERENCES customer_site(id),
    zone_code VARCHAR(32) NOT NULL, -- 'ZONE_01' to 'ZONE_12'
    zone_name VARCHAR(128) NOT NULL,
    total_capacity INTEGER NOT NULL DEFAULT 0,
    current_occupancy INTEGER NOT NULL DEFAULT 0,
    overflow_threshold INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE parking_session (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_id UUID NOT NULL REFERENCES parking_zone(id),
    vehicle_number VARCHAR(32) NOT NULL,
    vehicle_type VARCHAR(32) NOT NULL, -- LMV, HMV, BUS, 2W
    entry_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    exit_time TIMESTAMPTZ,
    entry_slip_id VARCHAR(64),
    pos_terminal_id VARCHAR(64),
    status VARCHAR(32) DEFAULT 'PARKED' -- PARKED, EXITED, OVERSTAY
);

-- 2. ANPR & Vehicle Surveillance Extension (Tenders A & B)
CREATE TABLE anpr_transaction (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID NOT NULL REFERENCES survapp_camera_master(id),
    site_id UUID NOT NULL REFERENCES customer_site(id),
    plate_number VARCHAR(32) NOT NULL,
    confidence NUMERIC(5,2) NOT NULL,
    vehicle_type VARCHAR(32),
    vehicle_make VARCHAR(64),
    vehicle_color VARCHAR(32),
    speed_kmh NUMERIC(5,2),
    image_s3_key VARCHAR(255),
    plate_s3_key VARCHAR(255),
    direction VARCHAR(16), -- ENTRY, EXIT
    timestamp TIMESTAMPTZ NOT NULL,
    is_hotlisted BOOLEAN DEFAULT FALSE,
    hotlist_category VARCHAR(64),
    is_corrected BOOLEAN DEFAULT FALSE,
    corrected_plate VARCHAR(32),
    corrected_by_user_id UUID REFERENCES survapp_user(id)
);

CREATE INDEX idx_anpr_plate_trgm ON anpr_transaction USING gin (plate_number gin_trgm_ops);
CREATE INDEX idx_anpr_timestamp ON anpr_transaction(timestamp DESC);

CREATE TABLE vehicle_watchlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plate_number VARCHAR(32) UNIQUE NOT NULL,
    category VARCHAR(64) NOT NULL, -- WANTED, STOLEN, SUSPICIOUS
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Incident Lifecycle Extension (Tender B)
CREATE TABLE incident (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_type VARCHAR(64) NOT NULL, -- CONGESTION, INTRUSION, THEFT, FIRE
    severity VARCHAR(16) NOT NULL, -- CRITICAL, HIGH, MEDIUM, LOW
    title VARCHAR(255) NOT NULL,
    description TEXT,
    site_id UUID REFERENCES customer_site(id),
    camera_id UUID REFERENCES survapp_camera_master(id),
    latitude NUMERIC(10,7),
    longitude NUMERIC(10,7),
    status VARCHAR(32) DEFAULT 'NEW', -- NEW, ASSIGNED, ESCALATED, RESOLVED, CLOSED
    assigned_user_id UUID REFERENCES survapp_user(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 13. API Implications

The following clean REST endpoints must be added to [`surv/app/routers/`](file:///opt/surv-learn/surv/app/routers/):

```
PARKING & OCCUPANCY ROUTER (/api/v1/parking)
  ├── GET    /zones                  -> List 12 zones with live capacity & occupancy
  ├── GET    /occupancy              -> Aggregate occupancy summary across Nilakkal
  ├── POST   /entry-slip             -> Handheld POS issues slip & records entry
  └── POST   /exit                   -> Records vehicle departure and updates count

ANPR & VEHICLE ROUTER (/api/v1/anpr)
  ├── POST   /events                 -> Ingests OCR payload from edge LPU/cameras
  ├── GET    /search                 -> Trigram fuzzy search (edit distance <= 2)
  ├── GET    /watchlist              -> List and filter hotlisted plates
  ├── POST   /watchlist              -> Add plate to hotlist with instant Kafka sync
  └── PUT    /corrections/{id}       -> Correct misread plate and record audit trail

ICCC & COMMAND ROUTER (/api/v1/iccc)
  ├── GET    /cop-summary            -> Single-call payload for Common Operating Picture
  ├── GET    /incidents              -> List active incidents with status and SLA timer
  ├── POST   /incidents              -> Create incident manually or from AI alert
  ├── PUT    /incidents/{id}/status  -> Transition incident state (Assigned -> Closed)
  └── GET    /gis/layers             -> GeoJSON feature collection of cameras & zones
```

---

## 14. AI & Analytics Implications

```
                     AI INFERENCE DEPLOYMENT TOPOLOGY

┌─────────────────────────┐   RTSP Feed    ┌───────────────────────────────────┐
│ IP Surveillance Cameras ├───────────────►│ Edge LPU (Industrial PC)          │
│ (Fixed, Bullet, PTZ)    │                │ - TensorRT / DeepStream Pipeline  │
└─────────────────────────┘                │ - ANPR License Plate OCR Model    │
                                           │ - Vehicle Classifier & Color CNN  │
                                           └─────────────────┬─────────────────┘
                                                             │ JSON Detection Events
                                                             ▼ (Encrypted HTTPS)
┌─────────────────────────┐   RTMP Feed    ┌───────────────────────────────────┐
│ Drone / PTZ Video Feeds ├───────────────►│ Central GPU AI Inference Server   │
│ (Aerial, Wide Angle)    │                │ - Crowd Density Model (CSRNet)    │
└─────────────────────────┘                │ - Human Pose / Fall Detection     │
                                           │ - Line Crossing Flow Counter      │
                                           └─────────────────┬─────────────────┘
                                                             │ JSON Analytics Events
                                                             ▼ (Port 9092)
┌──────────────────────────────────────────────────────────────────────────────┐
│                       APACHE KAFKA DISTRIBUTED EVENT BUS                     │
│  Topics: camera.motion, vehicle.anpr, crowd.density, flow.count, ai.alert    │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                                       ▼ Asynchronous Consumption
┌──────────────────────────────────────────────────────────────────────────────┐
│                    SARVANETRA HUB BACKEND & DATABASE                         │
│  - Segment DB Consumer: Tags video segments (full / motion / guard)          │
│  - Watchlist Alert Matcher: Matches plates against stolen database (<2s)    │
│  - Occupancy Aggregator: Updates zone capacity in PostgreSQL                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 15. ICCC Implications (Common Operating Picture)

Tender B (Page 13) provides a detailed mock-up of the required Command Centre dashboard. SARVANETRA's frontend must evolve from separate tabular pages into a **Unified Executive Common Operating Picture (COP)**:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│  SARVANETRA ICCC — COMMON OPERATING PICTURE (COP)                             [Malayalam | English]│
├─────────────────────────┬──────────────────────────────────────────┬─────────────────────────────┤
│ METRICS BAR             │ INTERACTIVE GIS MAP (MapLibre / Leaflet) │ ACTIVE INCIDENTS (SLA)      │
│ Total Pilgrims: 23,562  │                                          │ [CRITICAL] Crowd Surge Z4   │
│ Vehicles Inside: 2,356  │   [Pin: Cam 12 (UP)]                     │   Time: 14:32 | Assigned: P1│
│ Nilakkal Occupancy: 68% │   [Zone 1: 85% Full (Amber)]             │ [HIGH] Stolen Vehicle Match │
│ Cameras Online: 48/51   │   [Zone 4: 95% Full (Red)]               │   KL-07-CD-1234 (Zone 2)    │
│ Active Incidents: 3     │   [UAV Icon: Drone 01 Live Stream]       │ [MEDIUM] OFC Ring Link B Cut│
├─────────────────────────┼──────────────────────────────────────────┼─────────────────────────────┤
│ VIDEO WALL (4x GRID)    │ 12-ZONE PARKING OCCUPANCY BARS           │ REAL-TIME ALERT STREAM      │
│ [Live: Main Entry ANPR] │ Z1: ████████░░ 82% (Direct to Z3)        │ 14:35:12 Hotlist Match      │
│ [Live: Parking Ground 2]│ Z2: ██████████ 100% [FULL]               │ 14:34:50 Queue Overflow Gate│
│ [Live: Pampa Footbridge]│ Z3: ████░░░░░░ 42% [OPEN]                │ 14:33:10 Cam 08 Disconnect  │
│ [Live: Sannidhanam Walk]│ Z4: █████████░ 91% [NEAR FULL]           │ 14:31:05 Fall Detected Z1   │
└─────────────────────────┴──────────────────────────────────────────┴─────────────────────────────┘
```

---

## 16. Security, Compliance & Regulatory Implications

1. **Digital Personal Data Protection Act (DPDP Act, 2023):**
   - Must implement automated face and license plate blurring for exported video clips unless requested specifically under a police evidentiary warrant.
   - Enforce explicit automated retention limits (90 days for CCTV/ANPR; 7 days for local edge buffers).
2. **CERT-In Vulnerability Assessment Certification:**
   - Pre-condition for Go-Live across both tenders.
   - Mandates closing all OWASP Top 10 vulnerabilities, removing default credentials, enabling strict TLS 1.3, and completing formal third-party penetration testing.
3. **Public Procurement (Preference to Make in India) & GFR Rule 144(xi):**
   - Tender A explicitly prohibits products of Chinese origin and non-compliance with Chinese national surveillance standards (GB28181 / CCC).
   - Camera models proposed must have authentic STQC / BIS-ER certificates. Switches must have MTCTE certificates.

---

## 17. Reusable Core vs. Project-Specific Modules

```
┌────────────────────────────────────────────────────────────────────────────┐
│ 1. REUSABLE CORE PLATFORM (Ship in every deployment)                       │
│    - MediaMTX Ingestion, HLS Proxy, MinIO Storage, S3 Retention Cleaner    │
│    - Kafka KRaft Event Hub, PostgreSQL 16 Data Models, Alembic Migrations  │
│    - Multi-Tenant Org Closure Tree, Granular RBAC, Audit Logging           │
│    - Kong Perimeter Gateway, Web SPA Framework, Video Wall Playback        │
├────────────────────────────────────────────────────────────────────────────┤
│ 2. REUSABLE DOMAIN PLUGINS (Configured via feature flags)                  │
│    - ANPR Management Engine (Plate transactions, watchlists, fuzzy search) │
│    - Parking Management Engine (Zone capacity, entry/exit counters)        │
│    - ICCC Common Operating Picture (GIS map, incident ticketing drawer)    │
│    - Evidence Packaging Engine (Signed MP4, SHA-256 integrity manifest)    │
├────────────────────────────────────────────────────────────────────────────┤
│ 3. INTEGRATION ADAPTER CONNECTORS (Loaded as external microservices)       │
│    - Handheld Android POS Printer Bridge (Tender A)                        │
│    - ARAI-Certified Edge ANPR OCR Ingest Pipeline (Tender A)               │
│    - Central Deep Learning Computer Vision Worker (Tender B)               │
│    - Biometric Face Vector Search Bridge (Tender B)                        │
│    - IP Public Address (SIP) Audio Dispatch Bridge                         │
│    - State Police HQ Integration Feed                                      │
├────────────────────────────────────────────────────────────────────────────┤
│ 4. PROJECT CONFIGURATION (Config-only YAML / JSON files)                   │
│    - Site layout (Nilakkal 12 zones vs City Police 50 junctions)          │
│    - Network IP topology and camera RTSP URL inventory                     │
│    - Passenger estimation multipliers (Bus=50, Car=5, 2W=2)                │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 18. Development Priorities (Architecturally Ranked)

* **P0: Foundational Blockers (Must complete immediately):**
  1. Fix Kong edge gateway bypass in [`surv/kong/setup-kong-jwt.sh`](file:///opt/surv-learn/surv/kong/setup-kong-jwt.sh) for `X-Site-Token` traffic.
  2. Install `kcat` in [`surv/Dockerfile.mediamtx`](file:///opt/surv-learn/surv/Dockerfile.mediamtx) to restore Kafka camera lifecycle events.
  3. Align snapshot key to `{cam_id}/latest.jpg` in [`surv/workers/snapshot_worker.py`](file:///opt/surv-learn/surv/workers/snapshot_worker.py).
* **P1: Core Reusable Platform Capabilities (Both Tenders):**
  4. Alembic migration for Parking & ANPR schema (`parking_zone`, `anpr_transaction`, `vehicle_watchlist`).
  5. Real-time Parking Occupancy & Allocation Engine (`ParkingAllocationService`).
  6. Handheld Android POS terminal REST API bridge (`/api/v1/parking/entry-slip`).
  7. PostgreSQL trigram index and fuzzy plate search (`pg_trgm`).
  8. Watchlist matching and instant (<2s) UI alert notifications.
  9. Interactive GIS Map component in React SPA (Leaflet/MapLibre).
  10. Bi-lingual localization (English and Malayalam via `react-i18next`).
* **P2: Production Hardening & Advanced Modules:**
  11. Evidentiary video export packager with SHA-256 integrity manifest.
  12. Incident lifecycle management ticketing module.
  13. Line-crossing people counting and crowd density heatmap renderer.
  14. High Availability database clustering with Patroni.
  15. Automated CERT-In vulnerability remediation and security scanning.
* **P3: Long-Term Enhancements:**
  16. Biometric facial recognition and missing person search (`pgvector`).
  17. Predictive crowd intelligence and time-series queue forecasting.
  18. MAVLink drone telemetry integration and flight path plotting.

---

## 19. Target Architecture Diagram

```
                                  FIELD & SENSORS TIER
   ┌───────────────────────┐    ┌───────────────────────┐    ┌───────────────────────┐
   │ Fixed & PTZ Cameras   │    │ Dedicated ANPR Cams   │    │ Handheld Android POS  │
   │ (5MP Bullet, 40X PTZ) │    │ (+ 850nm IR Illum.)   │    │ (Thermal Slip Printer)│
   └──────────┬────────────┘    └──────────┬────────────┘    └──────────┬────────────┘
              │ RTSP                       │ RTSP                       │ HTTPS / JSON
              ▼                            ▼                            ▼
   ┌───────────────────────────────────────────────────────┐            │
   │           EDGE APPLIANCE / LOCAL PROCESSING UNIT      │            │
   │  - MediaMTX: RTSP pull & 7-day circular fMP4 storage  │            │
   │  - Edge ANPR: DeepStream / TensorRT OCR Inference     │            │
   │  - Edge Agent: SQLite event buffer & sync to Hub      │            │
   └──────────────────────────┬────────────────────────────┘            │
                              │ Encrypted WAN / OFC Ring                │
                              ▼                                         │
   ┌────────────────────────────────────────────────────────────────────┴─────────────┐
   │                       KONG ENTERPRISE API GATEWAY (:8000 / :8443)                │
   │  - Perimeter JWT validation (Web users) | X-Site-Token bypass (Edge appliances)  │
   │  - Commercial CORS, Rate Limiting, SSL termination, Load Balancing               │
   └──────────┬─────────────────────────────────────────────────────────┬─────────────┘
              │                                                         │
              ▼ Internal Network                                        ▼
   ┌────────────────────────────────────────────────────┐     ┌───────────────────────┐
   │        FASTAPI CORE APPLICATION CLUSTER (x2)       │     │    NGINX MEDIA PROXY  │
   │  - Camera & Stream Catalog  - Parking Occupancy    │     │  - HLS Stream Cache   │
   │  - ANPR Search & Watchlists - ICCC Incidents       │     │  - WebRTC Relay       │
   │  - Dynamic Stream Auth Hook - Traffic Reporting    │     └───────────┬───────────┘
   └──────────┬──────────────────┬──────────────────────┘                 │
              │                  │                                        │
              ▼                  ▼                                        ▼
   ┌───────────────────┐  ┌─────────────────────────────┐     ┌───────────────────────┐
   │ PATRONI HA CLUST  │  │ APACHE KAFKA 3-NODE KRaft   │     │  MediaMTX CLUSTER     │
   │ - PostgreSQL 16   │  │ - camera.motion             │     │  - RTSP/RTMP Ingest   │
   │ - Sync Replicas   │  │ - camera.status             │     │  - 60s fMP4 Slicing   │
   │ - Auto-Failover   │  │ - recording.segments        │     └───────────┬───────────┘
   │ - pg_trgm Search  │  │ - vehicle.anpr.detected     │                 │
   └───────────────────┘  │ - crowd.density.alert       │                 ▼
                          └──────────────┬──────────────┘     ┌───────────────────────┐
                                         │                    │  MinIO DISTRIBUTED S3 │
                                         ▼                    │  - 'recordings' (90d) │
                          ┌─────────────────────────────┐     │  - 'snapshots'        │
                          │    ASYNC WORKER SERVICES    │     │  - 'backup_clips'     │
                          │  - Segment DB Consumer      │     └───────────────────────┘
                          │  - Watchlist Alert Matcher  │
                          │  - MinIO Retention Cleaner  │
                          │  - Evidence Packaging       │
                          └─────────────────────────────┘
                                         │
                                         ▼ WebSockets / HTTPS
   ┌──────────────────────────────────────────────────────────────────────────────────┐
   │             INTEGRATED COMMAND & CONTROL CENTRE (ICCC) PRESENTATION              │
   │  - React 18 / Vite / Tailwind SPA with Bi-Lingual Support (Malayalam / English)  │
   │  - Common Operating Picture (COP) with Interactive GIS Map (Cameras, UAVs, Zones)│
   │  - Real-Time Parking Occupancy Grid & Entry/Exit Flow Gauges                     │
   │  - Video Wall Multi-Grid (Hls.js Low-Latency) & Incident Dispatch Console        │
   └──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 20. Recommended Development Sequence

```
STEP 1: Unblock Core Ingestion (Hours 1–4)
  ├── Patch 'surv/kong/setup-kong-jwt.sh' to bypass '/api/v1/fleet' & '/api/v1/motion/edge'
  ├── Add 'kcat' to 'surv/Dockerfile.mediamtx'
  └── Update 'surv/workers/snapshot_worker.py' to write '{cam_id}/latest.jpg'

STEP 2: Common Schema Extensions (Days 1–2)
  ├── Create Alembic migration for 'parking_zone', 'parking_session', 'anpr_transaction'
  ├── Enable PostgreSQL 'pg_trgm' extension
  └── Implement 'surv/app/routers/parking.py' and 'surv/app/routers/anpr.py'

STEP 3: Parking Engine & Handheld POS Integration (Days 3–5)
  ├── Build 'ParkingAllocationService' for live zone delta
  ├── Implement 'POST /api/v1/parking/entry-slip'
  └── Build 'ParkingDashboardPage.tsx' in React frontend with live occupancy gauges

STEP 4: ANPR Watchlist & Alert Engine (Days 6–7)
  ├── Add 'vehicle_watchlist' table and CRUD API
  ├── Build Kafka stream consumer matching plates against watchlist
  └── Add real-time UI notification toaster and audio chime in web SPA

STEP 5: Interactive GIS Map & Unified COP Dashboard (Days 8–10)
  ├── Integrate Leaflet / MapLibre into 'surv/frontend/src/pages/ICCCPage.tsx'
  ├── Plot camera pins, parking zones, and alerts with live status colors
  └── Implement 'react-i18next' for Malayalam and English UI toggle
```

---

## 21. Remaining Unknowns

1. **ARAI 230 km/h ANPR Speed Enforcement:** Developing custom OCR software will not satisfy Tender A's legal requirement for ARAI / CMVR Rule 126 certification. Bidding mandates securing an OEM partnership with a certified Indian ANPR vendor.
2. **Physical Camera Firmware & ONVIF Event Divergence:** Real-world camera firmware variants (Dahua, Hikvision, CP PLUS, Uniview) often format ONVIF XML differently. Physical testing on-site at Nilakkal will be required.
3. **Sabarimala Environmental Stress:** Extreme monsoons, lightning surges, and wild-animal attacks on cables require physical field verification of armored OFC depth, Gore-vent IP67 camera seals, and Class-B earthing (<0.2 Ohm).

---

## 22. Final Engineering Conclusions (The 6 Architectural Verbs)

To build a unified, enduring surveillance operating system capable of winning and executing both tenders, apply this strategy:

* **KEEP:** The core MediaMTX ingestion pipeline, Nginx low-latency HLS caching, MinIO S3 recording chunking, Apache Kafka KRaft event bus, and recursive PostgreSQL organizational closure table. They represent the strongest, most stable assets in the codebase.
* **EXTEND:** The database schema to include `parking_zone`, `parking_session`, `anpr_transaction`, and `vehicle_watchlist`; extend the frontend with `react-i18next` for Malayalam localization.
* **REFACTOR:** [`surv/kong/setup-kong-jwt.sh`](file:///opt/surv-learn/surv/kong/setup-kong-jwt.sh) to eliminate the edge agent 401 blocker, and refactor [`surv/workers/snapshot_worker.py`](file:///opt/surv-learn/surv/workers/snapshot_worker.py) to query cameras dynamically from PostgreSQL instead of static environment variables.
* **ADD:** An interactive GIS mapping component (Leaflet/MapLibre) to create the Common Operating Picture, a real-time Parking Occupancy Engine, and a trigram-based fuzzy plate search.
* **INTEGRATE:** Handheld Android POS thermal printers, ARAI-certified ANPR edge OCR engines, IP Public Address SIP horn speakers, and external deep learning computer vision workers.
* **DEFER:** Complex biometric face search (`pgvector`), proprietary drone ground stations, and predictive crowd AI until the foundational Parking, ANPR, and ICCC modules are fully commissioned and stabilized.
