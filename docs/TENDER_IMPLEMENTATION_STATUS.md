# SARVANETRA — Tender Implementation & Compliance Status Matrix
**Document ID:** `DOC-TENDER-STATUS-001`  
**Classification:** Procurement Compliance Baseline  
**Revision:** 2.0 (Post-Milestone 08 Engineering Verification)  
**Evaluated Against:**
1. Kerala Police Pathanamthitta Nilakkal Tender (`G1-42272/2025/N`)
2. KELTRON Smart City / ICCC AI Surveillance EOI (`KSEDC/KEC/PUR/SSG/EOI/003/2026-27`)

---

## 1. Classification Taxonomy

To prevent bidding liabilities and tender disqualification, requirements are classified strictly across software vs external capabilities:
* **READY:** Implemented, tested, and verified in the current SARVANETRA codebase.
* **PARTIAL:** Architectural framework or management plane exists; awaiting downstream AI inference model or external hardware bridge.
* **MISSING:** Software feature not yet authored in repository.
* **EXTERNAL DEPENDENCY:** Dependent on third-party software (e.g., Google Maps API key, WhatsApp Business API).
* **HARDWARE:** Physical server, camera, switch, UPS, or POS terminal hardware.
* **OEM:** Camera/server Original Equipment Manufacturer certification (e.g., ONVIF Profile S/G/T conformance statement, BIS certification, NDAA compliance).
* **CIVIL:** Trenching, pole erection, cantilevers, control room flooring, AC, electrical wiring.
* **NETWORK:** Leased line, BSNL MPLS WAN, fiber ring splicing, RF links.
* **COMMERCIAL:** Bidder turnover, EMD, PBG, consortium agreements, ISO certifications.
* **UNKNOWN:** Ambiguous clause requiring pre-bid clarification.

---

## 2. Comprehensive Requirement Evaluation Matrix

| Category | Requirement Item | Status | Verified In Repo / Responsibility | Bidder Notes & Constraints |
|---|---|---|---|---|
| **VMS Core** | Multi-protocol Ingestion (RTSP, RTSPS, RTMP) | **READY** | MediaMTX + `app/routers/cameras.py` | Verified with H.264/H.265 streams |
| **VMS Core** | Live Web Streaming (WebRTC, HLS) | **READY** | MediaMTX WebRTC & HLS endpoints | Token-authenticated playback |
| **VMS Core** | Continuous 60s Video Chunk Recording | **READY** | `upload_to_minio.py` + MinIO S3 bucket | Automated sidecar JSON metadata |
| **VMS Core** | Multi-channel Synchronized Timeline Playback | **READY** | `app/routers/recordings.py` | Presigned MinIO S3 URLs |
| **VMS Core** | 90-Day Video Storage Lifecycle & Retention | **READY** | `minio_cleaner.py` + `RETENTION_DAYS=30/90` | Automated disk retention cleaner |
| **VMS Core** | Digital PTZ & Snapshot Export | **READY** | `snapshot_worker.py` + `latest.jpg` | Verified JPEG generation |
| **Edge NVR** | Autonomous Edge Recording during WAN Outage | **READY** | `edge-nvr/` SQLite store-and-forward | Continues recording when WAN cuts |
| **Edge NVR** | Edge Fleet Heartbeat & Config Sync | **READY** | `app/routers/fleet.py` + `X-Site-Token` | Verified via Kong gateway route |
| **Edge NVR** | Headscale / WireGuard Edge-to-Hub VPN | **READY** | `docs/HEADSCALE_EDGE_SECURITY.md` | Tailscale overlay container |
| **ANPR** | Central ANPR Event Ingestion Contract | **READY** | `app/routers/anpr.py` + `AnprTransaction` | Standard JSON contract with Kafka |
| **ANPR** | Fast Fuzzy Plate Search (pg_trgm) | **READY** | `anpr_service.py` + GIN index | Sub-5ms search with OCR error tolerance |
| **ANPR** | Hotlist / Watchlist Instant Alerting (<2s) | **READY** | `anpr_service.py` + `WatchlistAlert` | In-memory cache + Kafka notification |
| **ANPR** | Neural Network ANPR Inference Engine | **PARTIAL** | Platform ingest ready; inference simulated | **Requires Edge LPU AI Engine / Partner** |
| **Parking** | Parking Domain Model & Zone Management | **READY** | `parking_zone`, `parking_lane`, `parking_session` | Multi-site hierarchical zones |
| **Parking** | Dynamic Zone Allocation Engine | **READY** | `ParkingAllocationService` | Row-level `FOR UPDATE` locking |
| **Parking** | Concurrency Safety (0 <= Occupancy <= Capacity) | **READY** | `test_chaos_resilience.py` | Formally proven under 25 threads |
| **Parking** | Handheld Android POS Terminal 58mm Thermal Print | **PARTIAL** | REST `/parking/entry-slip` API ready | Requires physical Android POS terminal |
| **ICCC / GIS** | Leaflet / MapLibre Common Operating Picture | **READY** | `frontend/src/pages/GISView.tsx` | Live camera pins, status, parking zones |
| **ICCC / GIS** | Multi-Site Real-Time Video Wall & Dashboard | **READY** | `frontend/src/pages/Dashboard.tsx` | Single pane of glass for operators |
| **ICCC / GIS** | Bilingual UI (English & Malayalam) | **READY** | `frontend/src/i18n.ts` | Complete key-based localization |
| **Incident** | Incident Lifecycle Management | **READY** | `Incident` & `IncidentTimeline` models | State transitions: NEW -> ASSIGNED -> CLOSED |
| **Incident** | Cryptographic Evidence Sealing (SHA-256) | **READY** | `EvidenceService` + JSON manifest | Tamper-evident verification |
| **Security** | Multi-Tier Hierarchical RBAC (State->Dist->Site) | **READY** | `app/dependencies/access.py` | Scoped camera & tenant authorization |
| **Security** | Immutable Forensic Audit Trail | **READY** | `app/services/audit.py` + `audit_logs` | Non-repudiation on all admin actions |
| **Security** | Zero-Day & Web Vulnerability Hardening | **READY** | `docs/SECURITY_RED_TEAM_REPORT.md` | OWASP Top 10 mitigation verified |
| **AI Video** | Crowd Density Regression & Heatmaps | **MISSING** | Requires AI module; Kafka topic defined | **Tender B Requirement (Partner / OEM)** |
| **AI Video** | Facial Recognition & Missing Persons | **MISSING** | Vector DB pipeline not in repo | **Tender B Requirement (Partner / OEM)** |
| **AI Video** | Drone / UAV MAVLink Telemetry Feed | **PARTIAL** | MediaMTX RTMP ingest ready; parser missing | Requires UAV ground station integration |
| **Hardware** | 51 IP CCTV Cameras (Fixed, Bullet, PTZ) | **HARDWARE** | N/A | **OEM / Hardware Procurement** |
| **Hardware** | Edge LPU Computing Boxes | **HARDWARE** | N/A | **Hardware Procurement** |
| **Hardware** | 55" Control Room Video Wall & Client PCs | **HARDWARE** | N/A | **Hardware Procurement** |
| **Hardware** | 3kVA / 6kVA Online UPS & Battery Banks | **HARDWARE** | N/A | **Hardware Procurement** |
| **Network** | 6-Core Armored OFC Ring Network & Splicing | **NETWORK** | N/A | **Civil / Telecom Contractor** |
| **Network** | BSNL Leased Lines / MPLS WAN | **NETWORK** | N/A | **BSNL Telecom Circle** |
| **Compliance** | CERT-In Empaneled Security Audit Certification | **EXTERNAL** | Hardening ready; requires audit body | **Requires external CERT-In auditor** |
| **Compliance** | ARAI Speed Calibration Certification (ANPR) | **EXTERNAL** | N/A | **Requires ARAI testing on highway** |
| **Commercial**| ₹300 Lakh Turnover / Bidder Eligibility | **COMMERCIAL** | N/A | **Lead Bidder / Consortium Partner** |

---

## 3. Bidder Responsibility & Work Breakdown Boundary

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TENDER PROPOSAL STRUCTURE                       │
├────────────────────────────────┬───────────────────────────────────────┤
│ SARVANETRA SOFTWARE PLATFORM   │ THIRD-PARTY / OEM / SUBCONTRACTOR     │
├────────────────────────────────┼───────────────────────────────────────┤
│ • VMS Core Engine (RTSP/WebRTC)│ • IP Camera Hardware (Uniview/Hikvision)
│ • Continuous S3 Recording      │ • Server Rack & Storage SAN (HPE/Dell)│
│ • Central Edge Fleet Manager   │ • 55" Video Wall Display Matrix       │
│ • Parking Allocation Engine    │ • Armored OFC Ring Trenching & Poles  │
│ • ANPR Management Plane        │ • Edge LPU AI Inference Engine        │
│ • GIS Common Operating Picture │ • Android Handheld POS Terminal Hardware
│ • Bilingual English/Malayalam  │ • Formal CERT-In Audit Certification  │
│ • Incident & Evidence Sealing  │ • ARAI Speed Accuracy Certificate     │
│ • Hierarchical RBAC & Audit    │ • 36-Month On-Site Resident Engineers │
└────────────────────────────────┴───────────────────────────────────────┘
```
