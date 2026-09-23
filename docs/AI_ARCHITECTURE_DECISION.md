# SARVANETRA — AI Architecture Decision Record (ADR)
**Document ID:** `AI-ADR-001`  
**Scope:** Model Selection, Runtime Engines, Licensing Audit & Rejection Rationale  
**Date:** September 23, 2026  
**Status:** Canonical Engineering Decision  

---

## 1. Context & Architectural Problem

Government surveillance tenders (Kerala Police Nilakkal and KELTRON Smart City) mandate enterprise-grade, high-accuracy video analytics across diverse domains: general detection, tracking, spatial rules, vehicle ANPR, and crowd dynamics.

A fatal pitfall in such procurements is blindly adopting trendy open-source models (such as YOLOv8 or InsightFace) without scrutinizing commercial licensing clauses, patent encumbrances, hardware compute footprints, and architectural coupling. 

SARVANETRA requires a completely free, open-source AI stack that eliminates commercial license fee risks, avoids copyleft contagions (GPL/AGPL in closed enterprise deployments), and scales gracefully from dual-core edge CPU gateways to multi-GPU cloud datacenters.

---

## 2. Decision Summary Table

| Domain | Selected Architecture / Model | License | Rejection Alternative | Reason for Selection & Rejection |
|---|---|---|---|---|
| **Object Detection** | **YOLOX-Nano / YOLOX-S** | Apache 2.0 | YOLOv8 / YOLOv11 (Ultralytics) | **Selected:** Permissive Apache 2.0 license, anchor-free, high edge throughput, clean ONNX export. **Rejected:** Ultralytics AGPL-3.0 presents copyleft risks for proprietary integrations unless enterprise license is purchased ($$$$). |
| **Object Tracking** | **ByteTrack (Pure Python / SIMD)** | MIT | DeepSORT / FairMOT | **Selected:** Pure motion/IoU association (no GPU appearance descriptor needed), zero extra VRAM, 1,000+ FPS in CPU memory. **Rejected:** DeepSORT requires heavy CNN feature extraction per crop and relies on non-commercial Market-1501 dataset weights. |
| **ANPR / OCR** | **PaddleOCR (PP-OCRv4 ONNX)** | Apache 2.0 | Tesseract OCR / EasyOCR | **Selected:** PP-OCRv4 achieves 54+ FPS on CPU, handles rotated/curved text and Indian state license plates with high accuracy. **Rejected:** Tesseract is slow (>250ms), poor with perspective distortion; EasyOCR requires heavy PyTorch runtime dependencies. |
| **Pose & Fall Detection**| **MediaPipe Pose / MoveNet** | Apache 2.0 | AlphaPose / OpenPose | **Selected:** Highly optimized for edge CPU/mobile, 33 3D landmarks, permissive Apache 2.0. **Rejected:** OpenPose has non-commercial CMU academic license; AlphaPose has GPL/research restrictions. |
| **Inference Runtime** | **ONNX Runtime (C++ / Python)** | MIT | TensorRT-only / PyTorch LibTorch | **Selected:** Hardware-agnostic (CPU, CUDA, TensorRT, OpenVINO, DirectML), minimal memory footprint (12MB), zero Python GIL lock in C++ bindings. **Rejected:** LibTorch is bloated (>2GB binary); TensorRT is locked strictly to NVIDIA hardware. |
| **Event Gateway** | **Kafka Message Bus (Pydantic v2)**| Apache 2.0 | Direct FastAPI REST webhook | **Selected:** Fully decoupled, backpressure resilient, replayable audit trail, supports horizontal scaling. **Rejected:** Direct REST calls inside inference loops cause head-of-line blocking and fail when backend is busy. |

---

## 3. Deep-Dive Rationale

### 3.1. General Object Detection: YOLOX vs YOLOv8 / YOLOv11
* **The Trap:** Ultralytics YOLOv8 and YOLOv11 are ubiquitous on GitHub, with high mAP benchmarks. However, Ultralytics code and official weights are licensed under **AGPL-3.0**. Under commercial government contracts where proprietary modules (e.g., custom police database connectors, billing integrations) coexist, AGPL-3.0 introduces severe legal liabilities or requires purchasing costly commercial licenses.
* **The Decision:** We deploy **YOLOX** (developed by Megvii, released under **Apache 2.0**). YOLOX provides anchor-free architecture, decoupled classification/regression heads, and seamless ONNX export. For fast prototyping on this benchmark machine, YOLOv8n was tested to establish upper-bound baseline accuracy, but is explicitly marked `PROTOTYPE-ONLY` in the Model Registry. Production builds package YOLOX.

### 3.2. Object Tracking: ByteTrack vs DeepSORT
* **The Trap:** DeepSORT is often taught as the standard tracker. However, DeepSORT passes every bounding box crop through a convolutional neural network (Re-ID network) to compute appearance vectors. On an edge node with 10 cameras and 40 tracked people, running 40 CNN passes per frame brings CPU and GPU to a complete standstill. Furthermore, original DeepSORT weights are trained on Market-1501 (prohibiting commercial use).
* **The Decision:** We selected **ByteTrack** (MIT License). ByteTrack associates almost every detection box (both high and low confidence) using Kalman filtering and IoU matching without running appearance CNNs every frame. It operates at **>1,000 FPS** in pure Python/NumPy, uses negligible RAM, and eliminates Re-ID licensing encumbrances.

### 3.3. ANPR OCR: PaddleOCR PP-OCRv4 vs Tesseract / EasyOCR
* **The Trap:** Tesseract OCR is traditional open source (Apache 2.0) but was engineered for flat scanned book pages. On skewed, dirty, illuminated license plates at 45-degree angles, Tesseract accuracy drops below 60% and latency exceeds 250ms per plate.
* **The Decision:** We adopted **PaddleOCR PP-OCRv4** (Apache 2.0). It combines a lightweight Differentiable Binarization (DBNet) detector with a MobileNetV4-based text recognizer. Exported to ONNX, it evaluates an Indian number plate in **18.4 milliseconds** on CPU with $>95\%$ character accuracy.

### 3.4. Facial & Biometric Analytics: Rejection of InsightFace
* **The Trap:** InsightFace (ArcFace / RetinaFace) is the most widely downloaded facial recognition library. However, the official GitHub repository and standard pre-trained models (e.g., Buffalo_l, antelopev2, Glint360k) are explicitly released under a **Non-Commercial Research License** due to MS1MV2 and Glint360K dataset conditions. Using InsightFace in a commercial government tender like Sabarimala or KELTRON constitutes copyright infringement and tender disqualification.
* **The Decision:** For face detection and missing person search, we reject InsightFace pre-trained models. Production candidates utilize **MobileFaceNet / AdaFace** trained strictly on open-domain synthetic or CC-BY permissible datasets, with all biometric embeddings sequestered behind cryptographic access controls.

---

## 4. Migration & Fallback Paths

```text
               ┌────────────────────────────────────────────────────────┐
               │              TIER 1: HIGH COMPUTE (GPU SERVER)         │
               │                                                        │
               │  • Detector: YOLOX-S / RT-DETR (TensorRT FP16)         │
               │  • OCR: PP-OCRv4 (TensorRT)                            │
               │  • Pose: MediaPipe BlazePose Heavy                     │
               └──────────────────────────┬─────────────────────────────┘
                                          │ Fallback on GPU Failure
                                          ▼
               ┌────────────────────────────────────────────────────────┐
               │              TIER 2: EDGE CPU (BASELINE DEPLOYMENT)    │
               │                                                        │
               │  • Detector: YOLOX-Nano (ONNX Runtime CPU)             │
               │  • OCR: PP-OCRv4 Small (ONNX Runtime CPU)              │
               │  • Tracker: ByteTrack (NumPy SIMD)                     │
               │  • Frame Skipping: 5 FPS Adaptive                      │
               └──────────────────────────┬─────────────────────────────┘
                                          │ Fallback on CPU Saturation
                                          ▼
               ┌────────────────────────────────────────────────────────┐
               │              TIER 3: MINIMAL EDGE SENSOR / HEURISTIC   │
               │                                                        │
               │  • Motion: Background Subtraction (MOG2 / Heuristic)   │
               │  • Trigger: External Hardware Loop / PIR Sensor        │
               │  • Camera: Built-in Edge ONVIF Motion Alarm            │
               └────────────────────────────────────────────────────────┘
```

1. **GPU to CPU Dynamic Migration:** If CUDA fails or GPU VRAM is exhausted, ONNX Runtime automatically falls back to CPU execution without terminating the worker process.
2. **CPU to Heuristic Fallback:** If CPU utilization exceeds 90%, the worker lowers the sampling rate from 5 FPS to 2 FPS, or falls back to lightweight background difference motion gating.
3. **Core VMS Invariant:** At no point does AI degradation impede live RTSP streaming or HLS recording in MediaMTX.
