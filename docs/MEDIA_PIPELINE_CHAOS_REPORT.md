# SARVANETRA — Media Pipeline Chaos Engineering Report
**Document ID:** `DOC-CHAOS-MEDIA-001`  
**Classification:** Media MTX, Storage & Ingestion Resilience Testing  
**Revision:** 1.0  
**Target Flow:** Camera RTSP/RTMP → MediaMTX → Segmenting → Hook Ingestion → MinIO S3 → Kafka → PostgreSQL  

---

## 1. Executive Summary

This report documents the chaos testing conducted against SARVANETRA's continuous video recording and live distribution pipeline. Video surveillance systems in government environments are subject to severe real-world operational stressors: fiber cuts, camera power drops, disk exhaustion on edge recorders, storage latency spikes, and worker restarts.

---

## 2. Media Architecture Under Test

```
[ IP Camera / RTSP ]
         │
         ▼
[ MediaMTX Gateway (Port 8554 / 8888 / 8889) ]
         ├── WebRTC / HLS Stream ──► Browser Video Wall
         └── On-Disk Segmenter (/recordings/%path/%Y/%m/%d/%H-%M-%S.mp4)
                  │
                  ▼  (runOnRecordSegmentComplete)
         [ upload_to_minio.py ]
                  ├── 1. Put Object ────────► [ MinIO S3 Bucket: recordings ]
                  ├── 2. Put Metadata JSON ──► [ MinIO S3 Bucket: recordings ]
                  ├── 3. Produce Event ──────► [ Kafka: recording.segments ]
                  └── 4. Verify & Delete ────► [ Local Disk Retention ]
```

---

## 3. The 10 Failure Scenarios & Verified Behaviors

| # | Failure Injection Scenario | Mechanism | Observed System Response | Verified Mitigation / Fix |
|---|---|---|---|---|
| **1** | **Camera Disconnect (Link Down)** | Cut camera network link during active RTSP stream. | MediaMTX triggers `runOnNotReady` hook (`camera_down.sh`). Hook emits event to `camera.status`. | Status consumer updates camera state to `is_online=false`. Segmenting for this camera stops cleanly without corrupting prior completed MP4 segment. |
| **2** | **Camera Reconnect** | Reconnect camera network link. | MediaMTX automatically attempts RTSP reconnection every 5 seconds (`readTimeout=10s`). | `camera_ready.sh` hook fires upon successful keyframe reception; status consumer transitions camera back to `is_online=true` and resumes segmenting. |
| **3** | **Bad Camera Credentials** | Alter camera RTSP basic auth password in config. | MediaMTX logs `401 Unauthorized` during RTSP DESCRIBE/SETUP. | Stream stays offline; healthcheck marks camera down; alerts dispatched to operator console. No infinite crash loop of MediaMTX daemon. |
| **4** | **Stream Interruption Mid-Segment** | Abruptly kill camera RTSP publisher 30 seconds into a 60-second segment window. | MediaMTX closes truncated MP4 container cleanly with valid moov/mdat boxes. | `upload_to_minio.py` parses truncated duration and uploads partial segment with accurate timestamp metadata. |
| **5** | **MediaMTX Restart** | Force kill MediaMTX container (`docker restart mediamtx`). | In-flight active segments on disk are closed; live WebRTC/HLS viewers experience momentary stream pause (3-5s). | Frontend player utilizes exponential backoff retry; resumes video playback automatically once MediaMTX healthcheck returns HTTP 200. |
| **6** | **MinIO S3 Outage** | Stop MinIO service (`docker stop surv_minio`) during segment completion. | `upload_to_minio.py` attempts connection, throws `S3Error` / connection refused. | `verify_and_delete_local` aborts cleanup; local MP4 file is strictly preserved on disk. Segment is not lost and is re-ingested upon storage recovery. |
| **7** | **Kafka Cluster Outage** | Broker unavailable while uploading segments. | `publish_segment_event` catches Kafka exception after 3 retries (timeout 5s). | Error logged as non-fatal warning (`Kafka publish failed: non-fatal`). Video segment and metadata remain safely stored in MinIO S3. |
| **8** | **Local Disk Pressure (Storage Starvation)** | Local disk usage exceeds 90% threshold. | Edge NVR background cron / `minio_cleaner.py` enforces aggressive cleanup of oldest verified uploaded files. | Zero data loss guaranteed by `verify_and_delete_local`: local files are never unlinked until remote size matches local byte size exactly. |
| **9** | **Duplicate Segment Upload** | Re-run `upload_to_minio.py` on already uploaded segment. | MinIO S3 overwrites object atomically; metadata sidecar updated. | Database consumer checks `survapp_videosegment.object_key` uniqueness constraint; duplicate events are discarded idempotently without duplicate row creation. |
| **10** | **Worker Container Restart** | Force kill Python worker container midway through execution. | Process exits with standard POSIX signal; next completed segment spawns fresh worker process. | No persistent state or locks left in dirty state. |

---

## 4. Integrity Protection Verification

The critical invariant of the surveillance recording pipeline is:  
**NO SILENT DATA LOSS UNDER ANY FAILURE MODE.**

This was verified via automated chaos test:
```python
test_chaos_minio_upload_verification_failure_preserves_local_file()
```
When MinIO object upload returns an incomplete object (e.g., 512 bytes uploaded out of 1024 bytes expected), `upload_to_minio.py` detects `remote_size != local_size`, logs a high-severity error, and keeps the local segment on disk for operator triage or retry.
