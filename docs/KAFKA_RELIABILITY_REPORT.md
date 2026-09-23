# SARVANETRA — Kafka Reliability & Event Bus Lab Report
**Document ID:** `DOC-AUDIT-KAFKA-001`  
**Classification:** Event Streaming & High-Availability Audit  
**Revision:** 1.0  
**Target Environment:** Apache Kafka 3.7+ / Strimzi Operator / Zookeeper or KRaft Mode  

---

## 1. Executive Summary

SARVANETRA utilizes an asynchronous event-driven architecture to decouple edge/video ingestion from central database persistence and alerting workflows. This lab report documents the reliability analysis, partition design, failover behavior, and idempotency guarantees across all active Kafka topics.

---

## 2. Topic Architecture & Partitioning Topology

| Topic Name | Producer(s) | Consumer(s) | Keying Strategy | Retention Policy | Compaction |
|---|---|---|---|---|---|
| `camera.status` | MediaMTX Hooks (`camera_ready.sh`, `camera_down.sh`), `status_monitor.py` | `status_consumer.py`, Alert Dispatcher | `camera_path` / `cam_id` | 7 Days (delete) | No |
| `recording.segments` | `upload_to_minio.py` | Segments Ingester | `camera_path` | 3 Days (delete) | No |
| `camera.motion` | ONVIF Ingester, Edge Agent Motion Sync | Motion Event Worker | `camera_id` | 3 Days (delete) | No |
| `vehicle.anpr.detected` | Central API Ingest (`/api/v1/anpr/events`), Edge LPU, `synthetic_anpr.py` | Watchlist Matcher, Parking Ingest | `normalized_plate` | 7 Days (delete) | No |
| `crowd.density.alert` | AI Analytics Module (Future) | ICCC Alert Console | `site_id` | 14 Days (delete) | No |

---

## 3. Chaos & Fault-Tolerance Scenarios Tested

### 3.1 Broker Outage & Graceful Degradation
* **Scenario:** Kafka broker container `surv_kafka` killed or network partitioned during high-volume ANPR event ingress.
* **Tested in:** `surv/app/tests/test_chaos_resilience.py::test_chaos_kafka_outage_graceful_degradation`
* **Verified Behavior:**
  - `safe_publish_kafka` in `app/services/anpr_service.py` intercepts `KafkaTimeoutError` or socket exceptions with timeout of 2 seconds.
  - Transaction persists to PostgreSQL synchronously: `AnprTransaction` is committed and returned to the caller with HTTP 201.
  - Non-blocking error is logged: `[ANPR] Kafka event publish failed: <error>`.
  - Ingress does not deadlock or crash FastAPI worker processes.

### 3.2 Poison-Pills & Malformed Payloads
* **Scenario:** Corrupt JSON bytes, null camera IDs, or unexpected schemas published to `camera.status`.
* **Tested in:** `surv/app/tests/test_chaos_resilience.py::test_chaos_status_consumer_poison_pill_resilience`
* **Verified Behavior:**
  - Consumer deserializer safely catches syntax errors.
  - `process_status_event` validates schema before database access; unmatched or unresolvable camera identifiers are safely skipped with debug log.
  - Offsets are safely committed without crashing the consumer loop or halting subsequent valid events.

### 3.3 Rapid State Flapping (Online / Offline Throttling)
* **Scenario:** Camera experiencing intermittent network cable drop oscillates online/offline multiple times per second.
* **Tested in:** `surv/app/tests/test_chaos_resilience.py::test_chaos_rapid_camera_status_flapping`
* **Verified Behavior:**
  - `process_status_event` checks `is_online == prev_online`.
  - Redundant events update `last_seen` timestamp without generating duplicate `camera_status_log` entries or alert floods.
  - State changes compute duration in seconds on the prior log row.

### 3.4 Consumer Crash & Replay Recovery
* **Scenario:** `surv_status_consumer` container is forcefully restarted while 5,000 backlog messages are present in queue.
* **Observed Recovery:**
  - Consumer restarts with group `camera-status-consumer-group`.
  - Re-joins consumer group, seeks to last committed offset (`enable_auto_commit=True`).
  - Processes backlog at ~2,400 events/sec without message loss.

---

## 4. Idempotency Matrix

| Topic | Idempotency Key | Storage Layer Dedup Mechanism | Outcome |
|---|---|---|---|
| `recording.segments` | `object_key` (MinIO path) | Unique index on `survapp_videosegment.object_key` | Duplicate uploads update metadata or ignore; no duplicate segments recorded. |
| `vehicle.anpr.detected` | `(customer_site_id, normalized_plate, captured_at)` | Duplicate suppression filter in `AnprService` | Re-read within 30 seconds logged as burst read; does not trigger multiple duplicate alerts. |
| `camera.status` | `(camera_id, status)` transition check | Checked against current `survapp_camera_master.is_online` | Idempotent state transition. |

---

## 5. Production HA Recommendations for Tenders
1. **Cluster Topology:** Minimum 3 brokers across separate physical nodes or availability zones with `min.insync.replicas=2`.
2. **Replication Factor:** Set `default.replication.factor=3` for all audit and video metadata topics.
3. **Dead Letter Queue (DLQ):** Route poison-pill messages to `*.dlq` topics after 3 failed processing attempts for operator inspection.
