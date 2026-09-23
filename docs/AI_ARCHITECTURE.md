# SARVANETRA — Modular AI Architecture & Perception Gateway
**Document ID:** `AI-ARCH-SPEC-001`  
**Classification:** Modular AI Systems Design  
**Revision:** 1.0  
**Target Flow:** Camera RTSP/RTMP → MediaMTX → AI Platform Worker → Event Gateway → Kafka → Core Services  

---

## 1. Architectural Philosophy: The Decoupled Perception Layer

SARVANETRA’s core engineering principle dictates that **VMS operations and video recording must never depend on the availability or latency of AI inference engines.**

```
                     [ IP Camera / RTSP Feed ]
                                │
                                ▼
                     [ MediaMTX Media Server ]
                                │
        ┌───────────────────────┴───────────────────────┐
        │                                               │
        ▼ (60s Chunking)                                ▼ (RTSP / Substream)
 [ upload_to_minio.py ]                    [ AI Perception Worker ]
        │                                               │
        ▼                                               ├── BaseDetector (YOLOX / ONNX)
 [ MinIO Object Storage ]                               ├── BaseTracker (ByteTrack)
        │                                               ├── SpatialRuleEngine (Intrusion/Line)
        ▼                                               └── AnprPipeline (PP-OCRv4)
 [ Video Recordings & Sidecars ]                        │
                                                        ▼
                                              [ AI Event Gateway ]
                                                        │
                                                        ▼
                                             [ Apache Kafka Topics ]
                                                        ├── vehicle.anpr.detected
                                                        ├── camera.ai.alerts
                                                        ├── crowd.density.alert
                                                        └── camera.people.count
                                                        │
                         ┌──────────────────────────────┴──────────────────────────────┐
                         ▼                                                             ▼
             [ FastAPI Business Logic ]                                     [ React ICCC & GIS ]
             ├── Watchlist Alert Matcher                                    ├── Leaflet Spatial COP
             ├── Parking Allocation Engine                                  ├── Real-Time Alert Drawer
             └── Incident & Evidence Sealer                                 └── Video Wall Overlay
```

---

## 2. Core Subsystems in `ai-platform/`

### 2.1 The Schema Layer (`ai_platform/schemas/`)
* **Standardized Envelope:** Every perception event emitted by any detector, tracker, or OCR engine is wrapped in `BaseAiEvent`, carrying:
  - `event_id`: Unique UUID.
  - `event_type`: e.g. `vehicle.anpr.detected`, `intrusion.detected`, `crowd.density.updated`.
  - `event_version`: `1.0`.
  - `timestamp`: Canonical UTC timestamp.
  - `camera_id`: MediaMTX path / hardware identifier.
  - `model_name` & `model_version`: Full provenance attribution for auditability.
  - `confidence`: Calibrated float $0.0 \le c \le 1.0$.
  - `evidence_references`: MinIO snapshot or video segment pointers.

### 2.2 The Engine Layer (`ai_platform/engine/`)
* **`OnnxDetector`:** Executes optimized ONNX models (e.g. `yolov8n_320.onnx`) with letterbox resizing, forward pass, and pure NumPy Non-Maximum Suppression (NMS). Benchmarked at **23.4 FPS** on standard CPU.
* **`ByteTracker`:** Two-stage association algorithm matching high-confidence detections first, then low-confidence detections using IoU and centroid proximity. Computes persistent `track_id`, trajectory vectors, and zone dwell time.
* **`SpatialRuleEngine`:** Zero-dependency geometry engine implementing:
  - Ray-casting point-in-polygon intrusion detection.
  - Cross-product line segment orientation for virtual tripwires.
  - Dwell-timer thresholds for loitering detection.

### 2.3 The Gateway Layer (`ai_platform/gateway/`)
* **Circuit Breaker Protection:** The `AiEventGateway` checks Kafka broker connectivity. If Kafka experiences a timeout or network partition, the gateway trips open, switches to local logging/degraded persistence mode, and avoids blocking frame processing loops.
* **Frigate MQTT Adapter:** `FrigateMqttAdapter` normalizes third-party edge MQTT payloads into SARVANETRA's canonical event schema.

---

## 3. Failure Domain Isolation

| Outage Scenario | System Behavior & Protection Mechanism |
|---|---|
| **AI Worker Crash / OOM** | MediaMTX continues recording without interruption. Local video chunks continue uploading to MinIO. Core VMS API remains operational. Docker auto-restarts AI container. |
| **Kafka Broker Down** | AI Gateway circuit breaker trips; logs events locally without crashing inference loop. Resumes Kafka dispatch automatically upon broker reconnection. |
| **Camera RTSP Drop** | MediaMTX fires `runOnNotReady` hook. Status consumer logs transition. AI worker evicts stale tracks via `tracker.reset()` upon reconnection. |
| **High Load / Slow CPU** | Frame queue capped at 10 frames per stream. Worker drops intermediate frames to guarantee zero memory bloat and real-time live processing. |
