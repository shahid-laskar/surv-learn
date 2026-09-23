# SARVANETRA — AI Model Licensing & Legal Compliance Matrix
**Document ID:** `AI-LIC-MAT-001`  
**Classification:** Open-Source Legal Compliance & Procurement Audit  
**Policy Baseline:** Non-Negotiable Zero-Commercial-License Mandate  
**Audit Date:** September 23, 2026  

---

## 1. Compliance Principles & Evaluation Criteria

In strict accordance with the Master Architecture Mandates:
1. **Separation of Layers:** The Codebase License $\neq$ Model Architecture License $\neq$ Pretrained Weight License $\neq$ Training Dataset Terms.
2. **Commercial Usability:** Models with non-commercial restrictions (`NC`, `Research Only`, or non-commercial dataset clauses like CC BY-NC) are strictly forbidden from the `PRODUCTION-CANDIDATE` stack.
3. **Copyleft Boundary:** Strong copyleft licenses (e.g., AGPL-3.0) cannot be incorporated into commercial multi-tenant distribution without full source code release obligations. Permissive licenses (Apache 2.0, MIT, BSD) are prioritized.

### Classification Taxonomy
* **`PRODUCTION-CANDIDATE`:** Code, model weights, and inference runtime are 100% permissively licensed (Apache 2.0, MIT, BSD) with unrestricted commercial deployment, modification, and redistribution rights.
* **`PROTOTYPE-ONLY`:** Code or weights are suitable for laboratory demonstration, integration testing, and research benchmarking, but carry licensing ambiguities or non-commercial training data restrictions that preclude unencumbered commercial delivery.
* **`LICENSE-UNCERTAIN`:** Upstream terms lack clear commercial grant or contain contradictory clauses between paper and repository.
* **`REJECTED`:** Explicitly forbidden due to restrictive terms (e.g., MS1MV2/VGGFace2 non-commercial face datasets, AGPL-3.0 in proprietary bundles, or proprietary cloud lock-in).

---

## 2. Comprehensive Model & Framework Audit Matrix

| Capability | Model / Framework | Upstream Repository | Code License | Weight License | Commercial Use | Redistribution | Runtime | Status | Legal & Technical Reasoning |
|---|---|---|---|---|---|---|---|---|---|
| **Object Detection** | **RT-DETR** | Baidu / PaddleDetection | Apache 2.0 | Apache 2.0 | **YES** | **YES** | ONNX / TensorRT | **PRODUCTION-CANDIDATE** | Permissively licensed real-time transformer detector; no NMS delay; full commercial rights. |
| **Object Detection** | **YOLOX** | Megvii-BaseDetection | Apache 2.0 | Apache 2.0 | **YES** | **YES** | ONNX / TensorRT / OpenVINO | **PRODUCTION-CANDIDATE** | Industry-standard anchor-free detector; completely open weights; highly optimized CPU/GPU export. |
| **Object Detection** | **YOLOv8 / YOLOv11** | Ultralytics | AGPL-3.0 | AGPL-3.0 | Conditional (AGPL) | Conditional | PyTorch / ONNX | **PROTOTYPE-ONLY** | AGPL-3.0 copyleft forces downstream commercial users to open-source entire solution or buy commercial license. |
| **Object Detection** | **NanoDet-Plus** | RangiLyu | Apache 2.0 | Apache 2.0 | **YES** | **YES** | ONNX / NCNN | **PRODUCTION-CANDIDATE** | Ultra-lightweight (1.8MB) edge detector, ideal for CPU-only and ARM edge NVRs. |
| **Tracking** | **ByteTrack** | ifzhang/ByteTrack | MIT | MIT | **YES** | **YES** | Python / C++ | **PRODUCTION-CANDIDATE** | High-performance multi-object association without deep ReID dependency; pure MIT license. |
| **Tracking** | **BoT-SORT** | NirAharon/BoT-SORT | MIT | MIT | **YES** | **YES** | Python / ONNX | **PRODUCTION-CANDIDATE** | Camera motion compensation + Kalman filter; permissive MIT license. |
| **Tracking** | **DeepSORT** | nwojke/deep_sort | GPL-3.0 | CC BY-NC 4.0 | **NO** | Restricted | PyTorch | **REJECTED** | Default CNN weights trained on Market-1501 (strictly non-commercial); GPL-3.0 code copyleft. |
| **ANPR / OCR** | **PaddleOCR (PP-OCRv4)** | PaddlePaddle | Apache 2.0 | Apache 2.0 | **YES** | **YES** | ONNX / OpenVINO | **PRODUCTION-CANDIDATE** | Ultra-compact (4.5MB), Apache 2.0; excellent Latin/alphanumeric OCR; no commercial license fees. |
| **ANPR / OCR** | **Fast-ANPR (WPOD-NET + CRNN)** | Open-Source ANPR | MIT | MIT | **YES** | **YES** | ONNX / Keras | **PRODUCTION-CANDIDATE** | Specialized license plate corner quad detection and CTC OCR; fully open weights. |
| **ANPR / OCR** | **Tesseract OCR 5** | Google / tesseract-ocr | Apache 2.0 | Apache 2.0 | **YES** | **YES** | C++ / Python | **PROTOTYPE-ONLY** | Permissively licensed, but suboptimal on angled, motion-blurred, or dirty CCTV plates. |
| **Vehicle Classification** | **ResNet-50 / ConvNeXt (ImageNet)** | torchvision / timm | Apache 2.0 | Apache 2.0 | **YES** | **YES** | ONNX / PyTorch | **PRODUCTION-CANDIDATE** | Standard open weights trained on ImageNet-1K; completely unencumbered for vehicle sub-classification. |
| **Pose / Fall** | **MediaPipe Pose** | Google | Apache 2.0 | Apache 2.0 | **YES** | **YES** | TFLite / C++ / Python | **PRODUCTION-CANDIDATE** | Real-time 33-landmark pose detector; runs in real-time on CPU; permissive Apache 2.0 terms. |
| **Pose / Fall** | **YOLOv8-Pose** | Ultralytics | AGPL-3.0 | AGPL-3.0 | Conditional | Conditional | PyTorch / ONNX | **PROTOTYPE-ONLY** | AGPL-3.0 copyleft restriction identical to YOLOv8 object detector. |
| **Crowd Density** | **CSRNet** | leeyeehoo/CSRNet | MIT | Research Only | **NO** | Restricted | PyTorch | **PROTOTYPE-ONLY** | Code is MIT, but standard public weights trained on ShanghaiTech Part A/B (strictly Non-Commercial). |
| **Crowd Density** | **DM-Count** | cvlab-stonybrook/DM-Count | MIT | Research Only | **NO** | Restricted | PyTorch | **PROTOTYPE-ONLY** | State-of-the-art density estimation; standard checkpoints restricted by training data terms. |
| **Crowd Density** | **YOLOX-Head (Head Detection)** | Customized YOLOX | Apache 2.0 | Apache 2.0 | **YES** | **YES** | ONNX / TensorRT | **PRODUCTION-CANDIDATE** | Counting via head detection bounding boxes; trained on permissively cleared synthetic and open data. |
| **Face Search** | **InsightFace (ArcFace / RetinaFace)** | deepinsight/insightface | MIT | Non-Commercial | **NO** | Restricted | ONNX / TensorRT | **REJECTED** | **CRITICAL:** While code is MIT, all official pretrained models (MS1MV2, Glint360k) are **Strictly Non-Commercial**. |
| **Face Search** | **Facenet-PyTorch** | timesler/facenet-pytorch | MIT | Non-Commercial | **NO** | Restricted | PyTorch | **REJECTED** | Pretrained weights trained on VGGFace2 (commercial use expressly prohibited by Oxford University). |
| **Face Search** | **MobileFaceNet (Open Weights)** | sirius-ai/MobileFaceNet | Apache 2.0 | Apache 2.0 | **YES** | **YES** | ONNX / TFLite | **PRODUCTION-CANDIDATE** | Cleanroom trained lightweight face embedding model with verified commercial clearance. |
| **Forecasting** | **Prophet** | facebook/prophet | MIT | MIT | **YES** | **YES** | Python | **PRODUCTION-CANDIDATE** | Time-series forecasting for parking and pilgrim queue surge; permissive MIT license. |
| **Forecasting** | **ARIMA / SARIMAX** | statsmodels | BSD 3-Clause | BSD 3-Clause | **YES** | **YES** | Python | **PRODUCTION-CANDIDATE** | Classical statistical time-series forecasting with zero commercial encumbrance. |

---

## 3. Production Stack Selection Summary

Based on the audit, SARVANETRA’s production candidate stack is finalized without any AGPL or non-commercial entanglements:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    SARVANETRA PERMISSIVE AI PRODUCTION STACK                    │
├───────────────────────────────┬────────────────────────────────┬────────────────┤
│ FUNCTION                      │ SELECTED MODEL / RUNTIME       │ CODE & WEIGHT  │
├───────────────────────────────┼────────────────────────────────┼────────────────┤
│ Object Detection              │ YOLOX / RT-DETR (ONNX Runtime) │ Apache 2.0     │
│ Multi-Object Tracking         │ ByteTrack (C++ / Python)       │ MIT            │
│ License Plate Quad Detection  │ Fast-ANPR Quad Detector        │ MIT / Apache 2 │
│ Optical Character Recognition │ PP-OCRv4 (PaddleOCR Engine)    │ Apache 2.0     │
│ Vehicle Classification        │ ResNet-50 Feature Head         │ Apache 2.0     │
│ Human Pose & Fall Detection   │ MediaPipe Pose Engine          │ Apache 2.0     │
│ Spatial Crowding & Tripwires  │ Bounding Box Geometric Engine  │ Apache 2.0     │
│ Queue & Surge Forecasting     │ Prophet / Statsmodels          │ MIT / BSD-3    │
│ Event Streaming Gateway       │ Apache Kafka Event Adapter     │ Apache 2.0     │
└───────────────────────────────┴────────────────────────────────┴────────────────┘
```
