# SARVANETRA — AI Platform Setup & Installation Guide
**Document ID:** `AI-SETUP-001`  
**Classification:** Operational Installation Runbook  
**Audience:** Systems Engineers, ML Engineers, DevOps  

---

## 1. Prerequisites

* **Operating System:** Ubuntu 22.04 LTS / Debian 12 / RHEL 9 (Linux x86_64 or ARM64)
* **Python Runtime:** Python 3.10+ (Current deployment: Python 3.13)
* **Container Runtime:** Docker Engine 24+ and Docker Compose v2
* **Storage:** Minimum 5 GB free disk space for models and virtual environments
* **Network:** Local host ports 8554 (RTSP), 9092 (Kafka), 9000 (MinIO), 8000 (Kong/FastAPI)

---

## 2. Environment Setup

### 2.1 Virtual Environment Initialization
```bash
cd /opt/surv-learn/surv
# Activate the platform virtual environment
source .venv/bin/activate
```

### 2.2 Installing AI & Vision Dependencies
```bash
pip install numpy onnxruntime opencv-python-headless shapely kafka-python-ng pydantic
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install ultralytics
```

### 2.3 Verify Hardware & ONNX Execution Provider
```bash
python3 -c "
import onnxruntime as ort
import torch
print('ONNX Runtime Providers:', ort.get_available_providers())
print('Torch Version:', torch.__version__, '| CUDA Available:', torch.cuda.is_available())
"
# Expected on CPU: ['CPUExecutionProvider']
```

---

## 3. Model Weights Provisioning

Export standard lightweight ONNX detection models into `ai-platform/models/`:
```bash
cd /opt/surv-learn
PYTHONPATH=. surv/.venv/bin/python3 -c "
from ultralytics import YOLO
import os
os.makedirs('ai-platform/models', exist_ok=True)
model = YOLO('yolov8n.pt')
model.export(format='onnx', imgsz=320, simplify=True)
os.rename('yolov8n.onnx', 'ai-platform/models/yolov8n_320.onnx')
print('Model exported to ai-platform/models/yolov8n_320.onnx')
"
```

---

## 4. Verification Test
```bash
cd /opt/surv-learn
PYTHONPATH=. surv/.venv/bin/pytest ai-platform/tests/
```
Expected output:
```text
12 passed in 6.95s
```
