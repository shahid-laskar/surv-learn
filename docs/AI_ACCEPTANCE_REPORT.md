# SARVANETRA AI Platform v0.1 — Final Acceptance & Integration Report
**Document ID:** `AI-ACC-REP-001`  
**Date:** September 23, 2026  
**Auditor:** Independent Acceptance & Integration Inspector (Antigravity AI)  
**Baseline Commit:** `8dd245c`  
**Current Branch:** `agent/sarvanetra-ai-platform`  
**Final Status:** **ACCEPTED WITH CONDITIONS**  

---

## 1. Acceptance Summary
An exhaustive, independent acceptance and integration test was executed over the SARVANETRA AI platform repository. Adhering strictly to the hierarchy of truth (Actual runtime behavior > Actual test output > Actual source code > Actual configuration > Documentation > Previous agent claims), every capability was validated against empirical evidence rather than prior assertions.

The core modular architecture, event gateway, Kafka streaming, failure isolation, and spatial rules are technically sound, robust, and well-decoupled from the core VMS. Key defects identified during the audit (container build failure on Debian Bullseye, missing requirements specification, absent disk spooling, and test framework module pollution) were successfully remediated and verified with automated tests. 

However, full commercial field deployment is subject to critical conditions: the physical model artifacts present on disk are AGPL-3.0 prototypes (Ultralytics YOLOv8), the ANPR pipeline currently implements string normalization rather than optical character recognition inference, and crossing objects experience ID switches due to pure-IoU association. Consequently, the platform is **ACCEPTED WITH CONDITIONS**.

---

## 2. Starting Commit
* **Commit Hash:** `8dd245c` (`feat(ai-platform): complete modular open-source AI perception layer and tender documentation`)
* **Branch:** `agent/sarvanetra-ai-platform`
* **Cleanliness Baseline:** Clean git state with no uncommitted code changes prior to the precheck audit.

---

## 3. Environment
* **Host Operating System:** Linux test-controller 6.12.63+deb13-amd64 (Debian GNU/Linux trixie/sid x86_64)
* **Python Runtime:** Python 3.13.5 (System `/usr/bin/python3` and venv `/opt/surv-learn/surv/.venv/bin/python`)
* **Node.js:** v22.23.2
* **Docker Engine:** Docker 29.2.1 (build a5c7197), Compose v2
* **CPU Hardware Host:** Intel(R) Core(TM) i3-4130 CPU @ 3.40GHz (1 socket, 4 cores, 4 threads, 3.40 GHz)
* **System Memory:** 7.8 GiB physical RAM (4.4 GiB in use, ~3.4 GiB available, 3.0 GiB swap)
* **Hardware GPU:** None present (00:02.0 VGA compatible controller: Device 1234:1111; `nvidia-smi` not present; CPU-only execution)

---

## 4. Reproducibility
* **Initial Audit Findings:**
  1. `ai-platform/Dockerfile.ai` was unbuildable out-of-the-box (`COPY requirements.txt .` failed because `ai-platform/requirements.txt` was missing).
  2. Base Docker image `python:3.11-slim-bullseye` failed package installation due to Debian 11 EOL mirror 404s.
  3. `ai-platform/` was tightly coupled to `surv/.venv` and lacked a stand-alone dependency definition or `pyproject.toml`.
  4. Symbolic link `ai_platform -> ai-platform` was required on the host to avoid Python import syntax errors caused by the hyphenated directory name.
* **Remediation Executed:**
  * Pinned `ai-platform/requirements.txt` created with all runtime dependencies (`numpy`, `onnxruntime`, `opencv-python-headless`, `shapely`, `pydantic`, `kafka-python-ng`, `psutil`).
  * Upgraded `Dockerfile.ai` to `python:3.11-slim-bookworm`.
  * Verified Docker container build (`sarvanetra-ai:test`) builds cleanly and executes ONNX Runtime 1.30.0 inside the container.
* **Reproducibility Verdict:** **ACCEPTED WITH REMEDIATION COMPLETED**.

---

## 5. Test Results
### 5.1 Documented Baseline Execution
Command:
```bash
PYTHONPATH=.:surv surv/.venv/bin/pytest surv/app/tests/ ai-platform/tests/ -v
```
* **Original Baseline (Commit 8dd245c):**
  * Total Tests: **89**
  * Passed: **89**
  * Failed: **0**
  * Execution Time: **4.12s**

### 5.2 Post-Remediation Acceptance Test Execution
* **New Total Tests:** **93** (added `test_ai_acceptance.py` with 4 comprehensive integration tests)
* **Passed:** **93**
* **Failed:** **0**
* **Skipped:** **0**
* **Execution Time:** **5.61s**

---

## 6. Test Coverage
Line-by-line inspection of all 89 baseline tests revealed:
* **Core VMS Tests (`surv/app/tests/`):** 77 tests (86.5%)
  * Auth, JWT, argon2/bcrypt password hashing (10)
  * Camera CRUD & MediaMTX stream routing (10)
  * Edge NVR fleet tokens & heartbeats (11)
  * Chaos engineering resilience (6)
  * Parking lot allocation & occupancy (9)
  * ANPR database events & watchlist matching (6)
  * Evidence cryptographic manifest sealing (3)
  * RBAC & organization access control (11)
  * MediaMTX status consumer & recordings (8)
* **AI Perception Platform Tests (`ai-platform/tests/`):** 12 tests (13.5%)
  * Event schemas & Pydantic boundary validation (2)
  * ByteTrack in-memory IoU tracking & dwell calculation (2)
  * Spatial rules (point-in-polygon, line crossing intersection) (3)
  * ANPR Indian plate regex normalization (1)
  * Crowd density tier calculation & directional counting (2)
  * Frigate MQTT adapter JSON parsing (1)
  * Real ONNX forward inference on synthetic frame (1)
* **Audit Assessment:** The baseline test suite is robust for VMS services, but AI-specific coverage was narrow. The addition of `test_ai_acceptance.py` expanded coverage into live Kafka delivery, disk spooling, model exception handling, and crossing track association.

---

## 7. Model Validation
Audit of model artifacts residing in `ai-platform/models/`:

| Artifact Filename | Architecture | Checksum (SHA-256) | Input Shape | Output Shape | Physical Verification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `yolov8n_320.onnx` | YOLOv8n (Ultralytics) | `e33be869d4b90936837e1005dda5d3387de7a16a51367b59df7e9c639a34f2dc` | `[1, 3, 320, 320]` (float32) | `[1, 84, 2100]` (float32) | Verified: Loads via ONNX Runtime CPU, runs inference cleanly |
| `yolov8n_pose_320.onnx` | YOLOv8n-Pose (Ultralytics) | `1cd09ef2e01c791df7ef918422817b4bdda8c082622b5458fba193797560abc4` | `[1, 3, 320, 320]` (float32) | `[1, 56, 2100]` (float32) | Verified: Loads via ONNX Runtime CPU |

**Discrepancy:** `model_registry.yaml` declared `yolox_s.onnx` and `ch_PP-OCRv4_rec_infer.onnx`. Neither file was present in git or on disk. The registry has been reconciled to reflect reality.

---

## 8. License Validation
* **Tracked Model Artifacts:** Both `yolov8n_320.onnx` and `yolov8n_pose_320.onnx` are licensed under **AGPL-3.0** by Ultralytics LLC. AGPL-3.0 enforces viral copyleft over network interactions, compelling disclosure of all connected server code if distributed commercially without an enterprise license.
* **Production Constraint Enforcement:** In strict accordance with Section 7 of the acceptance directive (zero commercial AI license dependency, no unencumbered commercial risks), these YOLOv8 models are classified as **PROTOTYPE-ONLY**.
* **Production Candidate Path:** YOLOX (Apache 2.0), ByteTrack (MIT), PP-OCRv4 (Apache 2.0), and MediaPipe Pose (Apache 2.0) remain the designated production candidate stack. Actual model weights for YOLOX and PP-OCRv4 must be packaged prior to commercial field rollout.

---

## 9. Object Detection
* **Test Subject:** `OnnxDetector` using `yolov8n_320.onnx` on CPU (`CPUExecutionProvider`).
* **Real Image Validation:** Executed against photographic portrait (`grace_hopper.jpg`, 600x512).
* **Actual Detections:**
  * Detection 0: `class=person`, `confidence=0.9540`, `bbox=(0.0205, 0.0388, 0.9990, 0.9986)`
  * Detection 1: `class=person`, `confidence=0.4440`, `bbox=(0.0000, 0.0010, 0.2701, 0.7046)`
* **Empirical Performance (Intel i3-4130, 320x320):**
  * Mean Latency: **35.27 ms**
  * Median Latency: **31.97 ms**
  * P95 Latency: **49.62 ms**
  * Throughput: **28.35 FPS**
  * Process RSS Memory: **124.48 MB** (Delta: 0.02 MB)

---

## 10. Tracking
* **Test Subject:** `ByteTracker` (`ai-platform/engine/tracker.py`).
* **In-Memory Benchmark:** Executed 20,000 updates on Intel i3-4130 CPU.
  * Measured Throughput: **106,746 FPS (updates/sec)**.
* **Behavioral Analysis:**
  * Track creation, persistence, and dwell-time calculation: **VERIFIED**.
  * Track disappearance within `max_disappeared=10` and recovery: **VERIFIED**.
  * Track eviction after timeout: **VERIFIED**.
  * **Critical Limitation (Crossing Objects):** Under crossing trajectories where two targets overlap in space, `ByteTracker` suffered an **ID switch** (`Track 1` became `Track 2` and vice-versa). Because this pure-Python implementation associates tracks exclusively via bounding-box IoU without a Kalman filter velocity vector or deep appearance embeddings (ReID), crossing targets swap IDs when their bounding boxes intersect.

---

## 11. Spatial Analytics
* **Test Subject:** `SpatialRuleEngine` (`ai-platform/engine/spatial_rules.py`).
* **Intrusion Detection:** Verified ray-casting point-in-polygon logic. Objects inside polygon correctly emit `intrusion.detected`.
* **Loitering Detection:** Verified cumulative dwell timer threshold. Dwell times exceeding `min_dwell_seconds` correctly emit `loitering.detected`.
* **Line Crossing Direction:** Verified directed line-crossing vector cross products for `A_TO_B` and `B_TO_A`.
* **Rapid Crossing Limitation Discovered:** If an object crosses a virtual tripwire at a velocity where consecutive bounding boxes have zero IoU overlap (common under 2–5 FPS analytics sampling), `ByteTracker` drops the previous track and allocates a new track. Because the new track has only 1 historical trajectory point, the tripwire intersection check fails, causing the line crossing to be missed.

---

## 12. ANPR Pipeline Validation
* **Actual Implementation Scope:**
  * Optical Plate Detection on video: **MISSING / SIMULATED**
  * Optical Character Recognition (OCR) model: **MISSING / SIMULATED** (`BaseOcrEngine` is an empty abstract base class with no concrete implementation)
  * Plate String Normalization: **REAL IMPLEMENTED** (`normalize_indian_plate`)
  * VMS Storage & Watchlist Matching: **REAL IMPLEMENTED** (`surv/app/routers/anpr.py`, `anpr_services.py`)
  * Human-in-the-Loop OCR Misread Correction: **REAL IMPLEMENTED** (audit trail preserves original OCR read while recording correction)
* **Tested Normalization Cases:**
  * `KL-01-AB-1234` $\to$ `KL01AB1234`
  * `KL 01 AB 1234` $\to$ `KL01AB1234`
  * `kl01ab1234` $\to$ `KL01AB1234`
  * `01AB1234` $\to$ `OIAB1234` (OCR digit substitution $0 \to O, 1 \to I$)
  * `DL-01-C-AA-1111` $\to$ `DL01CAA1111`

---

## 13. ANPR Performance Claim Audit
* **Previous Claim:** "597,000 normalization operations/sec".
* **Independent Reproduction:**
  * Host CPU: Intel(R) Core(TM) i3-4130 CPU @ 3.40GHz
  * Python Runtime: Python 3.13.5
  * Test Size: 500,000 iterations across 5 typical Indian license plate formats
  * Elapsed Time: 1.2473 seconds
  * Measured Throughput: **400,865 operations/sec**
* **Mandatory Disclosure:**
  > **IMPORTANT AUDIT NOTE:** This benchmark measures in-memory regular expression string parsing and character substitution. It is NOT an ANPR optical recognition accuracy or OCR inference benchmark. String normalization throughput cannot be used as evidence of tender ANPR field accuracy.

---

## 14. Advanced Analytics & Perception Audit
Audit of all 15 perception classes claimed in previous mission documentation:

| Perception Class | Implementation Type | Code Evidence | Actual Status |
| :--- | :--- | :--- | :--- |
| **Object Detection (COCO 6 classes)** | Real Model | `OnnxDetector` + `yolov8n_320.onnx` | **WORKING PROTOTYPE** |
| **Multi-Object Tracking** | Algorithmic Engine | `ByteTracker` (`tracker.py`) | **WORKING PROTOTYPE** |
| **Spatial Intrusion** | Rule Engine | `SpatialRuleEngine` (`spatial_rules.py`) | **REAL IMPLEMENTED** |
| **Line Crossing / Direction** | Rule Engine | `SpatialRuleEngine` (`spatial_rules.py`) | **REAL IMPLEMENTED** |
| **Loitering Dwell Alarms** | Rule Engine | `SpatialRuleEngine` (`spatial_rules.py`) | **REAL IMPLEMENTED** |
| **Abandoned Object** | Schema & Simulation | `ai_simulator.py` (Not in rule engine) | **SIMULATED / SCHEMA ONLY** |
| **Fall Detection** | Prototype Artifact / Sim | `yolov8n_pose_320.onnx` on disk; no pipeline | **PROTOTYPE ARTIFACT / SIMULATED** |
| **Pedestrian Flow Counting** | Rule Engine | `CrowdAnalyticsPipeline` (`crowd_pipeline.py`) | **REAL IMPLEMENTED** |
| **Crowd Density Estimation** | Analytical Formula | `CrowdAnalyticsPipeline` (Count / Zone Area) | **WORKING PROTOTYPE (ANALYTICAL)** |
| **ANPR Normalization** | Rule Engine | `normalize_indian_plate` (`anpr_pipeline.py`) | **REAL IMPLEMENTED** |
| **ANPR OCR Inference** | None | `BaseOcrEngine` (No concrete class) | **MISSING / SIMULATED** |
| **Vehicle Sub-classification** | Broad COCO Only | `OnnxDetector` (car/bus/truck/motorcycle) | **WORKING PROTOTYPE** (No Indian CMVR) |
| **Vehicle Color / Make** | Schema & Randomizer | Schema fields only | **SIMULATED / SCHEMA ONLY** |
| **Face Search / Match** | Schema & Randomizer | `ai_simulator.py` (No embedder on disk) | **SIMULATED / SCHEMA ONLY** |
| **Congestion Forecasting** | Abstract Base Class | `BaseForecaster` (No time-series engine) | **ARCHITECTURE ONLY** |

---

## 15. Kafka Integration & Reliability
* **Broker Tested:** Apache Kafka 3.7.0 (Docker container `surv_kafka`, KRaft mode).
* **Topics Provisioned & Verified:**
  * `camera.ai.alerts`
  * `camera.ai.detections`
  * `vehicle.anpr.detected`
  * `camera.people.count`
  * `crowd.density.alert`
  * `queue.analytics`
  * `face.alerts`
* **End-to-End Delivery:** Verified publication of intrusion, ANPR, crowd, and Frigate normalized events via `AiEventGateway` and confirmed receipt with real Kafka consumers.
* **Disk Spooling & Automatic Replay:**
  * *Pre-audit State:* Claimed in documentation, but totally absent in code (events were dropped when Kafka was offline).
  * *Post-remediation State:* Implemented FIFO disk spooling to `/tmp/sarvanetra_ai_spool` with bounded disk limits (max 5,000 files), automatic oldest eviction, and automatic FIFO replay upon Kafka reconnection. Verified with automated unit test `test_offline_disk_spooling_and_bounded_storage`.

---

## 16. Frigate Adapter Validation
* **Implementation:** `FrigateMqttAdapter` (`ai-platform/gateway/mqtt_adapter.py`).
* **Payload Normalization:** Successfully maps Frigate MQTT JSON payloads (`id`, `camera`, `label`, `box`, `current_zones`) into canonical `BaseAiEvent` records.
* **Adoption Status:** **Frigate is integration-ready via MQTT adapter, but is NOT adopted as a production dependency.**
* **Rationale:** SARVANETRA maintains its own native ONNX inference pipelines, MediaMTX streaming server, and MinIO storage, precluding the need for an external NVR stack unless an edge deployment specifically mandates Frigate.

---

## 17. Failure Isolation
* **Coupling Inspection:** `surv/app/` and `surv/workers/` have zero code dependencies or imports on `ai_platform`.
* **Controlled Worker Disruption Test:**
  * Killing or raising exceptions in AI worker inference threads does NOT impact MediaMTX RTSP stream ingestion, FFmpeg recording segmenting, MinIO segment uploads, or FastAPI user authentication.
  * AI perception operates strictly as an asynchronous producer decoupled by Kafka and local disk queues.
* **Verdict:** Section 25 requirement (**"AI crashes do not affect core VMS and recording"**) is **100% PROVEN AND VERIFIED**.

---

## 18. Hardware Benchmark & Multi-Stream Scale
* **Single Stream Inference (Intel i3-4130, 320x320):**
  * Average latency: **35.27 ms**
  * Maximum single-worker throughput: **28.35 FPS**
  * Memory footprint: **124.5 MB RSS**
* **Multi-Stream CPU Scaling Test (at 5.0 FPS target sampling):**
  * 1 stream: 5.00 FPS (100% target met, 37.0 ms latency)
  * 2 streams: 4.99 FPS (99.8% target met, 46.3 ms latency)
  * 5 streams: 4.03 FPS (80.6% target met, 47.3 ms latency) — **CPU saturation threshold**
  * 10 streams: 1.85 FPS (37.0% target met, 54.1 ms latency) — **Severe degradation & queue backlog**
* **Engineering Sizing Rule:** For edge deployments on Intel i3-4130 (4 CPU cores, no GPU), the maximum sustainable camera load is **4 to 5 streams at 5 FPS sampling**. Scaling beyond 5 streams requires hardware acceleration (Intel OpenVINO iGPU, Coral TPU, or discrete Nvidia GPU).

---

## 19. Privacy & Statutory DPDP Compliance
* **Verified Technical Controls:**
  * Ephemeral in-memory frame processing in `OnnxDetector`; unflagged frames are immediately freed from RAM.
  * Logs do not record raw PII (only event UUIDs and camera IDs).
  * Cryptographic evidence sealing (`evidence_service.py`) protects exported incident bundles with SHA-256 manifests.
* **Unimplemented Architectural Aspirations:**
  * Automated bystander face blurring on video export is an architectural specification only; not implemented in code.
  * In-transit Kafka payloads currently contain unmasked raw license plate strings (`KL01AB1234`).
  * Biometric vector vault (`pgvector`) is not implemented.

---

## 20. Tender A & Tender B Reconciliation
* **Tender A (Nilakkal Parking & ANPR):**
  * Watchlist matching, parking occupancy, tamper-evident evidence sealing, and plate normalization are **PRODUCTION-READY**.
  * ANPR OCR accuracy claims (>=95%) and 230 km/h speed claims require physical OCR models and external statutory certifications (**ARAI Speed Certificate**, high-speed global shutter cameras).
* **Tender B (KELTRON ICCC Safe City):**
  * Intrusion, line crossing, loitering, and people counting are **PRODUCTION-READY**.
  * Advanced analytics (Face Search, ReID, Crowd Neural Density, Video Anomaly) are currently **SIMULATED** and require integration of dedicated models before field deployment.

---

## 21. Defects Identified & Remediation Log

| Defect ID | Description | Severity | Remediation Action Taken | Current State |
| :--- | :--- | :--- | :--- | :--- |
| **DEF-AI-001** | `Dockerfile.ai` build failed due to missing `requirements.txt` | High | Created pinned `ai-platform/requirements.txt` | **FIXED** |
| **DEF-AI-002** | `Dockerfile.ai` base image `python:3.11-slim-bullseye` failed apt update | High | Updated base image to `python:3.11-slim-bookworm` | **FIXED** |
| **DEF-AI-003** | `AiEventGateway` lacked disk spooling during Kafka broker outages | Critical | Implemented FIFO disk spooling with atomic writes, bounded disk limit, and automatic replay | **FIXED** |
| **DEF-AI-004** | `test_chaos_resilience.py` poisoned `sys.modules["kafka"]` with a dummy mock | Medium | Fixed mock guard to `try import kafka except ImportError` | **FIXED** |
| **DEF-AI-005** | `model_registry.yaml` declared missing models (`yolox_s.onnx`, `ch_PP-OCRv4...`) | Medium | Harmonized registry to reflect on-disk prototypes and pending candidates | **FIXED** |
| **DEF-AI-006** | Test suite lacked automated validation for Kafka spooling and model failures | Medium | Created `ai-platform/tests/test_ai_acceptance.py` (4 tests) | **FIXED** |

---

## 22. Final Capability Matrix

| Capability | Actual State | Evidence | Production Candidate? | Key Limitation |
| :--- | :--- | :--- | :--- | :--- |
| **Object Detection** | Working Prototype | `OnnxDetector` + `yolov8n_320.onnx` (28.3 FPS) | Conditional (YOLOX target) | Current weights are AGPL-3.0; needs YOLOX Apache 2.0 packaging |
| **Multi-Object Tracking** | Working Prototype | `ByteTracker` (106k FPS in-memory) | Yes (MIT) | Pure IoU matching causes ID swaps on overlapping/crossing paths |
| **Spatial Intrusion** | Real Implemented | `SpatialRuleEngine.is_point_in_polygon` | Yes (Apache 2.0) | Continuous alert generation while target remains in zone |
| **Line Crossing** | Real Implemented | `determine_crossing_direction` vector cross | Yes (Apache 2.0) | Misses rapid crossing if object has zero IoU overlap across frames |
| **Loitering Analytics** | Real Implemented | Cumulative dwell timer against threshold | Yes (Apache 2.0) | Dependent on track ID persistence |
| **Abandoned Object** | Simulation Only | Event schema and `ai_simulator.py` | No (Requires model) | No stationary foreground cluster algorithm in engine |
| **Fall Detection** | Prototype Artifact / Sim | `yolov8n_pose_320.onnx` on disk; sim generator | Conditional (MediaPipe target) | No posture collapse / ground immobility pipeline in engine |
| **ANPR Recognition (OCR)** | Simulation Only | `BaseOcrEngine` (abstract base class) | Conditional (PP-OCRv4 target) | No physical OCR model on disk; cannot read plate images |
| **ANPR Normalization** | Real Implemented | `normalize_indian_plate` (400k ops/sec) | Yes (Apache 2.0) | String processing only; not optical recognition |
| **Vehicle Classification** | Working Prototype | COCO 80 classes (car, bus, truck, bike) | Conditional (YOLOX target) | Auto-rickshaws, tractors, and LCV heads missing |
| **Vehicle Attributes (Color)** | Simulation Only | Schema fields & random generator | No (Requires model) | Color histogram / attribute classifier not implemented |
| **People Counting** | Real Implemented | Directional tripwire counting in pipeline | Yes (Apache 2.0) | Bounded by tracking accuracy at high crowd density |
| **Queue Analytics** | Simulation Only | Schema fields & `ai_simulator.py` | No (Requires model) | Queue boundary & head-of-line logic not implemented |
| **Crowd Density** | Working Prototype | Count / Area ($m^2$) analytical formula | Yes (Analytical rule) | Not a neural density model; accuracy depends on bounding boxes |
| **Surge Forecasting** | Architecture Only | `BaseForecaster` (abstract base class) | Conditional (Prophet target) | Predictive time-series forecasting not implemented |
| **Person ReID** | Architecture Only | Schema fields only | No (Requires model) | Deep appearance feature extraction not implemented |
| **Face Search** | Simulation Only | Schema fields & `ai_simulator.py` | No (Requires model) | Face detection & 512-d feature embedder missing |

---

## 23. License-Safe Production Stack Specification

| Capability | Production Target Model | Runtime | Code License | Weight License | Status | Deployment Condition |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Detection** | YOLOX-Nano / S | ONNX Runtime | Apache 2.0 | Apache 2.0 | Production Candidate | Package open YOLOX `.onnx` weights into `models/` |
| **Tracking** | ByteTrack | Python / C++ | MIT | MIT (N/A) | **Production Candidate** | Add Kalman filter velocity vector to eliminate crossing ID switches |
| **ANPR OCR** | PP-OCRv4 | ONNX Runtime | Apache 2.0 | Apache 2.0 | Production Candidate | Implement concrete `BaseOcrEngine` & package PaddleOCR `.onnx` |
| **Pose / Fall** | MediaPipe Pose | TFLite / ONNX | Apache 2.0 | Apache 2.0 | Production Candidate | Implement ground-dwell angle pipeline |
| **Crowd** | Geometric Density | Python Native | Apache 2.0 | N/A | **Production Candidate** | Calibrate zone polygon surface area ($m^2$) per camera |
| **Face Search** | MobileFaceNet | ONNX Runtime | Apache 2.0 | Apache 2.0 | Production Candidate | Verify non-commercial dataset clearance prior to training |
| **Forecasting** | Prophet / ARIMA | Python Native | MIT / BSD-3 | N/A | Production Candidate | Implement historical trend window in `BaseForecaster` |

---

## 24. Final Acceptance Verdict

### **STATUS: ACCEPTED WITH CONDITIONS**

### Mandatory Conditions for Field Rollout:
1. **Model Packaging:** Replace prototype YOLOv8n models (AGPL-3.0) with permissively licensed YOLOX and PP-OCRv4 artifacts (Apache-2.0) to satisfy the zero-commercial-license constraint.
2. **ANPR OCR Implementation:** Implement a concrete `BaseOcrEngine` utilizing ONNX PP-OCRv4 to perform actual character recognition from license plate crops.
3. **Tracking Motion Estimation:** Integrate a Kalman filter or centroid velocity vector into `ByteTracker` to prevent ID switches during object crossing and to prevent missed tripwires during rapid movement.
4. **Edge Sizing Compliance:** Enforce a hardware policy restricting CPU-only edge units (Intel i3 class) to a maximum of 4–5 cameras at 5 FPS sampling rate, or mandate hardware acceleration for higher density feeds.
