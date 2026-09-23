# SARVANETRA — Comprehensive Tender Requirements Catalogue
**Document Version:** 1.0.0  
**Date:** September 22, 2026  
**Sources:**  
1. **Tender A:** Government of Kerala, Home Department, Office of the District Police Chief, Pathanamthitta (Tender Ref No. `G1-42272/2025/N`, GeM PAC ₹300 Lakh) — *Integrated ANPR, AI based Parking Management System, CCTV Surveillance System, Redundant Network for Nilakkal & Revamp of UPS and Power backup for Pampa & Sannidhanam*  
2. **Tender B:** Kerala State Electronics Development Corporation Limited (KELTRON) EOI (Tender Ref No. `KSEDC/KEC/PUR/SSG/EOI/003/2026-27`) — *Selection of an End-to-End Custom Development, Implementation, and Financing Partner for AI-Based Surveillance Projects*

---

## 1. Classification Scheme

Every requirement is mapped into one of 13 normalized categories to distinguish software platform capabilities from physical hardware, civil engineering, third-party integrations, and organizational bidder qualifications:

* **Category A: SARVANETRA SOFTWARE PLATFORM** (Core VMS, streaming, API, multi-tenant hierarchy, session management, web UI)
* **Category B: AI/ML CAPABILITY** (Computer vision inference, ANPR OCR, crowd density estimation, facial recognition, trajectory tracking)
* **Category C: CAMERA / EDGE DEVICE** (Physical IP bullet, PTZ, ANPR cameras, lenses, illuminators, sensors)
* **Category D: SERVER / STORAGE** (Physical 2U rack servers, enterprise HDDs/SSDs, hardware RAID, SAN/NAS, client workstations)
* **Category E: NETWORKING** (Core switches, PoE+ edge switches, 6-core/12-core/24-core armored OFC, patch panels, Cat6 cabling)
* **Category F: POWER / UPS / ELECTRICAL** (Online double-conversion UPS, battery banks, DG sets, KSEB meter boxes, earthing rods)
* **Category G: FIELD INSTALLATION / CIVIL WORK** (Poles, gantry cantilevers, RCC foundation, trenching, HDPE ducting, water barricades)
* **Category H: THIRD-PARTY INTEGRATION** (Google Maps / GIS, Handheld Android POS printers, VMS displays, WhatsApp/SMS/Email gateways, State PHQ feed)
* **Category I: OEM REQUIREMENT** (OEM 10-year presence, OEM direct R&D, MAF undertakings, STQC/BIS certificates, Non-malicious code certificate)
* **Category J: BIDDER ELIGIBILITY / COMMERCIAL** (Turnover >= ₹8–10 Cr, past PSU projects >= ₹3–10 Cr, Kerala office with GST, EMD/Solvency, Consortium MOU)
* **Category K: SUPPORT / SLA / O&M** (36–60 month comprehensive onsite warranty, 24x7 resident engineers during pilgrimage season, 24hr MTTR)
* **Category L: DOCUMENTATION / COMPLIANCE** (As-built CAD drawings, STAAD PRO foundation designs, CERT-In vulnerability audit, DPDP Act 2023 compliance)
* **Category M: FUTURE / SCALABILITY** (Paid parking module, bay-by-bay parking sensors, statewide police PHQ consolidation, drone mission telemetry)

> [!IMPORTANT]
> Requirements marked **NOT A SOFTWARE PLATFORM REQUIREMENT** cannot be solved by the SARVANETRA application code. They mandate physical hardware supply, civil execution, OEM authorizations, or legal bidder qualifications.

---

## 2. Tender A Normalized Requirement Catalogue
**Authority:** District Police Chief, Pathanamthitta | **Project:** Nilakkal, Pampa & Sannidhanam (Sabarimala)

| Req ID | Section | Requirement Description | Type | Compliance Class | Tender Page | Category | Platform vs External Scope |
|---|---|---|---|---|---|---|---|
| **T1-PMS-001** | Sec 2, 4.1 | Centralized monitoring of 12 designated parking grounds at Nilakkal | Mandatory | Functional | Page 1, 2 | **A** | **SARVANETRA CORE:** Multi-site zone grouping, aggregated dashboard view |
| **T1-PMS-002** | Sec 2, 4.1 | Automated dynamic allocation of vehicle to parking ground on entry based on real-time availability | Mandatory | Functional | Page 1, 2 | **A / B** | **SARVANETRA CORE + LOGIC:** Ingestion of entry count, zone allocation logic |
| **T1-PMS-003** | Sec 4.1, BOQ | Automatic parking slip generation via handheld Android POS terminals at entry gates | Mandatory | Functional / Hw | Page 2, 13, 44 | **H** | **THIRD-PARTY / MOBILE:** Handheld Android POS app with thermal printer integration |
| **T1-PMS-004** | Sec 4.1 | Real-time calculation and display of zone-wise parking occupancy and vacancy | Mandatory | Functional | Page 2 | **A** | **SARVANETRA CORE:** In-memory / SQL tallying of entry vs exit per zone |
| **T1-PMS-005** | Sec 4.1 | Live dashboards at Central Control Room (CCR), main entry, Police Aid Posts | Mandatory | Functional | Page 2 | **A** | **SARVANETRA CORE:** Web SPA display on large monitors, role-based dashboards |
| **T1-PMS-006** | Sec 4.9 | Future capability for bay-by-bay sensor guidance and paid parking operations | Optional / Future | Architectural | Page 3, 4 | **M** | **FUTURE MODULE:** Modbus/MQTT sensor ingestion and payment gateway API |
| **T1-PMS-007** | BOQ PMS-1 | Parking Management Software licensed for 26 lanes (In and Out) | Mandatory | Licensing | Page 12 | **A** | **SARVANETRA CORE:** License enforcement or commercial multi-lane software |
| **T1-ANPR-001** | Sec 4.2, Specs | Automatic Number Plate Recognition on video streams for standard English alphanumeric plates | Mandatory | AI / ML | Page 3, 34 | **B** | **AI / ANPR ENGINE:** Deep learning OCR model running on edge LPU or central GPU |
| **T1-ANPR-002** | Sec 4.2, Specs | Vehicle classification into LMV, HMV, Cars, Bikes, 2-wheelers, 3-wheelers, Buses, Minibuses | Mandatory | AI / ML | Page 3, 34, 39 | **B** | **AI / ANPR ENGINE:** Object classification CNN (e.g., YOLOv8/v10/RT-DETR) |
| **T1-ANPR-003** | Sec 4.2, Specs | Capture and storage of vehicle make, model, brand, and vehicle color during daytime | Mandatory | AI / ML | Page 3, 34, 39 | **B** | **AI / ANPR ENGINE:** Secondary classification head for color & vehicle brand |
| **T1-ANPR-004** | Sec 4.2, Specs | Hotlist / Watchlist management ("Wanted", "Suspicious", "Stolen") with instant control room alert | Mandatory | Functional | Page 3, 34, 42 | **A** | **SARVANETRA CORE:** Database watchlist table, Kafka real-time matching (<2-3s alert) |
| **T1-ANPR-005** | Sec 4.2 | Tracking of which parking zone a vehicle is currently parked in | Mandatory | Functional | Page 3 | **A** | **SARVANETRA CORE:** Correlating entry gate ANPR event with zone assignment |
| **T1-ANPR-006** | Sec 4.3, Specs | ANPR operation under day/night, pitch-dark, rain, fog, dust, and headlight glare | Mandatory | Camera / AI | Page 3, 38, 40 | **C / B** | **CAMERA + AI:** Requires dedicated 5MP ANPR camera with synchronized 850nm IR illuminator |
| **T1-ANPR-007** | Specs 2.e, 15 | Recognition of number plates on vehicles moving at speeds up to 230 km/h (+/- 2%) | Mandatory | AI / Testing | Page 34, 40 | **B / I** | **EXTERNAL CERTIFICATION:** ARAI / Rule 126 CMVR speed test certificate for ANPR engine |
| **T1-ANPR-008** | Specs 2.g | Local ANPR processing on edge Local Processing Unit (LPU) to survive network outage | Mandatory | Edge AI | Page 34, 38 | **B / C** | **EDGE NVR / LPU:** On-premise industrial PC running edge inference pipeline |
| **T1-ANPR-009** | Specs 9, 5 | ANPR reading accuracy >= 90% daytime, >= 80% nighttime (90-95% overall) | Mandatory | AI / Metric | Page 35, 39, 41 | **B** | **AI BENCHMARK:** Tested accuracy on Indian HSRP and standard plates |
| **T1-ANPR-010** | Specs 10 | Detection of 2-wheeler traffic violations: "No Helmet" and "Triple Riding" | Mandatory | AI / ML | Page 35, 41 | **B** | **AI INFERENCE:** Rider keypoint / helmet detection CNN |
| **T1-ANPR-011** | Specs 3.a | Damaged / altered number plate detection for accident and hit-and-run investigation | Mandatory | AI / ML | Page 34 | **B** | **AI INFERENCE:** Plate damage / anomaly segmentation |
| **T1-ANPR-012** | Specs 2.c, 10 | Direct storage of vehicle plate, JPEG snapshot, timestamp, and site in PostgreSQL database | Mandatory | Data Layer | Page 34, 41 | **A** | **SARVANETRA CORE:** Native PostgreSQL schema for ANPR transaction logs |
| **T1-ANPR-013** | Specs 6.b, 15 | Fuzzy plate search in database supporting Levenshtein edit distance of 1 and 2 characters | Mandatory | Search / API | Page 35, 42 | **A** | **SARVANETRA CORE:** PostgreSQL `pg_trgm` extension or Elasticsearch fuzzy query |
| **T1-ANPR-014** | Specs 13 | Tamper-proof date/time watermarking embedded directly onto captured vehicle JPEG images | Mandatory | Security / Img | Page 42 | **A / B** | **IMAGE PROCESSING:** Cryptographic watermark / metadata embedding in FFmpeg/Pillow |
| **T1-ANPR-015** | Specs 14 | Bi-lingual Graphical User Interface supporting English and Malayalam | Mandatory | Frontend UI | Page 42 | **A** | **SARVANETRA FRONTEND:** `react-i18next` localization for English & Malayalam |
| **T1-ANPR-016** | Specs 16.e | Automatic pre/post video clip recording (few seconds before and after) for hotlisted vehicles | Mandatory | Video / VMS | Page 42 | **A** | **SARVANETRA CORE:** Segment extraction or edge NVR pre-event buffer clip |
| **T1-ANPR-017** | Specs 17 | Manual license plate correction workflow by authorized users with non-tamperable audit logs | Mandatory | Workflow | Page 42 | **A** | **SARVANETRA CORE:** Plate edit UI modal + immutable `audit_log` entry |
| **T1-ANPR-018** | Specs 2.h, 4.7| People crowd estimation and traffic density derived from vehicle count and seat capacity | Mandatory | Analytics | Page 3, 34 | **A / B** | **ANALYTICS ENGINE:** Configurable passenger multiplier per vehicle class (Bus=50, Car=5) |
| **T1-ANPR-019** | Specs 8, 4.7 | Traffic analytics reports: volume, peak-hour trends, historical comparison, daily/monthly | Mandatory | Reporting | Page 3, 38 | **A** | **SARVANETRA FRONTEND/API:** Chart.js/Recharts time-series traffic aggregation |
| **T1-ANPR-020** | Specs BOQ 2 | Seamless integration with existing Pathanamthitta Control Room and State PHQ Trivandrum | Mandatory | Integration | Page 9, 37 | **H** | **EXTERNAL INTEGRATION:** REST API / RTSP re-stream / Kafka bridge to State Police HQ |
| **T1-ANPR-021** | BOQ Specs | Supply of 2 Nos 5MP ANPR Bullet Cameras (5-50mm motorized lens, 50fps, 130dB WDR, IP67, IK10) | Mandatory | Hardware | Page 9, 25 | **C** | **NOT A SOFTWARE REQUIREMENT:** Physical camera procurement |
| **T1-ANPR-022** | BOQ Specs | Supply of 2 Nos External IR Illuminators (850nm, 100m, 42 LEDs, IEC-62471 eye safety certified) | Mandatory | Hardware | Page 9, 35 | **C** | **NOT A SOFTWARE REQUIREMENT:** Physical illuminator procurement |
| **T1-ANPR-023** | BOQ Specs | Supply of 1 No Field Server / LPU (i7 13th Gen+, 32GB RAM, GPU HD630+, MIL-STD-810G, dual GbE) | Mandatory | Hardware | Page 9, 36 | **D** | **NOT A SOFTWARE REQUIREMENT:** Edge industrial compute hardware |
| **T1-CCTV-001** | Sec 4.4, BOQ | IP CCTV surveillance covering entry/exit, 12 parking grounds, helipad, circulation routes | Mandatory | Deployment | Page 3, 4 | **C / G** | **NOT A SOFTWARE REQUIREMENT:** 25 PMS fixed cameras, 16 bullet cameras, 10 PTZ cameras |
| **T1-CCTV-002** | Sec 4.5 | All CCTV footage recorded and retained for a minimum of 90 days | Mandatory | Storage / VMS | Page 3 | **A / D** | **SARVANETRA + HW:** MinIO retention policy configured to 90 days + Enterprise Storage |
| **T1-CCTV-003** | Sec 4.5 | Recorded footage exportable and storable outside CCTV system for evidentiary use | Mandatory | VMS / Legal | Page 3 | **A** | **SARVANETRA CORE:** MP4 clip export with digital signature/hash verification |
| **T1-CCTV-004** | Sec 4.6 | Local ANPR data stored in LPU for min 7 days, Central Control Room retained for min 90 days | Mandatory | Retention | Page 3 | **A** | **SARVANETRA CORE:** Edge SQLite 7-day TTL + Hub PostgreSQL/MinIO 90-day retention |
| **T1-CCTV-005** | BOQ Specs | 5MP Low-Light Bullet Cameras with ONVIF Profiles S/G/T/M, STQC, UL, CE, RoHS, in-camera AI | Mandatory | Hardware | Page 10, 22 | **C / I** | **NOT A SOFTWARE REQUIREMENT:** STQC/BIS certified OEM cameras |
| **T1-CCTV-006** | BOQ Specs | 4MP PTZ Cameras (40x Optical Zoom, 450m IR, 140dB WDR, IP67, IK10, ONVIF S/G/T/M) | Mandatory | Hardware | Page 14, 28 | **C / I** | **NOT A SOFTWARE REQUIREMENT:** STQC/BIS certified PTZ cameras |
| **T1-CCTV-007** | BOQ Specs | 32-Channel 4K Embedded NVR with 90-day storage, 4 SATA bays (up to 80TB), TPM cyber chipset | Mandatory | Hardware | Page 14, 31 | **D** | **NOT A SOFTWARE REQUIREMENT:** Physical standalone appliance NVR |
| **T1-CCTV-008** | Sec 3, 10 | Seasonal shifting of CCTV visuals between Nilakkal Police Station & Nilakkal Control Room | Mandatory | Operational | Page 2, 6 | **A / K** | **SARVANETRA CORE:** Dynamic multi-workstation stream routing via Kong/Nginx |
| **T1-NET-001** | Sec 6, BOQ | Dedicated redundant communication network with min 6-core OFC links (24C/12C/6C armored) | Mandatory | Network | Page 4, 15, 50 | **E / G** | **NOT A SOFTWARE REQUIREMENT:** Trenching, HDPE pipe, OFC laying, splicing |
| **T1-NET-002** | Sec 6, BOQ | High-speed redundant ring network topology (cable cut/link failure does not interrupt stream) | Mandatory | Network | Page 4, 15 | **E** | **NOT A SOFTWARE REQUIREMENT:** RSTP/MSTP/ERPS ring configuration on managed switches |
| **T1-NET-003** | Sec 6, BOQ | 2 Nos 24-Port 10G SFP+ Stackable Layer-3 Core Switches with 4x 25G uplinks, MTCTE certified | Mandatory | Hardware | Page 4, 15, 47 | **E** | **NOT A SOFTWARE REQUIREMENT:** Enterprise Layer 3 core switch hardware |
| **T1-NET-004** | BOQ Specs | 13 Nos 8-Port Gigabit PoE+ (170W) Layer-2+ Field Switches with 2x SFP fiber uplinks | Mandatory | Hardware | Page 10, 15, 46 | **E** | **NOT A SOFTWARE REQUIREMENT:** Field PoE+ switches in outdoor racks |
| **T1-PWR-001** | Sec 8, BOQ | Revamp of UPS and battery backup at Sabarimala CCTV (Pampa & Sannidhanam) for 2–6 hr backup | Mandatory | Electrical | Page 5, 18, 58 | **F** | **NOT A SOFTWARE REQUIREMENT:** 3kVA/6kVA Online UPS + 200AH/100AH battery banks |
| **T1-PWR-002** | BOQ Specs | 12 Nos 1000VA UPS with 6-Hour Backup (120AH battery) for outdoor CCTV field poles | Mandatory | Electrical | Page 11, 16 | **F** | **NOT A SOFTWARE REQUIREMENT:** Pole-mounted field UPS units |
| **T1-PA-001** | Sec 4.8, BOQ | IP-based Public Address system touch console (min 30 IP speakers) and 5x 30W IP66 speakers | Mandatory | Hardware / Sw | Page 3, 18 | **H** | **NOT A SOFTWARE REQUIREMENT / INTEGRATION:** SIP/RTSP IP horn speaker system |
| **T1-CIVIL-001** | BOQ Specs | 33 GI camera poles, 1 Cantilever gantry pole (8m high x 7m horizontal), STAAD PRO design | Mandatory | Civil | Page 12, 15 | **G** | **NOT A SOFTWARE REQUIREMENT:** Civil foundations, gantry erection |
| **T1-CCR-001** | Sec 7, BOQ | Control room modernization: 55" commercial 4K displays, client workstations (i7/16GB/SSD) | Mandatory | Hardware | Page 4, 9, 45 | **D** | **NOT A SOFTWARE REQUIREMENT:** Physical video wall & workstations |
| **T1-SLA-001** | Sec 10, 17 | Comprehensive 36-month onsite warranty and maintenance; 24-hour MTTR | Mandatory | Support | Page 6, 7 | **K** | **NOT A SOFTWARE REQUIREMENT:** SI SLA commitment |
| **T1-SLA-002** | Sec 17 | 1 Resident Site Engineer deployed 3 weeks prior and throughout 3-month festival + pooja days | Mandatory | Manpower | Page 7 | **K** | **NOT A SOFTWARE REQUIREMENT:** Onsite technical staffing |
| **T1-QUAL-001** | Sec 11, PreQ | Integrator turnover >= ₹10 Cr/yr for last 3 years; Solvency certificate of ₹10 Cr from bank | Mandatory | Commercial | Page 8, 21 | **J** | **NOT A SOFTWARE REQUIREMENT:** Prime bidder financial qualification |
| **T1-QUAL-002** | PreQ 13 | Integrator experience: 1 PSU/Govt CCTV/VMS job of ₹10 Cr or 2 of ₹5 Cr or 3 of ₹3.75 Cr in 3 yrs | Mandatory | Experience | Page 8, 21 | **J** | **NOT A SOFTWARE REQUIREMENT:** System integrator credentials |
| **T1-QUAL-003** | PreQ 15, 29 | Integrator & Parking OEM must have active registered office in Kerala with GST number | Mandatory | Statutory | Page 8, 21, 22 | **J** | **NOT A SOFTWARE REQUIREMENT:** Kerala legal presence |
| **T1-QUAL-004** | PreQ 1, 10 | CCTV OEM in India >10 yrs; No Chinese origin (GFR Rule 144(xi)); No GB28181/CCC | Mandatory | OEM Legal | Page 19, 20 | **I** | **NOT A SOFTWARE REQUIREMENT:** OEM origin declaration |
| **T1-QUAL-005** | PreQ 20-24 | ANPR OEM registered in India >10 yrs, R&D in India, 2 Govt projects with >=500 AI licenses | Mandatory | OEM Legal | Page 21 | **I** | **NOT A SOFTWARE REQUIREMENT:** ANPR OEM company credentials |
| **T1-QUAL-006** | PreQ 28 | Parking Management OEM successfully executed >=3000 parking lots in PSU in India | Mandatory | OEM Exp | Page 22 | **I** | **NOT A SOFTWARE REQUIREMENT:** Parking software OEM credentials |
| **T1-SEC-001** | Specs 10, 11 | CERT-In empaneled agency vulnerability assessment and encryption certificate for Local & Central apps | Mandatory | Security / Audit | Page 35, 40 | **L** | **CERTIFICATION AUDIT:** Formal third-party CERT-In assessment |

---

## 3. Tender B Normalized Requirement Catalogue
**Authority:** KELTRON (Kerala State Electronics Development Corporation Ltd) | **Type:** EOI for System Integrator / Partner

| Req ID | Section | Requirement Description | Type | Compliance Class | Tender Page | Category | Platform vs External Scope |
|---|---|---|---|---|---|---|---|
| **T2-VMS-001** | Sec 4.7, 4.11 | Centralized VMS for live monitoring, intelligent recording, playback, and evidence export | Mandatory | Functional | Page 10, 11 | **A** | **SARVANETRA CORE:** MediaMTX + MinIO + FastAPI core video management |
| **T2-VMS-002** | Sec 4.7 | Event-based recording, smart video search, and secure multi-tier storage management | Mandatory | Functional | Page 11 | **A** | **SARVANETRA CORE:** Segment tagging (`full`, `motion`, `guard`), timeline query |
| **T2-VMS-003** | Sec 4.7 | Comprehensive camera health monitoring, uptime tracking, and failure alerting | Mandatory | Functional | Page 11 | **A** | **SARVANETRA CORE:** `status_monitor.py` and `notifier.py` |
| **T2-AI-001** | Sec 4.1.1 | Perimeter intrusion detection on live and recorded video streams | Mandatory | AI / ML | Page 7 | **B** | **AI ENGINE:** Edge/central computer vision inference worker |
| **T2-AI-002** | Sec 4.1.1 | Line crossing and unauthorized access detection with real-time alerts | Mandatory | AI / ML | Page 7 | **B** | **AI ENGINE:** Virtual tripwire geometry algorithm |
| **T2-AI-003** | Sec 4.1.1 | Loitering detection (dwell time threshold in user-defined polygon zone) | Mandatory | AI / ML | Page 7 | **B** | **AI ENGINE:** Trajectory tracking + time accumulation |
| **T2-AI-004** | Sec 4.1.1 | Abandoned or unattended object detection | Mandatory | AI / ML | Page 7 | **B** | **AI ENGINE:** Stationary foreground blob classification |
| **T2-AI-005** | Sec 4.1.1 | Fall detection and medical emergency alert | Mandatory | AI / ML | Page 7 | **B** | **AI ENGINE:** Human pose estimation (keypoint orientation analysis) |
| **T2-AI-006** | Sec 4.1.1 | Suspicious or abnormal behavior detection | Mandatory | AI / ML | Page 7 | **B** | **AI ENGINE:** Temporal action recognition / trajectory anomaly model |
| **T2-AI-007** | Sec 4.1.1 | Object classification (person, bicycle, motorbike, car, bus, truck) | Mandatory | AI / ML | Page 7 | **B** | **AI ENGINE:** Pretrained COCO-class detection model |
| **T2-AI-008** | Sec 4.1.1 | Multi-camera vehicle and person tracking across non-overlapping views | Mandatory | AI / ML | Page 7 | **B** | **AI ENGINE:** Re-identification (ReID) embedding feature matching |
| **T2-FLOW-001** | Sec 4.1.2 | Bidirectional entry and exit counting across defined thresholds | Mandatory | Analytics | Page 8 | **B** | **AI ENGINE:** Overhead or angled line-crossing counting model |
| **T2-FLOW-002** | Sec 4.1.2 | Real-time area occupancy monitoring and pedestrian throughput metrics | Mandatory | Analytics | Page 8 | **A / B** | **SARVANETRA + AI:** Inflow minus outflow accumulator |
| **T2-FLOW-003** | Sec 4.1.2 | Queue length estimation and queue progression / wait-time analysis | Mandatory | Analytics | Page 8 | **B** | **AI ENGINE:** Bounding-box queue clustering model |
| **T2-FLOW-004** | Sec 4.1.2 | Pedestrian movement direction, dwell time, flow visualization, and heat maps | Mandatory | Analytics | Page 8 | **A / B** | **SARVANETRA CORE:** Canvas heatmap rendering from trajectory coordinates |
| **T2-CROWD-001**| Sec 4.2.1 | Continuous crowd density estimation (persons per m²) across monitored zones | Mandatory | Analytics | Page 8, 13 | **B** | **AI ENGINE:** Density map regression model (e.g., CSRNet, DM-Count) |
| **T2-CROWD-002**| Sec 4.2.1 | Congestion identification, risk indicators, and automated threshold alerts | Mandatory | Analytics | Page 8 | **A / B** | **SARVANETRA CORE:** Configurable trigger thresholds dispatching alerts |
| **T2-PRED-001** | Sec 4.3.1 | Predictive crowd intelligence: forecast crowd build-up, queue formation, congestion | Mandatory | Predictive AI| Page 8 | **B** | **AI / DATA SCIENCE:** Time-series forecasting (LSTM / Prophet / ARIMA) |
| **T2-PRED-002** | Sec 4.3.1 | Demand forecasting, capacity utilization modeling, and operational risk scoring | Mandatory | Analytics | Page 8 | **B** | **DATA SCIENCE:** Statistical predictive modeling pipeline |
| **T2-JOURNEY-001**| Sec 4.3.2 | Journey intelligence: integrate transport, parking, access control, gates, queues | Mandatory | Integration | Page 9 | **A / H** | **SARVANETRA ARCH:** Multi-modal data ingestion & timeline correlation |
| **T2-ANPR-001** | Sec 4.4.1 | AI-enabled ANPR: vehicle ID, tracking, entry/exit, blacklist/whitelist, search | Mandatory | AI / ML | Page 9 | **B / A** | **AI ENGINE + SARVANETRA:** OCR model + Watchlist database |
| **T2-PARK-001** | Sec 4.4.2 | Smart parking: real-time occupancy, vehicle guidance, overflow detection, dashboards | Mandatory | Functional | Page 9 | **A / H** | **SARVANETRA CORE:** Parking management module and dashboard widgets |
| **T2-MISSING-001**| Sec 4.4.3 | Face-based search, video analytics correlation, and last-seen location timeline | Mandatory | AI / Biometric| Page 9, 10 | **B / L** | **AI ENGINE:** Face detection + 512-d feature vector indexing (Milvus/pgvector) |
| **T2-DRONE-001**| Sec 4.5.1 | Drone video streaming ingest (RTSP/RTMP), situational awareness, and recording | Mandatory | Video / Ingest | Page 10 | **A** | **SARVANETRA CORE:** MediaMTX RTMP push ingest natively supports drone feeds |
| **T2-DRONE-002**| Sec 4.5.1 | Drone mission management, aerial telemetry overlay, and GIS coordinate integration | Mandatory | Integration | Page 10 | **H** | **THIRD-PARTY:** MAVLink / Drone control SDK integration |
| **T2-OPRESP-001**| Sec 4.6.1 | Automated crowd regulation: dynamic access control, automated SOP execution | Mandatory | Operational | Page 10 | **A** | **SARVANETRA CORE:** Event-driven rule engine (Kafka -> Action trigger) |
| **T2-OPRESP-002**| Sec 4.6.1 | Integration with Public Announcement (PA), Variable Message Signs (VMS), and SMS | Mandatory | Integration | Page 10 | **H** | **THIRD-PARTY:** Protocols: SIP/VoIP, NTCIP/TCP for VMS displays, HTTP SMS |
| **T2-ICCC-001** | Sec 4.8 | Integrated Command and Control Centre: Common Operating Picture (COP) dashboard | Mandatory | UI / Platform | Page 11, 13 | **A** | **SARVANETRA FRONTEND:** Unified executive GIS command dashboard |
| **T2-ICCC-002** | Sec 4.8 | GIS map visualization with real-time camera, sensor, alert, and drone overlay | Mandatory | GIS / UI | Page 11, 13 | **A / H** | **SARVANETRA FRONTEND:** Leaflet / OpenLayers / Mapbox with GeoJSON layers |
| **T2-ICCC-003** | Sec 4.8 | Multi-incident lifecycle management, decision support, and audit trail export | Mandatory | Workflow | Page 11 | **A** | **SARVANETRA CORE:** Incident state machine (New, Assigned, Escalated, Closed) |
| **T2-ICCC-004** | Sec 4.8 | Mobile client access for authorized field officers and decision makers | Mandatory | Mobile | Page 11 | **H** | **MOBILE APP:** Android/iOS React Native client with push notifications |
| **T2-ARCH-001** | Sec 4.9 | Open standards, modular microservice architecture, and open REST/WebSocket APIs | Mandatory | Architectural | Page 11, 12 | **A** | **SARVANETRA CORE:** FastAPI modular routers, OpenAPI 3.0 specs, Kafka KRaft |
| **T2-ARCH-002** | Sec 4.9 | Cloud, On-Premises, and Hybrid deployment capability | Mandatory | DevOps | Page 12 | **A** | **SARVANETRA CORE:** Docker Compose and containerized microservices |
| **T2-ARCH-003** | Sec 4.9 | High Availability (HA) with no single point of failure (Active-Active / Active-Passive) | Mandatory | Architecture | Page 12 | **D / E** | **INFRASTRUCTURE:** Patroni/pgpool for Postgres, Kafka KRaft 3-node, MinIO cluster |
| **T2-ARCH-004** | Sec 4.9 | Database clustering, synchronous replication, and automated failover/failback | Mandatory | Database | Page 12 | **D** | **INFRASTRUCTURE:** PostgreSQL Patroni HA cluster |
| **T2-SEC-001** | Sec 4.9 | Compliance with the Digital Personal Data Protection Act, 2023 (DPDP Act) | Mandatory | Compliance | Page 12 | **L / A** | **SARVANETRA + LEGAL:** Data minimization, consent tracking, PII redaction |
| **T2-SEC-002** | Sec 4.9 | Secure SDLC based on OWASP Top 10 guidelines and strict vulnerability management | Mandatory | Security | Page 12 | **L** | **DEV PROCESS:** Bandit, Trivy container scanning, SAST/DAST pipelines |
| **T2-SEC-003** | Sec 4.9 | Third-party security audit and certification by a CERT-In empaneled auditor before Go-Live | Mandatory | Security / Audit | Page 12 | **L** | **EXTERNAL AUDIT:** Formal CERT-In penetration test and closure report |
| **T2-DELIV-001**| Sec 4.10, 10.7| Complete source code, documentation, and IP rights transferred to purchaser | Mandatory | Legal / IP | Page 12, 18 | **J / L** | **ORGANIZATIONAL:** Contractual transfer of custom software IP to KELTRON |
| **T2-DELIV-002**| Sec 4.10, 10.8| Minimum 5 years of comprehensive warranty, SLA, and Annual Technical Support | Mandatory | Commercial | Page 12, 18 | **K** | **NOT A SOFTWARE REQUIREMENT:** 5-year SLA contract commitment |
| **T2-MANPOWER-001**| Sec 5 | Project team staffing: PM (8+y), Architect (10+y), Tech Lead (8+y), 3x Sr Devs (5+y), QA, UI/UX, 2x DBA, DevOps, Cyber Expert | Mandatory | HR / Team | Page 14 | **J** | **NOT A SOFTWARE REQUIREMENT:** Resumes and qualifications of 12 named experts |
| **T2-QUAL-001** | Sec 2.1, 2.2 | Average annual turnover >= ₹8 Cr over last 3 FYs; Positive net worth as on 31/03/2026 | Mandatory | Financial | Page 4 | **J** | **NOT A SOFTWARE REQUIREMENT:** Audited balance sheets and CA certificate |
| **T2-QUAL-002** | Sec 2.4 | Prior experience: AI surveillance / TMS / Safe City >= ₹3 Cr; >=100 AI Video Analytics licenses | Mandatory | Experience | Page 5, 6 | **J** | **NOT A SOFTWARE REQUIREMENT:** Client work orders & completion certificates |
| **T2-QUAL-003** | Sec 2.5 | Mandatory company certifications: Any two of ISO 9001:2015, ISO 27001:2022, CMMI Level 3 | Mandatory | Quality | Page 5, 7 | **J** | **NOT A SOFTWARE REQUIREMENT:** ISO/CMMI certificates |
| **T2-QUAL-004** | Sec 3.5 | Live Technical Presentation and Product Demonstration (30 marks out of 100) | Mandatory | Technical | Page 7 | **A / B** | **SARVANETRA DEMO:** Running live testbench with simulated video & analytics |
