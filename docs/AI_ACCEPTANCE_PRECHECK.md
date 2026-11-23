# SARVANETRA AI Platform v0.1 — Acceptance Precheck Audit
**Document ID:** `AI-ACC-PRE-001`  
**Date:** September 23, 2026  
**Auditor:** Independent Acceptance & Integration Inspector (Antigravity AI)  
**Target Commit:** `8dd245c`  
**Target Branch:** `agent/sarvanetra-ai-platform`  

---

## 1. Executive Summary & Audit Mandate
This precheck audit establishes the ground truth of the SARVANETRA repository prior to any code modification, pursuant to Section 2 of `docs/final_acceptance_test.md`. Per the hierarchy of truth:
1. Actual runtime behavior
2. Actual test output
3. Actual source code
4. Actual configuration
5. Documentation
6. Previous agent claims

No code modifications were introduced prior to the completion of this precheck document.

---

## 2. Git & Version Control State

| Parameter | Observed Value | Status |
| :--- | :--- | :--- |
| **Current Commit** | `8dd245c` (`feat(ai-platform): complete modular open-source AI perception layer and tender documentation`) | Verified baseline |
| **Current Branch** | `agent/sarvanetra-ai-platform` | Verified |
| **Working Tree Cleanliness** | Clean (0 modified tracked files, 0 staged files) | Verified |
| **Untracked Files** | `docs/final_acceptance_test.md` (acceptance mission directive) | Verified clean baseline |
| **Tracked Symlinks** | `ai_platform -> ai-platform` (tracked symlink enabling Python import) | Verified |

---

## 3. Environment & Runtime Specifications

| Runtime / Tool | Exact Version | Details / Architecture |
| :--- | :--- | :--- |
| **Host Operating System** | Linux 6.12.63+deb13-amd64 | Debian GNU/Linux trixie/sid (x86_64) |
| **System Python** | Python 3.13.5 | `/usr/bin/python3` |
| **Venv Python** | Python 3.13.5 | `/opt/surv-learn/surv/.venv/bin/python` |
| **Node.js** | v22.23.2 | Global runtime |
| **Docker Engine** | Docker version 29.2.1, build a5c7197 | Client and daemon operational |
| **Docker Compose** | Docker Compose version v2 | Integrated with Docker CLI |

---

## 4. Hardware Host Profile

| Component | Specification | Reality Check vs Previous Claim |
| :--- | :--- | :--- |
| **Processor (CPU)** | Intel(R) Core(TM) i3-4130 CPU @ 3.40GHz | Identical to reported host (i3-4130) |
| **Cores / Threads** | 4 logical CPU units (1 socket, 1 thread/core, 4 vCPUs allocated) | Verified |
| **Memory (RAM)** | 7.8 GiB Total (4.4 GiB used, ~3.4 GiB available, 3.0 GiB swap) | Matches reported 8 GB system |
| **Discrete GPU** | None detected (`00:02.0 VGA compatible controller: Device 1234:1111`, `nvidia-smi` not found) | Confirms CPU-only inference environment |

---

## 5. Test Suite Configuration Baseline

* **Pytest Version:** 9.1.1 (`pytest-asyncio` 1.4.0)
* **Reported Command:** `PYTHONPATH=.:surv surv/.venv/bin/pytest surv/app/tests/ ai-platform/tests/ -v`
* **Test Discovery Breakdown:**
  * Core VMS tests (`surv/app/tests/`): 77 tests
  * AI platform tests (`ai-platform/tests/`): 12 tests
  * Total tests collected: **89 items**
* **Baseline Execution Status:**
  * Passed: **89**
  * Failed: **0**
  * Skipped: **0**
  * Execution Time: **4.12s**

---

## 6. AI Model Artifacts & Checksums

Verification of all files residing in `ai-platform/models/`:

| Artifact Path | Format | Size | SHA-256 Checksum | Detected Architecture |
| :--- | :--- | :--- | :--- | :--- |
| `ai-platform/models/yolov8n_320.onnx` | ONNX | 12.7 MB (13,293,766 B) | `e33be869d4b90936837e1005dda5d3387de7a16a51367b59df7e9c639a34f2dc` | YOLOv8n (320x320 input, 80 COCO classes) |
| `ai-platform/models/yolov8n_pose_320.onnx` | ONNX | 13.1 MB (13,717,678 B) | `1cd09ef2e01c791df7ef918422817b4bdda8c082622b5458fba193797560abc4` | YOLOv8n-Pose (320x320 input, keypoints) |

### Discrepancy Note on Model Registry:
`ai-platform/config/model_registry.yaml` lists:
1. `models/yolox_s.onnx` (sha256: `9f86d08188...`) — **FILE NOT PRESENT ON DISK**
2. `models/ch_PP-OCRv4_rec_infer.onnx` (sha256: `5e884898da...`) — **FILE NOT PRESENT ON DISK**

Only the YOLOv8n models are present on disk. YOLOv8 is subject to Ultralytics AGPL-3.0 licensing terms, classifying it as `PROTOTYPE-ONLY` per `AI_MODEL_LICENSE_MATRIX.md`.

---

## 7. AI & Kafka Configuration Review

### 7.1 AI Platform Configuration Files
* `ai-platform/config/camera_analytics.yaml`: Defines per-camera analytics pipelines for 3 cameras (`CAMKRTVM0001`, `CAM_NILAKKAL_GATE1`, `CAM_PAMPA_TREK01`) covering intrusion polygons, tripwires, loitering zones, ANPR thresholds, and crowd density parameters.
* `ai-platform/config/model_registry.yaml`: Declarative catalog of models, frameworks, target tasks, and licensing attributes.

### 7.2 Kafka Configuration
* **Broker Host / Port:** `surv_kafka:9092` (Docker internal) / `localhost:9092` (Host mapping via `${KAFKA_PORT}`)
* **Topic Routing Table (`ai-platform/gateway/event_gateway.py`):**
  * `vehicle.anpr.detected` $\rightarrow$ `vehicle.anpr.detected`
  * `vehicle.classified` $\rightarrow$ `vehicle.anpr.detected`
  * `intrusion.detected` $\rightarrow$ `camera.ai.alerts`
  * `line_crossing.detected` $\rightarrow$ `camera.ai.alerts`
  * `loitering.detected` $\rightarrow$ `camera.ai.alerts`
  * `abandoned_object.detected` $\rightarrow$ `camera.ai.alerts`
  * `fall.detected` $\rightarrow$ `camera.ai.alerts`
  * `person.detected` $\rightarrow$ `camera.ai.detections`
  * `person.counted` $\rightarrow$ `camera.people.count`
  * `crowd.density.updated` $\rightarrow$ `crowd.density.alert`
  * `queue.updated` $\rightarrow$ `queue.analytics`
  * `face.match.detected` $\rightarrow$ `face.alerts`

---

## 8. Docker Infrastructure & Services Inventory

The repository defines services across multiple Compose files:
* Core compose: `surv/docker-compose.yml`
* Services defined:
  1. `postgres` (PostgreSQL 16)
  2. `redis` (Redis 7)
  3. `headscale` (Mesh VPN control plane)
  4. `caddy` (Reverse proxy & TLS termination)
  5. `derp` (Tailscale DERP relay)
  6. `tailscale` (VPN client node)
  7. `kafka` (Apache Kafka 3.7.0, KRaft mode)
  8. `kafka_init` (Topic bootstrap provisioner)
  9. `kafka_ui` (Kafka web management UI)
  10. `minio` (S3 object storage)
  11. `mediamtx` (RTSP/WebRTC/HLS streaming server)
  12. `nginx_hls` (HLS proxy and static assets)
  13. `frontend` (React SPA)
  14. `app` (FastAPI core backend)
  15. `db_migrate` (Alembic runner)
  16. `segment_consumer` (MinIO segment indexing worker)
  17. `onvif_producer` (ONVIF event polling worker)
  18. `motion_consumer` (Motion alarm processing worker)
  19. `status_monitor` (MediaMTX stream health monitor)
  20. `status_consumer` (Camera status event worker)
  21. `minio_cleaner` (Retention policy lifecycle worker)
* **AI Service Container Status:** `ai-platform/Dockerfile.ai` is provided in the repository, but **NOT** wired into `surv/docker-compose.yml`. Furthermore, `ai-platform/Dockerfile.ai` specifies `COPY requirements.txt .`, yet `ai-platform/requirements.txt` does not exist in `ai-platform/`.
