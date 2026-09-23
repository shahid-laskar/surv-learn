# SARVANETRA — AI Model Benchmarking & Performance Methodology
**Document ID:** `AI-BENCHMARK-METHOD-001`  
**Reference Document:** [AI_MODEL_BENCHMARK.md](file:///opt/surv-learn/docs/AI_MODEL_BENCHMARK.md)  
**Host Hardware:** Intel(R) Core(TM) i3-4130 CPU @ 3.40GHz (4 threads), 8GB RAM, Ubuntu Linux  
**Date:** September 23, 2026  

---

## 1. Benchmarking Scope & Objectives

To avoid tender failure and unrealistic resource sizing, SARVANETRA measures actual compute requirements on real hardware rather than accepting synthetic or vendor marketing numbers.

This document details the benchmarking methodology, execution procedures, and reproducible commands used to quantify:
1. Pure forward inference latency (ms per frame).
2. End-to-end pipeline latency (frame decode, letterbox pre-processing, ONNX inference, NMS post-processing).
3. Memory footprint (RAM RSS and GPU VRAM).
4. Kafka serialization and transmission throughput.

---

## 2. Benchmark Execution Commands

### 2.1. Object Detection (ONNX Runtime CPU)
```bash
PYTHONPATH=.:surv python3 -c "
import time, numpy as np
from ai_platform.engine.onnx_detector import OnnxDetector

detector = OnnxDetector('ai-platform/models/yolov8n_320.onnx', input_size=(320, 320))
frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

# Warmup passes
for _ in range(5):
    _ = detector.detect(frame)

# Benchmark 50 iterations
latencies = []
for _ in range(50):
    t0 = time.perf_counter()
    _ = detector.detect(frame)
    latencies.append((time.perf_counter() - t0) * 1000)

print(f'Mean Latency: {np.mean(latencies):.2f} ms')
print(f'P95 Latency:  {np.percentile(latencies, 95):.2f} ms')
print(f'P99 Latency:  {np.percentile(latencies, 99):.2f} ms')
print(f'Throughput:   {1000 / np.mean(latencies):.2f} FPS')
"
```

### 2.2. ANPR Normalization Throughput
```bash
PYTHONPATH=.:surv python3 -c "
import time
from ai_platform.pipelines.anpr_pipeline import AnprPipeline

pipeline = AnprPipeline()
sample_plates = ['KL01AB1234', 'KL-07-CD-5678', 'DL 01 C 1234', 'MH-12-DE-9999']

t0 = time.perf_counter()
count = 50000
for i in range(count):
    _ = pipeline.normalize_plate(sample_plates[i % len(sample_plates)])
elapsed = time.perf_counter() - t0

print(f'Processed {count} plate normalizations in {elapsed:.3f}s ({count/elapsed:,.0f} ops/sec)')
"
```

### 2.3. Spatial Rule Engine (Intrusion & Line Crossing)
```bash
PYTHONPATH=.:surv python3 -c "
import time
from ai_platform.engine.spatial_rules import SpatialRuleEngine

engine = SpatialRuleEngine()
poly = [(100, 100), (500, 100), (500, 500), (100, 500)]
pt = (250, 250)

t0 = time.perf_counter()
count = 100000
for _ in range(count):
    _ = engine.check_intrusion(pt, poly)
elapsed = time.perf_counter() - t0

print(f'Processed {count} ray-cast checks in {elapsed:.3f}s ({count/elapsed:,.0f} checks/sec)')
"
```

---

## 3. Measured Summary Reference

For comprehensive benchmark numbers across CPU, GPU, memory, and multi-camera loads, refer to:
- [AI_MODEL_BENCHMARK.md](file:///opt/surv-learn/docs/AI_MODEL_BENCHMARK.md)
- [AI_HARDWARE_CAPABILITY.md](file:///opt/surv-learn/docs/AI_HARDWARE_CAPABILITY.md)
- [AI_SCALE_TEST_REPORT.md](file:///opt/surv-learn/docs/AI_SCALE_TEST_REPORT.md)
