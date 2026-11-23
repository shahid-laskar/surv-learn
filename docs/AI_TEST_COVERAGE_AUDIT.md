# SARVANETRA AI Platform v0.1 — Test Coverage Audit
**Document ID:** `AI-COV-001`  
**Date:** September 23, 2026  
**Auditor:** Independent Acceptance & Integration Inspector  
**Baseline Commit:** `8dd245c`  

---

## 1. Executive Summary
The previous mission reported a baseline of **89 automated tests**. This audit inspects what those 89 tests actually execute and verifies whether they represent genuine automated validation of the AI platform or conflate platform VMS tests with AI perception tests.

### Key Finding: **86.5% of Baseline Tests are Core VMS Tests, NOT AI Tests**
* **Total Tests in Baseline:** 89
* **Core VMS Tests (`surv/app/tests/`):** 77 tests (86.5%)
* **AI Perception Platform Tests (`ai-platform/tests/`):** 12 tests (13.5%)

While the core VMS tests are valuable and rigorous (covering authentication, camera management, edge fleet heartbeats, tamper-evident cryptographic sealing, and chaos engineering), the AI perception platform itself has only **12 automated tests**.

---

## 2. Comprehensive Test Taxonomy & Classification

| Test Suite / Module | Count | Primary Category | Secondary Category | Actual Target of Test |
| :--- | :--- | :--- | :--- | :--- |
| `test_access_enforcement.py` | 3 | Security | Unit | RBAC camera access policy enforcement |
| `test_access_service.py` | 4 | Security | Integration | Organization subtree hierarchy and scoping |
| `test_acl_sync.py` | 4 | Security | Integration | Headscale mesh VPN ACL rules generation |
| `test_anpr.py` | 6 | Integration | Database / Service | Core VMS ANPR event storage & watchlist hit |
| `test_auth.py` | 10 | Security | Unit | JWT encoding, Argon2/Bcrypt hash, session revocation |
| `test_cameras.py` | 10 | Integration | MediaMTX | RTSP URL parsing, stream route add/delete |
| `test_chaos_resilience.py` | 6 | Failure / Chaos | Integration | Kafka outage fallback, camera flapping, DB rollback |
| `test_evidence.py` | 3 | Security | Cryptography | SHA-256 manifest sealing, tamper detection |
| `test_fleet.py` | 11 | Integration | Edge NVR | Site secret tokens, heartbeat, backup clip upload |
| `test_incidents.py` | 4 | Unit | Business Logic | Incident workflow state transitions |
| `test_parking.py` | 9 | Unit / Integration | Service | Parking zone allocation, occupancy tracking |
| `test_recordings.py` | 3 | Unit | Storage | HLS recording timeline segmentation query |
| `test_status_consumer.py` | 3 | Kafka | Integration | Camera online/offline status event consumption |
| `test_ai_platform.py` | 12 | AI Platform | Unit / Inference | AI schemas, tracker, spatial rules, ANPR regex, ONNX |
| **TOTAL** | **89** | — | — | **All 89 Passed (4.12s)** |

---

## 3. Deep-Dive Audit of AI Platform Tests (`ai-platform/tests/`)

The 12 AI perception tests in `ai-platform/tests/test_ai_platform.py` were audited line-by-line:

| Test Name | Genuine Assertions | Superficial / Limitation Identified |
| :--- | :--- | :--- |
| `test_ai_event_schema_serialization` | Asserts Pydantic serialization, required fields (`event_id`, `timestamp`, `confidence`), ISO 8601 formatting. | Tested with mock dict; does not test schema migration or schema evolution. |
| `test_ai_event_schema_invalid_confidence` | Asserts validation error when `confidence = 1.5` or `< 0.0`. | Genuine schema boundary validation. |
| `test_iou_calculation` | Asserts overlapping box IoU ($0.52$) and disjoint box IoU ($0.0$). | Pure math unit test; genuine. |
| `test_bytetrack_id_persistence_and_dwell` | Simulates 5 sequential detection frames; asserts track ID persistence (ID 1) and dwell time accumulation. | High-level simulation; does not test track fragmentation or occlusions. |
| `test_point_in_polygon` | Tests interior point, exterior point, and edge point against rectangle polygon. | Pure geometric algorithm; genuine. |
| `test_line_intersection` | Tests crossing and parallel line segments. | Pure vector math; genuine. |
| `test_spatial_rule_engine_intrusion_and_loitering` | Configures intrusion zone and loitering zone; pushes simulated detections; asserts alert generation. | Genuine logic verification of polygon rule engine. |
| `test_indian_license_plate_normalization` | Tests 6 plate variations (`KL 01 AB 1234`, `DL-01-C-AA-1111`, etc.); asserts space removal and OCR confusion corrections ($O \to 0, I \to 1$). | **String processing only.** Does NOT test OCR recognition or plate image inference. |
| `test_crowd_density_and_congestion_levels` | Evaluates crowd density formula ($\text{count} / \text{area}$) across tiers (LOW, MEDIUM, HIGH, CRITICAL). | Pure formula test; genuine. |
| `test_people_counting_flow` | Simulates crossing tripwires in directions A-to-B and B-to-A; asserts in/out counter increments. | Genuine tracking logic. |
| `test_frigate_mqtt_normalization` | Passes Frigate MQTT JSON string; asserts conversion to canonical `BaseAiEvent` with bounding box. | Genuine JSON adapter parsing test. |
| `test_real_onnx_detector_inference` | Loads `models/yolov8n_320.onnx`; executes forward inference on synthetic zero-filled image `np.zeros((320, 320, 3), dtype=np.uint8)`. | Genuine ONNX runtime loading & forward pass; however, input is all-black synthetic frame, not real video/image with detectable objects. |

---

## 4. Gaps in Test Coverage (AI Perception Platform)

1. **No Real Dataset / Ground Truth Testing:** No tests evaluate precision, recall, or mAP against real CCTV frames or benchmark video clips.
2. **Missing Real ANPR Inference Tests:** No test executes a real plate detection model or OCR engine (PP-OCRv4) against license plate images.
3. **Missing Live Kafka Tests:** `test_ai_platform.py` does not test live event publication to an actual running Kafka broker.
4. **Missing Disk Spooling & Circuit Breaker Tests:** The event gateway claim of disk spooling during broker disconnect is completely untested in the AI test suite.
5. **Missing Pose / Fall Model Tests:** Although `yolov8n_pose_320.onnx` is present in `ai-platform/models/`, there is no test exercising it.
6. **No Multi-Stream Concurrency Tests:** The 12 tests run sequentially in single-threaded Python.

---

## 5. Summary & Verdict
The reported 89 tests do pass and verify fundamental building blocks. However, representing this suite as "89 AI platform tests" is misleading. The AI platform itself is tested by 12 unit tests. To achieve high confidence, acceptance validation must execute dedicated integration tests for real inference, Kafka event delivery, failover, and hardware benchmarking.
