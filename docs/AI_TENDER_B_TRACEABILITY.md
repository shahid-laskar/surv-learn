# SARVANETRA — Tender B AI Requirements Traceability Matrix
**Document ID:** `AI-TRACEABILITY-TENDER-B`  
**Tender Reference:** KELTRON EOI AI-Based Surveillance Projects (Safe City / ICCC)  
**Scope:** Complete Traceability of Tender B Advanced Video Analytics, Crowd, and ICCC AI Primitives  
**Date:** September 23, 2026  
**Status:** Canonical Reference Specification  

---

## 1. Overview & Architecture Boundary

Tender B represents the large-scale Smart City / Safe City Integrated Command and Control Centre (ICCC) requirements issued by KELTRON. Unlike Tender A's focused parking and highway scope, Tender B mandates an extensive suite of city-scale artificial intelligence capabilities, including public safety spatial analytics, crowd dynamics, behavioral anomaly detection, multi-camera journey intelligence, and high-security access verification.

SARVANETRA decouples these workloads into dedicated, independent analytics workers running outside the VMS/MediaMTX core. Inference occurs via lightweight ONNX Runtime execution with standardized event dissemination via Kafka topics to the central ICCC incident correlation backend.

---

## 2. Tender B AI Traceability Matrix

| Capability Clause | Description | Candidate / Implemented Model | Runtime Engine | Kafka Event Contract | Kafka Topic | Backend Service & DB | Frontend / ICCC Element | Verification Test | Status |
|---|---|---|---|---|---|---|---|---|---|
| **Intrusion Detection** | Detection of unauthorized individuals or objects penetrating sensitive spatial perimeters | YOLOX-Nano (Apache 2.0) | ONNX Runtime (CPU/TensorRT) | `perimeter.intrusion.detected` (v1.0.0) | `surv.ai.events.spatial` | `surv/app/services/incident_service.py` -> `incidents` | Red polygon overlay on GIS map + flashing alert drawer | `test_spatial_rules_intrusion` | **PRODUCTION-CANDIDATE** |
| **Line Crossing / Direction** | Tripping virtual perimeter wires with bidirectional orientation tracking | ByteTrack + Vector Crossing Rule | Python / NumPy SIMD Math | `line_crossing.detected` (v1.0.0) | `surv.ai.events.spatial` | `surv/app/services/incident_service.py` -> `incidents` | Virtual tripwire vector render + direction arrow marker | `test_spatial_rules_line_crossing` | **PRODUCTION-CANDIDATE** |
| **Loitering Analytics** | Dwell-time monitoring exceeding configurable thresholds ($t > t_{thresh}$) in sterile zones | ByteTrack (Centroid & Dwell tracker) | Pure-Python ByteTrack tracker | `loitering.detected` (v1.0.0) | `surv.ai.events.spatial` | `incident_service.py` tracking cumulative dwell seconds | Dwell timer badge floating over tracked target box | `test_spatial_rules_loitering` | **PRODUCTION-CANDIDATE** |
| **Abandoned Object Detection** | Stationary unattended baggage/packages detected for $>30$ seconds with owner detachment | Background-Foreground sub-clustering + YOLOX-Nano | ONNX Runtime + Temporal state tracker | `abandoned_object.detected` (v1.0.0) | `surv.ai.events.spatial` | `incident_service.py` -> `incidents` (Severity: High) | Pulsing orange hazard halo + unattended duration clock | `test_abandoned_object_simulation` | **WORKING PROTOTYPE** |
| **Fall Detection** | Abrupt vertical posture collapse and horizontal ground immobility | YOLOv8n-pose / MediaPipe Pose (Apache 2.0) | ONNX Runtime (320x320 input) | `fall.detected` (v1.0.0) | `surv.ai.events.safety` | `incident_service.py` -> Medical Emergency Dispatch | High-priority SOS siren alert + nearest first-responder prompt | `test_fall_detection_event` | **WORKING PROTOTYPE** (MediaPipe Candidate) |
| **Abnormal Behavior** | Panic running, violent fighting, sudden crowd dispersal | SlowFast / VideoMAE (Apache 2.0 / MIT) | TorchScript / ONNX Temporal Runtime | `abnormal_behavior.detected` (v1.0.0) | `surv.ai.events.safety` | `incident_service.py` -> `incidents` (Severity: Critical) | Anomaly confidence score meter + camera auto-focus PTZ command | `test_abnormal_behavior_schema` | **SIMULATION / PROTOTYPE** |
| **Object Classification** | Multi-class differentiation: person, bicycle, car, motorcycle, bus, truck, boat | YOLOX-Nano / NanoDet-Plus (Apache 2.0) | ONNX Runtime CPU/GPU | `object.classified` (v1.0.0) | `surv.ai.events.perception` | `surv/app/services/fleet_service.py` & `parking_service.py` | Target classification tag + color/size attribute card | `test_detector_onnx_forward` | **PRODUCTION-CANDIDATE** |
| **Re-ID / Multi-Camera Tracking** | Cross-camera person tracking and continuous journey trajectory reconstruction | FastReID (Apache 2.0) trained on open market data | ONNX Runtime (Vector similarity cosine metric) | `reid.trajectory.updated` (v1.0.0) | `surv.ai.events.tracking` | `surv/app/services/tracking_service.py` -> Vector Index | GIS multi-camera breadcrumb trail with timestamped hops | `test_reid_feature_matching` | **WORKING PROTOTYPE** *(Licensing requires verified training weights)* |
| **People Counting** | Bidirectional ingress/egress counting across designated gate boundaries | ByteTrack + Virtual Tripwire vector count | Pure-Python SIMD | `person.counted` (v1.0.0) | `surv.ai.events.crowd` | `surv/app/services/crowd_service.py` -> `camera_counts` | Live IN/OUT counter metrics overlay on camera tiles | `test_crowd_counting` | **PRODUCTION-CANDIDATE** |
| **Queue Analytics** | Queue length, head-of-line wait time, bottleneck alerting | Spatial polygon density + ByteTrack dwell queue estimator | Pure-Python spatial math | `queue.metrics.updated` (v1.0.0) | `surv.ai.events.crowd` | `crowd_service.py` -> `queue_telemetry` | Queue depth bar chart (Current wait: 4m 12s) | `test_queue_analytics_schema` | **WORKING PROTOTYPE** |
| **Crowd Density** | Estimation of people per square meter ($\text{persons/m}^2$) & surge levels | CSRNet / YOLOX person cluster estimator | ONNX Runtime | `crowd.density.updated` (v1.0.0) | `surv.ai.events.crowd` | `crowd_service.py` -> `density_zones` | Color-coded heatmap overlay: Green (<2), Orange (2-4), Red (>4) | `test_crowd_density` | **PRODUCTION-CANDIDATE** |
| **Predictive Analytics / Congestion Forecasting** | Early warning of stampede risk and bottleneck surges ($t+15$ min projection) | Prophet / LightGBM time-series forecasting (MIT) | ONNX Runtime / SciPy | `crowd.forecast.alert` (v1.0.0) | `surv.ai.events.crowd` | `crowd_service.py` -> Predictive advisory table | Surge advisory ticker: "Zone C expected to exceed capacity at 18:30" | `test_predictive_crowd_forecasting` | **WORKING PROTOTYPE** |
| **Centralized ANPR** | City-wide vehicle search, hotlist tracking, stolen vehicle interception | YOLOX + PaddleOCR PP-OCRv4 (Apache 2.0) | ONNX Runtime | `anpr.plate.detected` (v1.0.0) | `surv.ai.events.anpr` | `surv/app/services/anpr_service.py` -> `anpr_events` | City-wide ANPR search tab with wildcard & fuzzy matching | `test_anpr_pipeline_end_to_end` | **PRODUCTION-CANDIDATE** |
| **Face Search / Missing Person** | 1:N gallery matching for lost children and registered missing persons | MobileFaceNet / AdaFace (MIT / Apache 2.0) | ONNX Runtime (128-dim/512-dim embedding) | `face.match.detected` (v1.0.0) | `surv.ai.events.security` | `surv/app/services/security_service.py` -> Vector Vault | Missing person search dialog with reference photo upload | `test_face_match_schema` | **WORKING PROTOTYPE** *(Biometric DPDP Act governance strictly applied)* |
| **Drone AI Video Ingest** | Aerial surveillance feed ingest, crowd anomaly tracking, disaster monitoring | RTSP stream ingest via MediaMTX + YOLOX aerial weights | MediaMTX + ONNX Runtime | `drone.telemetry.updated` (v1.0.0) | `surv.ai.events.aerial` | `surv/app/services/camera_service.py` -> `cameras` | Aerial HUD overlay with GPS coordinates and altitude | `test_drone_rtsp_ingest_schema` | **INTEGRATION READY** |

---

## 3. ICCC Integration & Event Correlation

In accordance with Tender B requirements, all AI perception events emitted on `surv.ai.events.*` topics are ingested by the SARVANETRA Central ICCC Alert Correlator:
1. **Multi-Sensor Correlation:** Correlates an ANPR hit with downstream crowd surge or perimeter breach within a spatio-temporal window ($\Delta t \le 180\text{s}, \Delta d \le 500\text{m}$).
2. **Standardized Alert Escalation:** Automatic generation of Priority 1 incidents with attached evidence snapshots and video playback offsets ($t-10\text{s}$ to $t+30\text{s}$).
3. **Operator Acknowledgment & SOP Workflow:** Mandates digital operator sign-off, SOP resolution checklist, and audit logging into immutable PostgreSQL audit tables.
