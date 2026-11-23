# SARVANETRA AI Platform v0.1 — License Revalidation Review
**Document ID:** `AI-LIC-REV-001`  
**Date:** September 23, 2026  
**Auditor:** Independent Acceptance & Integration Inspector  
**Baseline Policy:** Zero-Commercial-License Mandate & Permissive Open-Source Requirement  

---

## 1. Compliance Principles & Evaluation Rules
Section 7 of `docs/final_acceptance_test.md` establishes non-negotiable legal criteria:
1. **Separation of Layers:** Code license $\neq$ Model architecture license $\neq$ Pretrained weights license $\neq$ Training dataset terms.
2. **Open-Source Only:** No commercial or proprietary licenses are available to purchase.
3. **Copyleft & Distribution Risk:** AGPL-3.0 requires full source disclosure of all network-interfacing software; it cannot be embedded into commercial multi-tenant proprietary distributions without triggering copyleft obligations.
4. **Non-Commercial Restrictions:** Models trained on research-only datasets (e.g., MS1MV2, VGGFace2, ShanghaiTech CC BY-NC) are legally barred from production commercial deployment.

---

## 2. Audit of Existing Model Artifacts on Disk

| Artifact Filename | Architecture | Source / Exporter | Code License | Weight License | Status | Legal Risk & Assessment |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ai-platform/models/yolov8n_320.onnx` | YOLOv8n (Detection) | Ultralytics (PyTorch export) | AGPL-3.0 | AGPL-3.0 | **PROTOTYPE-ONLY** | Ultralytics enforces AGPL-3.0 on both code and official weights. Network distribution triggers copyleft source release requirements unless enterprise license is purchased. |
| `ai-platform/models/yolov8n_pose_320.onnx` | YOLOv8n-Pose (Keypoints) | Ultralytics (PyTorch export) | AGPL-3.0 | AGPL-3.0 | **PROTOTYPE-ONLY** | Same AGPL-3.0 terms as YOLOv8n. Keypoints support fall detection prototyping, but weights are copyleft encumbered. |

**Key Finding:** The only physical model artifacts present in the repository are AGPL-3.0 encumbered and are classified as **PROTOTYPE-ONLY**.

---

## 3. License Audit of Production-Candidate Models

| Capability | Target Model | Upstream Project | Code License | Weights License | Commercial Cleared | Production Candidate? | Assessment & Terms |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Object Detection** | **YOLOX** | Megvii BaseDetection | Apache 2.0 | Apache 2.0 | **YES** | **YES** | Fully unencumbered. Anchor-free, permissively licensed open weights. Highly suitable for CPU ONNX deployment. |
| **Object Detection** | **RT-DETR** | Baidu PaddleDetection | Apache 2.0 | Apache 2.0 | **YES** | **YES** | Real-time transformer detector; Apache 2.0 code and weights. |
| **Multi-Object Tracking** | **ByteTrack** | ByteDance / ifzhang | MIT | MIT (N/A) | **YES** | **YES** | Pure motion-association algorithm based on Kalman filter + Hungarian algorithm; requires no pretrained CNN weights. |
| **ANPR / OCR** | **PP-OCRv4** | Baidu PaddleOCR | Apache 2.0 | Apache 2.0 | **YES** | **YES** | Compact MobileNet-based CRNN/SVTR architecture under Apache 2.0. Unrestricted commercial deployment. |
| **Pose / Fall** | **MediaPipe Pose** | Google | Apache 2.0 | Apache 2.0 | **YES** | **YES** | 33-landmark BlazePose topology; Apache 2.0 license on both model graph and weights. |
| **Crowd Density** | **Geometric Regressor** | Custom SARVANETRA | Apache 2.0 | N/A | **YES** | **YES** | Pure rule/geometry algorithm operating over bounding box count and zone area ($m^2$); zero weight encumbrance. |
| **Vehicle Classifier** | **ResNet-50 / MobileNetV3** | PyTorch Torchvision | BSD-3 / Apache 2.0 | Apache 2.0 | **YES** | **YES** | Standard ImageNet-1K pretrained weights released under open terms. |
| **Face Recognition** | **MobileFaceNet** | Sirius-AI / Open Source | Apache 2.0 | Apache 2.0 | **YES** | **YES** | Pretrained on synthetic or permissively cleared datasets. (InsightFace ArcFace is REJECTED due to non-commercial MS1MV2 dataset). |
| **Forecasting** | **Prophet / ARIMA** | Meta / Statsmodels | MIT / BSD-3 | N/A | **YES** | **YES** | Open mathematical time-series modeling. |

---

## 4. Discrepancy Between Documentation and Repository State
* In `docs/AI_MASTER_MISSION_REPORT.md` and `docs/AI_ARCHITECTURE_DECISION.md`, the AI perception layer is described as having adopted the permissive Apache-2.0 stack.
* In reality, `ai-platform/models/` contains **YOLOv8n ONNX models (AGPL-3.0)** because they are compact (13MB), easy to run in test environments, and natively supported by the custom ONNX detector.
* **Tender & Production Recommendation:**
  1. For field deployment and tender compliance, the platform MUST package YOLOX and PP-OCRv4 artifacts to maintain 100% Apache-2.0 / MIT compliance.
  2. The current YOLOv8n models must remain documented as **development/integration prototypes only**, strictly segregated from the commercial deliverable.
