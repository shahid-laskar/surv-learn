# SARVANETRA — AI Hardware Capability & Environment Profile Audit
**Document ID:** `AI-HW-CAP-001`  
**Classification:** Hardware Discovery & Deployment Profiles  
**Date of Audit:** September 23, 2026  
**Auditor:** SARVANETRA Autonomous Engineering Team  

---

## 1. Local Development Environment Discovery

Actual measurements conducted via native OS telemetry:
* **Host CPU Architecture:** x86_64
* **Processor Model:** Intel(R) Core(TM) i3-4130 CPU @ 3.40GHz
* **Total Physical Cores / Threads:** 2 Cores / 4 Threads
* **Instruction Set Extensions:** SSE4.2, AVX2 (No AVX-512, No AMX)
* **System Memory (RAM):** 7.8 GiB Total (3.3 GiB used, 4.4 GiB available)
* **Swap Space:** 3.0 GiB
* **Local Primary Disk (`/dev/sda1`):** 99 GiB total (48 GiB used, 46 GiB free, 51% utilization)
* **Dedicated GPU:** None detected (`nvidia-smi` command not found; PCI bus reports integrated Intel HD Graphics 4400)
* **NVIDIA Driver / CUDA Runtime:** Not available
* **Docker Container Runtime:** Standard `runc` (Containerd v2); `nvidia-container-toolkit` not present.

---

## 2. Deployment Profiles Specification

To ensure SARVANETRA can function seamlessly across developer workstations, edge NVR appliances, and central command control data centers, four operational hardware profiles are established:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           SARVANETRA DEPLOYMENT PROFILES                         │
├────────────────────┬────────────────────┬───────────────────┬────────────────────┤
│ PROFILE 1: DEV CPU │ PROFILE 2: EDGE AI │ PROFILE 3: GPU LAB│ PROFILE 4: CENTRAL │
├────────────────────┼────────────────────┼───────────────────┼────────────────────┤
│ • Intel i3/i5/i7   │ • Rockchip RK3588  │ • NVIDIA RTX 4090 │ • 2x NVIDIA A100 / │
│ • 8 GB RAM         │   (6 TOPS NPU)     │   (24 GB VRAM)    │   L40S (48 GB VRAM)│
│ • No discrete GPU  │ • Jetson Orin Nano │ • 32 GB RAM       │ • Dual Intel Xeon  │
│ • ONNX Runtime CPU │ • RKNN / TensorRT  │ • TensorRT / CUDA │ • 128 GB RAM       │
│ • 1-2 Stream POI   │ • 4-8 Ingest RTSP  │ • 16-24 Streams   │ • 64-100 Streams   │
│ • Synthetic Sim    │ • Local ANPR + ROI │ • Full Analytics  │ • Central ICCC VMS │
└────────────────────┴────────────────────┴───────────────────┴────────────────────┘
```

### Profile 1: `AI_DEV_CPU` (Current Environment Baseline)
* **Primary Role:** Local unit testing, CI/CD pipeline execution, API contract verification, and synthetic event generation.
* **Target Runtimes:** ONNX Runtime (`CPUExecutionProvider`), OpenVINO CPU, OpenCV DNN.
* **Model Constraints:** Quantized INT8 / FP16 nano models (e.g., YOLOX-Nano, MobileNetV3, Fast-ANPR quantized, ByteTrack CPU).
* **Processing Cadence:** Frame-skipping mode (1 to 2 frames per second sampling).
* **Guaranteed Fallback:** Pure synthetic perception generator (`ai_simulator.py`) generating realistic detections for all 15 perception classes without CPU thermal throttling.

### Profile 2: `AI_EDGE` (Edge NVR Appliance / LPU Box)
* **Target Hardware:** Industrial edge appliance with dedicated Neural Processing Unit (e.g., Rockchip RK3588 with 6 TOPS NPU, NVIDIA Jetson Orin Nano 40 TOPS, or Hailo-8 M.2 module).
* **Target Workloads:** Lane-side ANPR (1-4 lanes), virtual perimeter intrusion tripwires, stationary loitering.
* **Storage Invariant:** SQLite local store-and-forward queue with Store-and-Forward sync to Central Hub over Headscale WireGuard overlay.
* **Power & Thermal:** Passive cooling, <25W power envelope.

### Profile 3: `AI_DEV_GPU` (Staging / AI Lab Node)
* **Target Hardware:** Single workstation GPU (NVIDIA RTX 3060 / 4070 / 4090 with 12GB to 24GB VRAM), 32 GB RAM, 8-core CPU.
* **Target Runtimes:** TensorRT 10.x, PyTorch with CUDA 12.x, ONNX Runtime (`CUDAExecutionProvider`).
* **Throughput:** 16-24 concurrent 1080p RTSP streams @ 10-15 FPS inference.
* **Supported Tasks:** Multi-class object detection, vehicle color/type classification, crowd density estimation.

### Profile 4: `AI_CENTRAL_GPU` (Tender Production ICCC Command Center)
* **Target Hardware:** Enterprise Rackmount Server (e.g., Dell PowerEdge R760xa / HPE ProLiant DL380a) with 2x to 4x NVIDIA L40S (48GB VRAM each) or NVIDIA A100/H100 GPUs, 256 GB RAM, redundant 10Gbps SFP+ networking.
* **Target Workloads:** Full statewide or district-wide multi-channel analytics:
  - 100+ concurrent live RTSP streams.
  - Continuous crowd density heatmap regression.
  - Multi-camera visitor journey tracking (ReID).
  - High-concurrency facial recognition vector search.
* **High Availability:** N+1 GPU server failover coordinated via Strimzi Kafka cluster and Kubernetes orchestrator.

---

## 3. Resource Governance & Thresholds for Current Node

To ensure the core VMS (MediaMTX, PostgreSQL, Kafka, MinIO) remains 100% stable while running AI services on the current development machine:
1. **CPU Limit for AI Worker Containers:** Capped at 2.0 cores max (`cpus: "2.0"`).
2. **Memory Limit for AI Worker Containers:** Capped at 1.5 GiB RAM max (`mem_limit: 1536m`) to prevent OS out-of-memory (OOM) killer from terminating PostgreSQL or MinIO.
3. **Queue Invariant:** In-memory frame queue capped at 10 frames per stream. If inference latency exceeds frame arrival rate, worker drops intermediate frames to guarantee live real-time processing and zero RAM bloat.
