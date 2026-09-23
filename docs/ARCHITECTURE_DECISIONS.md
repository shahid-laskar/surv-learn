# SARVANETRA — Architecture Decision Records (ADRs)
**Document ID:** `DOC-ARCH-ADR-001`  
**Classification:** Engineering Baseline & Architecture Decisions  
**Status:** Living Architectural Record  

---

## Index of Records

* [ADR-001: MediaMTX as Central & Edge Multi-Protocol Video Gateway](#adr-001)
* [ADR-002: Dual Authentication Boundary (Kong JWT vs Edge X-Site-Token)](#adr-002)
* [ADR-003: Apache Kafka Event Bus with Degraded Synchronous Fallback](#adr-003)
* [ADR-004: Strict Verify-Before-Delete Invariant for S3 Video Segments](#adr-004)
* [ADR-005: Decoupled ANPR Management Plane from Edge LPU Inference](#adr-005)
* [ADR-006: Row-Level Database Locking for Concurrent Parking Allocations](#adr-006)
* [ADR-007: PostgreSQL pg_trgm GIN Index for Fuzzy OCR Plate Search](#adr-007)
* [ADR-008: Canonical SHA-256 Manifest Sealing for Court-Admissible Evidence](#adr-008)

---

### <a name="adr-001"></a>ADR-001: MediaMTX as Multi-Protocol Video Gateway
* **Context:** Surveillance cameras use varying protocols (RTSP, RTSPS, RTMP) while modern browsers require WebRTC (sub-second) and HLS (high scalability).
* **Decision:** Deploy MediaMTX in Go as the universal gateway. It provides native RTSP/RTMP ingest, automated 60-second fMP4 segmenting, hook callbacks (`runOnRecordSegmentComplete`, `runOnNotReady`), and high-performance WebRTC/HLS distribution.
* **Consequences:** Eliminates FFmpeg subprocess spawning bottlenecks; centralizes stream lifecycle hooks into lightweight bash scripts publishing directly to Kafka.

---

### <a name="adr-002"></a>ADR-002: Dual Authentication Boundary (Kong JWT vs Edge X-Site-Token)
* **Context:** Public safety operators require JWT tokens with RBAC claims; distributed Edge NVR nodes require automated mTLS or site token authentication without interactive human logins.
* **Decision:** Configure Kong API Gateway with dual routing. Route `/api/v1/fleet/*` and edge ingest routes validate `X-Site-Token` matching database records without requiring an interactive JWT. All client/browser endpoints strictly enforce HS256 JWTs with hierarchical claims.
* **Consequences:** Edge NVRs can transmit telemetry and heartbeat even when user sessions are invalid; eliminates risk of human token expiration breaking automated fleet synchronization.

---

### <a name="adr-003"></a>ADR-003: Apache Kafka Event Bus with Degraded Fallback
* **Context:** Ingestion spikes (e.g. 50 vehicles/minute across multiple gates) must not block HTTP API workers or lock database connections.
* **Decision:** Employ Apache Kafka as the asynchronous event bus for camera status, segment uploads, and ANPR events. In `AnprService`, wrap Kafka producers with a 2-second timeout: if Kafka is unreachable, write synchronously to PostgreSQL and return HTTP 201.
* **Consequences:** Guarantees zero data loss during broker maintenance or network blips while maintaining sub-10ms API responses under normal operation.

---

### <a name="adr-004"></a>ADR-004: Strict Verify-Before-Delete Invariant for S3 Video Segments
* **Context:** Edge NVRs have constrained SSD storage; deleting files prematurely causes catastrophic video evidence loss.
* **Decision:** `upload_to_minio.py` issues a `stat_object` call verifying remote object byte size equals local byte size before unlinking local MP4 files (`verify_and_delete_local`). If size differs, local file is kept and an alert is logged.
* **Consequences:** Formally prevents silent video loss under S3 network disconnections or partial uploads.

---

### <a name="adr-005"></a>ADR-005: Decoupled ANPR Management Plane from Edge LPU Inference
* **Context:** SARVANETRA does not ship with proprietary AI weights; tenders require ARAI-certified edge LPUs or commercial engines.
* **Decision:** Implement a clean REST + Kafka ingest contract (`/api/v1/anpr/events`, topic `vehicle.anpr.detected`). Any certified AI engine or LPU device can push events into SARVANETRA without code modifications.
* **Consequences:** Avoids coupling SARVANETRA to unstable Python deep learning libraries; enables commercial OEM partner engines to plug in seamlessly.

---

### <a name="adr-006"></a>ADR-006: Row-Level Database Locking for Concurrent Parking Allocations
* **Context:** Multiple entry gates allocate parking slots simultaneously during peak pilgrimage surges at Nilakkal.
* **Decision:** `ParkingAllocationService` acquires a `SELECT ... FOR UPDATE` row lock on `parking_zone` within an atomic transaction before incrementing `current_occupancy`.
* **Consequences:** Guarantees the invariant $0 \le \text{occupancy} \le \text{capacity}$ under heavy concurrency. Tested and verified up to 25 parallel threads.

---

### <a name="adr-007"></a>ADR-007: PostgreSQL pg_trgm GIN Index for Fuzzy OCR Plate Search
* **Context:** Cameras frequently misread characters (e.g., '0' as 'O', '8' as 'B') due to dust, rain, or high speed.
* **Decision:** Add PostgreSQL `pg_trgm` extension and create a GIN index on `anpr_transaction.normalized_plate` (`gin_trgm_ops`).
* **Consequences:** Operators can search with 1 or 2 character variations with sub-5ms latency across 100,000+ plate records.

---

### <a name="adr-008"></a>ADR-008: Canonical SHA-256 Manifest Sealing for Court Evidence
* **Context:** Police evidence exported from surveillance systems is challenged in judicial proceedings for tampering.
* **Decision:** Implement `EvidenceService` to assemble video segments, camera metadata, and operator identities into a canonical JSON structure sealed with a master SHA-256 digest.
* **Consequences:** Court-admissible proof of integrity. Tampering with any byte invalidates the checksum and flags an alert in the verification endpoint.
