# SARVANETRA — AI Privacy & Data Protection Architecture
**Document ID:** `AI-PRIVACY-ARCH-001`  
**Statutory Framework:** Digital Personal Data Protection Act 2023 (DPDP Act 2023), IT Act 2000, Bureau of Indian Standards (BIS) Data Governance  
**Scope:** Privacy-by-Design, Biometric Vector Isolation, Redaction, Retention & Audit Policies for AI Vision Operations  
**Date:** September 23, 2026  
**Status:** Approved Architecture Guideline  

---

## 1. Executive Summary & Privacy Principles

Surveillance AI systems intrinsically process personally identifiable information (PII) and sensitive biometric information (SBI). Under India's **Digital Personal Data Protection Act (DPDP Act) 2023**, processing of such data mandates strict purpose limitation, data minimization, cryptographic storage isolation, role-based access control, defined retention periods, and automated redaction.

SARVANETRA adopts a strict **Privacy-by-Design** architecture across its AI inference, storage, and presentation tiers:
1. **Raw Video & Frame Isolation:** AI workers process frames in ephemeral memory buffers; unredacted frames are discarded immediately post-inference unless flagged as evidence.
2. **Biometric Embedding Segregation:** Face embeddings (128-dim / 512-dim floating point vectors) are isolated in a restricted cryptographic vault and never exposed via client-facing APIs.
3. **No Sensitive PII in Logs:** Plate characters, facial descriptors, and person trajectories are sanitized in all application, gateway, and Kafka broker logs.
4. **Automated Evidence Redaction:** Exported CCTV footage automatically obfuscates bystander faces and non-target license plates using automated bounding-box pixelation/blurring.

---

## 2. AI-Generated Sensitive Information Inventory

| Data Element | Classification | Source Component | Vulnerability / Exposure Risk | Storage Engine & Protection | Access Tier |
|---|---|---|---|---|---|
| **License Plate Characters** | Indirect PII / Vehicle Identification | `anpr_pipeline.py` | Stalking, unauthorized tracking, mass vehicular surveillance | Encrypted at rest (AES-256) in PostgreSQL `anpr_events` | Law Enforcement / Parking Ops (Role: `OFFICER`, `ADMIN`) |
| **Vehicle Image Crops** | Contextual PII (Driver visible in windshield) | ANPR High-Resolution Camera | Privacy breach of driver & passengers | MinIO Object Store (S3 bucket with SSE-S3 encryption) | Authorized Investigating Officer with audit token |
| **Face Crops** | Sensitive Biometric PII | Face Detection Engine | Identity theft, unauthorized identification | MinIO Restricted Vault (`biometrics-secure`) | Strictly restricted (`SUPERADMIN`, `FORENSIC_LEAD`) |
| **Face Embeddings (Vectors)** | Mathematical Biometric Identifier | Face Recognition Feature Extractor | Reverse-engineering reconstruction, biometric spoofing | Vector DB / Isolated PostgreSQL table (`pgvector` with salt) | Internal AI Matcher Engine ONLY (Never exposed to REST API) |
| **Person Trajectory / Breadcrumbs** | Behavioral PII (Movement history) | ByteTrack / Multi-camera ReID | Routine profiling, spatial stalking of citizens | Ephemeral Redis cache (TTL 24 hours); aggregated summaries in DB | System automated rules; Operator requires Incident Warrant |
| **Fall / Medical Alert Snapshots** | Sensitive Personal Health Data | Fall Detection / Pose Estimator | Dignity violation, medical condition exposure | MinIO Encrypted Evidence Bucket | Medical Dispatch / Control Room Duty Officer |

---

## 3. Architecture for Biometric & PII Isolation

```text
               ┌────────────────────────────────────────────────────────┐
               │              AI INFERENCE TIER (EPHEMERAL)             │
               │                                                        │
               │  [RTSP Stream] ──► [In-Memory Frame Buffer]            │
               │                             │                          │
               │              ┌──────────────┴──────────────┐           │
               │              ▼                             ▼           │
               │     [Face/Plate Detector]        [Vector Embedder]     │
               │              │                             │           │
               └──────────────┼─────────────────────────────┼───────────┘
                              │ Crops                       │ 512-d Vector
                              ▼                             ▼
               ┌──────────────────────────────┐    ┌────────────────────┐
               │    MINIO OBJECT STORAGE      │    │ BIOMETRIC ISOLATION│
               │    (Encrypted Bucket:        │    │ VAULT (RESTRICTED) │
               │     `ai-evidence-vault`)     │    │                    │
               │                              │    │ Encrypted Vectors  │
               │  • Bystander auto-blurred    │    │ (Salted Cosine DB) │
               │  • SHA-256 digital seal      │    │ NO USER ACCESS     │
               │  • 30-day retention lock     │    │ Internal Match Only│
               └──────────────┬───────────────┘    └─────────┬──────────┘
                              │                              │
                              ▼                              ▼
               ┌────────────────────────────────────────────────────────┐
               │               APPLICATION & PRESENTATION TIER          │
               │                                                        │
               │  • REST API: Returns match status + confidence ONLY    │
               │  • Logs: License plate masked as `KL-01-**-**34`       │
               │  • Export: Automatic redaction of bystander faces      │
               │  • Audit: Every query logged to immutable ledger       │
               └────────────────────────────────────────────────────────┘
```

---

## 4. Key Privacy Controls & Safeguards

### 4.1. Biometric Vector Protection & Mathematical Isolation
* Face recognition models extract high-dimensional embedding vectors ($x \in \mathbb{R}^{512}$). These embeddings are stored with system-generated UUIDs with no direct mapping to citizen identities.
* The matching service executes 1:N vector queries strictly within the backend worker boundary. The REST API exposes only:
  ```json
  {
    "match_found": true,
    "confidence": 0.942,
    "case_id": "INC-2026-0923-01",
    "alert_timestamp": "2026-09-23T08:20:00Z"
  }
  ```
  Raw vector floats are explicitly omitted from all API schemas.

### 4.2. Sensitive Data Log Masking & Sanitization
All logger adapters implement automated regex filtering to sanitize PII before writing to disk, stdout, or Kafka:
* **License Plates:** `KL01AB1234` is serialized in logs as `KL01****34`.
* **Personal Names & Aadhaar/ID:** Fully redacted to `[REDACTED_PII]`.
* **GPS Coordinates:** Truncated to 2 decimal places in public logs to prevent pinpoint location tracking of individuals.

### 4.3. Automated Dynamic Video Redaction
For export of evidence video footage under Section 65B of the Indian Evidence Act or public records requests:
* The system invokes the Redaction Pipeline (`OpenCV + YOLOX-Nano`).
* Any person or vehicle not explicitly designated as the "Target Subject of Investigation" is processed through Gaussian blurring ($\sigma = 15$) or Mosaic pixelation ($16 \times 16$ block size).
* The redacted stream is signed and sealed with a verifiable digital watermark.

### 4.4. Retention, Expiration & Right to Erasure
* **Standard Vehicle Trajectories & Parking Logs:** Automated purge after **30 days** via PostgreSQL partitioned table drops (`DROP PARTITION`).
* **Non-Incident Video Footage:** Automated deletion by MediaMTX / MinIO lifecycle rules after **30 days**.
* **Incident Evidence:** Locked under cryptographic hold for **180 days** or until legal disposal order.
* **Right to Erasure (DPDP Act Compliance):** The `access_service.py` provides an audited administrative endpoint `/api/v1/privacy/purge-citizen-records` that purges all associated plate sightings and tracking history across database tables upon statutory authorization.

---

## 5. Security & Access Control (RBAC Integration)

Access to AI-derived forensic data is governed by SARVANETRA's Zero-Trust RBAC:
* **Viewer / Guard:** Can view live video streams and aggregate crowd density metrics. Zero access to raw ANPR logs or identity queries.
* **Parking Operator:** Access to parking slot counts and real-time gate validation. Cannot query historical citizen movement paths.
* **Law Enforcement Officer:** Full search access to ANPR and Watchlist matches upon entry of a valid Police Station Case Dairy Number (FIR Number).
* **Forensic Auditor / Super Admin:** Read-only access to immutable audit logs; dual-authorization required for forensic identity exports.

All queries against ANPR and face watchlists record the querying operator's user ID, IP address, timestamp, and judicial justification in `evidence_audit_logs`.
