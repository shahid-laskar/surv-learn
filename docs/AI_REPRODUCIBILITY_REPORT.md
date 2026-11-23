# SARVANETRA AI Platform v0.1 — Reproducibility Audit Report
**Document ID:** `AI-REP-001`  
**Date:** September 23, 2026  
**Auditor:** Independent Acceptance & Integration Inspector  
**Baseline Commit:** `8dd245c`  

---

## 1. Reproducibility Assessment Overview
To validate whether a new engineer can reliably reproduce the AI perception layer from scratch without relying on undocumented local host state, an end-to-end audit was conducted following `docs/AI_SETUP.md` and `docs/final_acceptance_test.md`.

### Verdict: **CONDITIONAL / DEFECTS DETECTED**
The AI platform test suite passes in the pre-configured local virtual environment (`surv/.venv`), but a clean-room engineer faces multiple severe reproducibility hurdles when following the repository documentation or attempting containerized execution.

---

## 2. Detailed Dimension Audit

### 2.1 Python Environment & Dependency Specifications
* **Virtual Environment Coupling:** `ai-platform/` does not possess its own independent virtual environment configuration, `pyproject.toml`, or `setup.py`. It relies entirely on the monolithic environment located at `surv/.venv`.
* **Missing `requirements.txt`:** While `docs/AI_SETUP.md` documents ad-hoc `pip install` commands, there was no pinned `requirements.txt` inside `ai-platform/`.
* **Python Version Compatibility:** The system and `surv/.venv` run **Python 3.13.5**. However, `ai-platform/Dockerfile.ai` is pinned to `python:3.11-slim-bullseye`.
* **Runtime vs Export Dependencies:** `AI_SETUP.md` prescribes installing heavy build-time packages (`torch`, `torchvision`, `ultralytics`) solely to re-export YOLO models, even though lightweight inference only requires `numpy`, `onnxruntime`, `opencv-python-headless`, and `shapely`.

### 2.2 Docker Containerization Failure (Verified Runtime Defect)
* **Execution Test:**
  ```bash
  docker build -t test-ai-platform -f ai-platform/Dockerfile.ai ai-platform/
  ```
* **Observed Runtime Failure:**
  ```text
  ------
   > [4/6] COPY requirements.txt .:
  ------
  Dockerfile.ai:16
  ERROR: failed to build: failed to solve: failed to compute cache key: "/requirements.txt": not found
  ```
* **Root Cause:** Line 16 of `ai-platform/Dockerfile.ai` attempts to `COPY requirements.txt .`, but no `requirements.txt` exists in `ai-platform/`. This container image cannot be built by any engineer or CI/CD runner from commit `8dd245c`.

### 2.3 Package Naming and Module Resolution
* **Hyphenated Directory Name:** The source directory is named `ai-platform/`. In standard Python, hyphenated module names (`ai-platform`) are invalid syntax for imports (`import ai-platform` triggers a syntax error).
* **Tracked Symlink Workaround:** The codebase circumvents this by tracking a symbolic link in git: `ai_platform -> ai-platform`.
* **Portability Hazard:** While functional on POSIX Linux environments, git checkouts on Windows systems with default permissions (or where `core.symlinks=false`) check out symlinks as plain text files, causing immediate `ModuleNotFoundError: No module named 'ai_platform'` on test execution.

### 2.4 Model Artifact Reproducibility
* **Present in Git:**
  * `ai-platform/models/yolov8n_320.onnx` (12.7 MB, sha256: `e33be869d4b9...`)
  * `ai-platform/models/yolov8n_pose_320.onnx` (13.1 MB, sha256: `1cd09ef2e01c...`)
  * These are tracked in git and can be loaded offline without downloading from external servers.
* **Missing Models Declared in Configuration:**
  * `ai-platform/config/model_registry.yaml` lists:
    * `models/yolox_s.onnx` (sha256: `9f86d08188...`)
    * `models/ch_PP-OCRv4_rec_infer.onnx` (sha256: `5e884898da...`)
  * Neither model exists anywhere in the repository. Attempting to initialize pipelines referencing these models fails unless fallback to YOLOv8n occurs.

### 2.5 ONNX Runtime & OpenCV Execution
* **Available Execution Providers:** Only `['CPUExecutionProvider']` is present. No CUDA, TensorRT, or OpenVINO execution providers are available.
* **ONNX Compatibility:** Both tracked ONNX models initialize cleanly under ONNX Runtime 1.30.0 with 320x320 inputs.
* **OpenCV:** `opencv-python-headless` 5.0.0.93 functions properly without X11 or GUI display dependencies.

### 2.6 Kafka & MQTT Integration Reproducibility
* **Kafka Dependency:** `kafka-python-ng` 2.2.3 is installed in `surv/.venv`.
* **Degraded Mode:** When Kafka (`surv_kafka:9092`) is offline, `AiEventGateway` handles the connection error without crashing, opening its circuit breaker.
* **MQTT:** `FrigateMqttAdapter` operates as an in-memory JSON normalizer (`normalize_and_publish`) and does not require an active MQTT daemon or `paho-mqtt` socket during unit tests.

---

## 3. Required Remediation for Full Reproducibility
1. Add a pinned `ai-platform/requirements.txt` containing all runtime dependencies (`numpy`, `onnxruntime`, `opencv-python-headless`, `shapely`, `pydantic`, `kafka-python-ng`).
2. Fix `ai-platform/Dockerfile.ai` build context so Docker container builds reproducibly.
3. Provide a proper `pyproject.toml` or package setup in `ai-platform/` so `pip install -e .` works portably without requiring manual symlink resolution.
4. Harmonize `model_registry.yaml` to reflect the actual model artifacts present on disk.
