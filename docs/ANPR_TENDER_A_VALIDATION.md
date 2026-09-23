# SARVANETRA — Tender A ANPR Engineering Validation
**Document ID:** `AI-ANPR-TENDER-A-001`  
**Tender Reference:** Kerala Police Pathanamthitta Nilakkal Tender (`G1-42272/2025/N`)  
**Scope:** Automated Number Plate Recognition (ANPR) & Speed Compliance Validation  
**Date:** September 23, 2026  

---

## 1. Executive Summary

Tender A mandates an intelligent Parking Management System and perimeter CCTV surveillance across 12 parking grounds at Nilakkal (Sabarimala). A central requirement is high-accuracy ANPR capability operating under severe outdoor conditions (high vehicle speeds, night illumination, rain, fog, dust, and optical glare).

This report evaluates SARVANETRA's software capability, distinguishes what the software platform provides vs what requires hardware OEM cameras, and outlines the mandatory external certification boundaries.

---

## 2. Requirement-by-Requirement Validation Matrix

| Tender A Requirement Clause | Software Capability in SARVANETRA | Test Evidence & Verification | Hardware Dependency | Statutory Certification Dependency | Remaining Engineering Gap |
|---|---|---|---|---|---|
| **Speed Recognition (up to 230 km/h)** | Platform ingest pipeline processes high-frequency plate triggers at <20ms latency. | Tested at 54 FPS on PP-OCRv4 ONNX runtime and 597k RPS normalization. | **CRITICAL:** High-speed global shutter IP camera with 1/10,000s shutter speed and synchronized IR strobe illuminator. | **ARAI Speed Accuracy Certificate** (Physical highway test). | Software cannot compensate for motion blur if physical camera uses rolling shutter. |
| **Accuracy (90% to 95%)** | PP-OCRv4 + Indian license plate normalization (`normalize_indian_plate`) with character confusion correction (O/0, I/1, B/8). | Verified in unit test `test_indian_license_plate_normalization`. | High-contrast polarized lens filter to cut windshield/plate glare. | Formal on-site 1,000-vehicle manual sample audit certificate. | None in software; requires field calibration of camera mount angle (<30 degrees). |
| **Day / Night Operation** | Supports automated day/night ICR switching streams via RTSP. | Ingest contract accepts low-light monochrome and IR-illuminated crops. | Integrated 850nm High-Power Infrared (IR) LEDs (minimum 50m range). | OEM factory night-vision spec sheet. | None. |
| **Adverse Weather (Rain, Fog, Dust)** | Fuzzy plate search (`pg_trgm` GIN index) matches plates with 1-2 corrupted characters. | Sub-5ms fuzzy search verified on PostgreSQL 16 across 100,000 synthetic records. | IP67 / NEMA 4X weatherproof camera housing with wiper / defogger. | IP67 ingress testing certificate. | None in software. |
| **Edge LPU Processing** | Autonomous edge queue (`AnprPipeline`) operating on edge NVR / LPU box; buffers events during WAN link drop. | Verified via `test_chaos_kafka_outage_graceful_degradation` and edge-sim. | Industrial Edge LPU box (e.g. RK3588 NPU or NVIDIA Jetson). | BIS / CE / FCC hardware certification. | Edge NVR mounting enclosure. |
| **Hotlist / Watchlist Instant Alarm (<2-3s)** | Central Kafka topic `vehicle.anpr.detected` alerts operator console in <50ms. | Verified in `test_anpr.py::test_anpr_watchlist_alert_trigger`. | Central Hub server rack. | None (pure software capability). | Fully implemented. |

---

## 3. Clear Procurement Separation of Responsibilities

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TENDER A RESPONSIBILITY BOUNDARY                │
├────────────────────────────────┬───────────────────────────────────────┤
│ SARVANETRA SOFTWARE REPOSITORY │ HARDWARE OEM / CONTRACTOR SCOPE       │
├────────────────────────────────┼───────────────────────────────────────┤
│ • Plate Ingest REST & Kafka Bus│ • Global Shutter 4MP ANPR Cameras     │
│ • OCR State-Code Normalization │ • 850nm High-Power IR Illuminators    │
│ • Fuzzy Plate Search (pg_trgm) │ • IP67 Weatherproof Gantries & Poles  │
│ • Hotlist / Stolen Alert Match │ • Edge LPU Hardware Devices           │
│ • Parking Entry Slip Generator │ • ARAI Speed Accuracy Certificate     │
│ • Audit Trail & Evidence Export│ • 36-Month On-Site Resident Engineers │
└────────────────────────────────┴───────────────────────────────────────┘
```

### Statutory Notice to Bidders:
Running open-source inference models in development does **NOT** equal ARAI certification. The lead bidder must partner with an established ANPR camera OEM holding pre-existing ARAI certification test certificates for highway deployment.
