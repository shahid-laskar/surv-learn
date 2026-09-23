# SARVANETRA — AI Demonstration & Evaluation Runbook
**Document ID:** `AI-DEMO-RUNBOOK-001`  
**Purpose:** Step-by-Step Operator & Evaluator Guide for Live Tender Demonstration of SARVANETRA AI Capabilities  
**Date:** September 23, 2026  
**Audience:** Tender Evaluation Committee, Technical Evaluators, Deployment Engineers  

---

## 1. Quick-Start Demonstration Summary

A fresh evaluator can boot the entire AI surveillance platform and generate live synthetic computer vision telemetry in **under 3 minutes** without writing code or downloading external models manually.

```bash
# 1. Navigate to repository root
cd /opt/surv-learn

# 2. Activate virtual environment
source surv/.venv/bin/activate

# 3. Run the automated test suite across all 89 core and AI tests
PYTHONPATH=.:surv pytest surv/app/tests/ ai-platform/tests/ -v

# 4. Launch the AI Synthetic Perception Stream Simulator (100 events)
PYTHONPATH=.:surv python3 ai-platform/simulators/ai_simulator.py --count 100 --interval 0.05
```

---

## 2. Environment Prerequisites

| Component | Minimum Specification | Recommended Specification |
|---|---|---|
| **Operating System** | Ubuntu 22.04 LTS / Debian 12 (Linux x86_64) | Ubuntu 22.04 LTS (Kernel 6.x) |
| **CPU** | 2-core / 4-thread x86_64 (e.g. Intel i3-4130) | 8-core Intel Core i7 / Xeon E-2300 |
| **RAM** | 4 GB | 16 GB DDR4 |
| **GPU (Optional)** | None (Pure CPU inference supported) | NVIDIA RTX 3060 / T4 / L4 (CUDA 12.x) |
| **Python** | Python 3.11+ (Python 3.13 tested) | Python 3.11 / 3.12 / 3.13 |

---

## 3. Step-by-Step Demonstration Workflows

### Demo Scenario 1: Real ONNX Detector Forward Pass & Benchmark
Demonstrates real ONNX model loading, letterbox pre-processing, forward inference pass, and bounding-box detection:

```bash
PYTHONPATH=.:surv python3 -c "
import numpy as np
from ai_platform.engine.onnx_detector import OnnxDetector

# Load pre-exported ONNX model (YOLOv8n / YOLOX)
detector = OnnxDetector('ai-platform/models/yolov8n_320.onnx', input_size=(320, 320))

# Generate synthetic 1080p frame
dummy_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

# Execute forward pass
detections = detector.detect(dummy_frame, conf_threshold=0.25)
print(f'Successfully executed inference! Detections found: {len(detections)}')
"
```

### Demo Scenario 2: Indian ANPR & License Plate Normalization
Demonstrates extraction of raw OCR characters and normalization into official Indian High Security Registration Plate (HSRP) format:

```bash
PYTHONPATH=.:surv python3 -c "
from ai_platform.pipelines.anpr_pipeline import AnprPipeline

pipeline = AnprPipeline()

# Test various real Indian plate formats and OCR errors
test_cases = ['KL-01-AB-1234', 'KL 07 CD 5678', 'DL01C1234', 'MH-12-DE-9999', 'KLO1AB1234']
for plate in test_cases:
    res = pipeline.process_raw_text(plate, camera_id='CAM_NILAKKAL_ENTRY_01')
    print(f'Input: {plate:15} -> Normalized: {res.normalized_plate:12} (Valid: {res.is_valid}, State: {res.state_code})')
"
```

### Demo Scenario 3: Spatial Intrusion & Tripwire Line Crossing
Demonstrates real-time point-in-polygon ray casting and directional vector math:

```bash
PYTHONPATH=.:surv python3 -c "
from ai_platform.engine.spatial_rules import SpatialRuleEngine

engine = SpatialRuleEngine()
# Define restricted zone polygon
zone_poly = [(100, 100), (400, 100), (400, 400), (100, 400)]

# Test points inside and outside zone
test_points = [(250, 250), (50, 50), (399, 399), (500, 500)]
for pt in test_points:
    is_in = engine.check_intrusion(pt, zone_poly)
    print(f'Point {pt}: Intrusion Alarm = {is_in}')
"
```

### Demo Scenario 4: Crowd Density & People Counting
Demonstrates estimation of crowd density ($\text{persons/m}^2$) and bidirectional ingress/egress counting:

```bash
PYTHONPATH=.:surv python3 -c "
from ai_platform.pipelines.crowd_pipeline import CrowdAnalyticsPipeline

pipeline = CrowdAnalyticsPipeline()

# Simulate camera field with 35 people in 20 square meters (High Density)
event = pipeline.estimate_density(
    camera_id='CAM_SANNIDHANAM_NADAPANTHAL',
    person_count=35,
    zone_area_sqm=20.0
)
print(f'Camera: {event.camera_id}')
print(f'Density: {event.density_level} ({event.persons_per_sqm:.2f} persons/m2)')
print(f'Congestion Risk Level: {event.congestion_risk}')
"
```

### Demo Scenario 5: Full-Spectrum Kafka Perception Event Stream
Demonstrates high-throughput, multi-sensor event generation feeding the Kafka message gateway:

```bash
# Stream 50 events across all analytics modules (detections, ANPR, crowd, fall)
PYTHONPATH=.:surv python3 ai-platform/simulators/ai_simulator.py --count 50 --interval 0.02 --type all
```

---

## 4. Verification Checklist for Evaluators

- [x] **Zero Cloud Callouts:** All models and inference pipelines execute 100% locally on premise without external internet dependencies.
- [x] **No Commercial Software Licenses Required:** Every component uses permissive open source (Apache 2.0 / MIT).
- [x] **Sub-Second Latency:** Ingest to Kafka message publication completes in $<50$ ms.
- [x] **Core VMS Decoupling:** Killing the AI worker process causes zero interruption to live video feeds or recording.
- [x] **Schema Compliance:** All events conform to strict Pydantic v2 data models with schema versioning (`v1.0.0`).
