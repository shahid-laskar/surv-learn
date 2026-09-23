# SARVANETRA — AI Platform Developer & Extension Guide
**Document ID:** `AI-DEV-001`  
**Classification:** Developer Guide & Plugin Architecture  
**Subject:** Adding Custom Detectors, Trackers, OCR Engines, and Spatial Rules  

---

## 1. Directory Structure

```text
ai-platform/
├── config/
│   ├── model_registry.yaml        # Model metadata, tasks, checksums, licenses
│   └── camera_analytics.yaml      # Per-camera analytical triggers and ROI zones
├── engine/
│   ├── base.py                    # Abstract Base Classes (BaseDetector, BaseTracker, BaseOcrEngine)
│   ├── onnx_detector.py           # Real ONNX Runtime inference implementation
│   ├── tracker.py                 # Multi-object tracker (ByteTracker)
│   └── spatial_rules.py           # Intrusion, Tripwire, and Loitering rule engine
├── gateway/
│   ├── event_gateway.py           # Circuit breaker Kafka event producer
│   └── mqtt_adapter.py            # Frigate / Edge MQTT normalizer
├── pipelines/
│   ├── object_pipeline.py         # Detection + Tracking + Spatial Rules
│   ├── anpr_pipeline.py           # License Plate Normalization & Ingest
│   └── crowd_pipeline.py          # Density estimation & People Counting
├── simulators/
│   └── ai_simulator.py            # Synthetic perception generator across 15 classes
└── tests/
    └── test_ai_platform.py        # Automated test suite
```

---

## 2. Implementing a Custom Detector

To integrate a new neural network detector (e.g. specialized helmet detection or vehicle color classifier), inherit from `BaseDetector` in `ai_platform/engine/base.py`:

```python
from ai_platform.engine.base import BaseDetector, Detection
from typing import List, Any

class CustomHelmetDetector(BaseDetector):
    def __init__(self, model_path: str, confidence_threshold: float = 0.6):
        super().__init__("helmet-detector-v1", model_path, confidence_threshold)
        # Initialize your ONNX / TensorRT / OpenVINO session here

    def detect(self, frame: Any) -> List[Detection]:
        # Preprocess frame, execute forward pass, extract bboxes
        return [
            Detection(
                class_name="helmet_missing",
                confidence=0.92,
                x1=0.2, y1=0.3, x2=0.4, y2=0.5,
                attributes={"rider_count": 2}
            )
        ]
```

---

## 3. Configuring Camera Spatial Analytics

Edit `ai-platform/config/camera_analytics.yaml` to assign analytical rules to a camera stream without rebuilding containers:

```yaml
cameras:
  - camera_id: "CAM_PERIMETER_NORTH"
    site_id: 1
    stream_url: "rtsp://localhost:8554/CAM_PERIMETER_NORTH"
    analytics:
      intrusion: true
      line_crossing: true
    regions:
      intrusion_zones:
        - zone_id: "ZONE_FENCE_NORTH"
          polygon: [[0.0, 0.2], [1.0, 0.2], [1.0, 0.4], [0.0, 0.4]]
          target_classes: ["person", "car"]
      tripwires:
        - tripwire_id: "WIRE_ENTRY_LANE"
          p1: [0.2, 0.8]
          p2: [0.8, 0.8]
          direction: "A_TO_B"
```

---

## 4. Running the Development Simulator

To test downstream Kafka consumers, FastAPI routers, and frontend UI dashboards without connecting live RTSP cameras:
```bash
PYTHONPATH=. surv/.venv/bin/python3 ai-platform/simulators/ai_simulator.py --count 20 --interval 0.5 --type all
```
Supported types: `all`, `detection`, `spatial`, `anpr`, `crowd`, `counting`, `fall`, `face`.
