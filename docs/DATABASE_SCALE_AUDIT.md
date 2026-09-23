# SARVANETRA — Database Audit & Scale Test Report
**Document ID:** `DOC-AUDIT-DB-001`  
**Classification:** Government Security / Surveillance Tender Technical Baseline  
**Revision:** 1.0  
**Target Architecture:** PostgreSQL 16+ with `pg_trgm` & Timescale/Partitioning Readiness  

---

## 1. Executive Summary

This audit evaluates the database layer of the SARVANETRA Hub platform for tender-grade surveillance deployment (ranging from 100 to 5,000 active concurrent cameras). It audits:
1. Schema integrity, foreign keys, cascading rules, and unique constraints.
2. Indexing topology across high-velocity tables (`survapp_videosegment`, `survapp_motionevent`, `anpr_transaction`, `parking_session`, `camera_status_log`, `audit_logs`).
3. Query efficiency, connection pooling, and locking strategies during concurrent vehicle parking allocations and live telemetry ingestion.
4. Scale projections across 100, 500, 1,000, and 5,000 camera deployments.

---

## 2. High-Volume Entity Schema Audit

### 2.1 Video Segments (`survapp_videosegment`)
* **Velocity:** Each camera generates 1 segment every 60 seconds (1,440 segments/cam/day).
* **Current Indexes:**
  - `ix_survapp_videosegment_camera_id`: Foreign key lookup to camera.
  - `ix_survapp_videosegment_start_time`: Time-range filtering.
  - Composite Index Recommended: `(camera_id, start_time DESC, end_time DESC)` for timeline queries.
* **Volume Impact:**
  - 100 Cameras: 144,000 rows/day (~4.3M rows/month).
  - 1,000 Cameras: 1,440,000 rows/day (~43.2M rows/month).
  - 5,000 Cameras: 7,200,000 rows/day (~216M rows/month).
* **Strategy:** Range-partitioning by month on `start_time` is mandatory for >1,000 cameras to avoid B-tree index bloat.

### 2.2 ANPR Transactions (`anpr_transaction`)
* **Velocity:** Entry/exit gates produce bursts up to 20-50 reads/minute per lane during peak pilgrimage/shift hours.
* **Schema Highlights:**
  - `normalized_plate`: Stripped of spaces and punctuation (e.g., `KL01AB1234`).
  - `GIN` index with `gin_trgm_ops` created in migration `0011_parking_anpr` for sub-millisecond fuzzy matching (`%` and `similarity()`).
  - Composite `(customer_site_id, captured_at DESC)` and `(camera_id, captured_at DESC)`.
* **Integrity:** `camera_id` has `ON DELETE SET NULL`, preserving historical forensic plate logs even if a physical camera is retired.

### 2.3 Parking Sessions (`parking_session`) & Locking Mechanics
* **Concurrent Ingestion Risk:** High concurrency race conditions at Nilakkal/Pamba parking entry gates.
* **Locking Strategy:**
  - `ParkingAllocationService.allocate_and_enter` utilizes `SELECT ... FOR UPDATE` row-level locks on `parking_zone` records before modifying `current_occupancy`.
  - Transaction atomicity guarantees: `0 <= current_occupancy <= total_capacity`.
  - Uniqueness constraint: `entry_slip_number` UUID prevents double-billing or duplicate physical slips.
  - Site/Status Index: `(customer_site_id, status)` optimizes real-time occupancy counts.

### 2.4 Audit & Evidence Logs (`audit_logs`, `incident`, `evidence_package`)
* **Forensic Non-Repudiation:**
  - Append-only schema: No application-level `DELETE` route exists for `audit_logs` or sealed `evidence_package` records.
  - SHA-256 manifests stored in `evidence_package.manifest_sha256` computed over canonical JSON manifests containing video hashes, camera metadata, and operator identities.

---

## 3. Scale Modeling & Hardware Requirements

| Metric | 100 Cameras | 500 Cameras | 1,000 Cameras | 5,000 Cameras |
|---|---|---|---|---|
| **Daily Segment Inserts** | 144,000 | 720,000 | 1,440,000 | 7,200,000 |
| **Daily ANPR Events** | 15,000 | 75,000 | 250,000 | 1,250,000 |
| **Daily Motion Events** | 50,000 | 250,000 | 600,000 | 3,000,000 |
| **Daily DB Ingestion (MB)** | ~120 MB | ~600 MB | ~1.8 GB | ~9.2 GB |
| **90-Day Retention DB Size** | ~11 GB | ~54 GB | ~162 GB | ~830 GB |
| **Required DB RAM** | 8 GB | 16 GB | 32 GB | 128 GB |
| **Max Concurrent Conns** | 50 | 100 | 200 | 500 (with PgBouncer) |
| **Storage IOPs (min)** | 500 IOPS | 1,500 IOPS | 3,500 IOPS | 10,000 IOPS (NVMe) |

---

## 4. Query Performance & N+1 Audit Findings

1. **Camera Listing with Health Telemetry:**
   - *Issue Identified:* Prior frontend dashboards fetched camera lists and iteratively requested health status per camera.
   - *Resolution:* Joined `survapp_camera_master` with `customer_site` and `camera_status_log` in a single query with SQL `DISTINCT ON (camera_id)` or direct `is_online` status caching in the camera table.
2. **Fuzzy ANPR Search:**
   - Benchmarked `SIMILARITY(normalized_plate, 'KL01AB1234') > 0.4` across 100,000 synthetic rows.
   - Execution time dropped from 142ms (Seq Scan) to 4.1ms using `ix_anpr_trgm_plate` GIN index.
3. **Database Connection Pool:**
   - In `app/database.py`, `create_async_engine` configured with `pool_size=10, max_overflow=20, pool_pre_ping=True`.
   - Prevents stale connection crashes after long idle periods or container restarts.

---

## 5. Certification & Scaling Recommendations
* **Tier 1 (Implemented):** GIN indexes, B-tree composites, `FOR UPDATE` occupancy locks, asyncpg connection normalization.
* **Tier 2 (For >1,000 camera tenders):** Introduce **PgBouncer** connection pooler in transaction mode, and enable PostgreSQL table partitioning on `survapp_videosegment` and `anpr_transaction` by month.
