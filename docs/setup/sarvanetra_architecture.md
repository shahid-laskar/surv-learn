# Sarvanetra — Server Architecture
**Standalone Reference Page**
*Classification: Internal — Not for Public Distribution*

---

## Overview

Sarvanetra runs as a single-server deployment composed of purpose-built, containerised services orchestrated by Docker Compose. Every component is open-source, runs on a standard Linux host, and communicates over a private internal Docker network. The server receives no public IP address — it operates entirely within the BSNL surveillance VLAN (see network brief).

The architecture is deliberately layered: cameras talk only to the media layer, the media layer writes only to storage, events flow only through the message bus, and clients reach everything only through the API gateway. No component is directly exposed without authentication.

---

## Server Hardware Baseline

| Resource | Minimum | Recommended |
|---|---|---|
| CPU | 4 cores (x86_64) | 8+ cores |
| RAM | 8 GB | 16–32 GB |
| OS Disk | 50 GB SSD | 100 GB SSD |
| Recording Storage | 2 TB HDD | 4–8 TB HDD RAID |
| Network NIC | 1 Gbps | 1 Gbps (dedicated to VLAN 200) |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

GPU/hardware transcoding is optional and only needed if simultaneous re-encoding of more than 8 streams is required.

---

## Service Map

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        SARVANETRA SERVER (Docker Host)                       │
│                        Private IP: 10.100.x.x  (BSNL VLAN 200)              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                   CLIENT-FACING LAYER                                   │ │
│  │                                                                         │ │
│  │   ┌──────────────────────────────────────────────────────────────────┐  │ │
│  │   │           Kong API Gateway   (:8000 HTTP / :8443 HTTPS)          │  │ │
│  │   │   JWT validation · Rate limiting · Route proxying · ACL          │  │ │
│  │   │   Admin UI: Konga (:1337)                                        │  │ │
│  │   └───────────┬─────────────────┬──────────────────┬────────────────┘  │ │
│  └───────────────│─────────────────│──────────────────│────────────────────┘ │
│                  │                 │                  │                       │
│  ┌───────────────▼──┐  ┌───────────▼──────┐  ┌───────▼──────────────────┐   │
│  │  APPLICATION     │  │  MEDIA DELIVERY  │  │  OBJECT STORAGE          │   │
│  │                  │  │                  │  │                          │   │
│  │  Django / FastAPI│  │  Nginx HLS Proxy │  │  MinIO  (:9000)          │   │
│  │  (:8000 internal)│  │  (:8080)         │  │  Console (:9001)         │   │
│  │                  │  │                  │  │                          │   │
│  │  REST API        │  │  Serves HLS .m3u8│  │  Buckets:                │   │
│  │  Dashboard UI    │  │  & .ts segments  │  │  · recordings/           │   │
│  │  JWT issuance    │  │  from shared vol │  │  · snapshots/            │   │
│  │  Timeline API    │  │                  │  │                          │   │
│  └──────┬───────────┘  └─────────┬────────┘  └──────────────┬───────────┘   │
│         │                        │                           │               │
│  ┌──────▼───────────────────┐    │                           │               │
│  │  DATA LAYER              │    │                           │               │
│  │                          │    │                           │               │
│  │  PostgreSQL (:5432)      │    │                           │               │
│  │  · camera_master         │    │                           │               │
│  │  · motion_event          │    │                           │               │
│  │  · video_segment         │    │                           │               │
│  │  · camera_status_log     │    │                           │               │
│  │  · kong (API GW config)  │    │                           │               │
│  │                          │    │                           │               │
│  │  Redis (:6379)           │    │                           │               │
│  │  · session cache         │    │                           │               │
│  │  · API response cache    │    │                           │               │
│  └──────────────────────────┘    │                           │               │
│                                  │                           │               │
│  ┌───────────────────────────────▼───────────────────────────▼─────────────┐ │
│  │                     MEDIA INGESTION LAYER                               │ │
│  │                                                                         │ │
│  │   MediaMTX Media Server                                                 │ │
│  │   · RTSP Ingest     :8554   ← cameras push here                        │ │
│  │   · HLS Output      :8888   → Nginx reads from shared volume           │ │
│  │   · WebRTC Output   :8889   → browser direct (sub-second latency)      │ │
│  │   · Management API  :9997   ← workers query stream health              │ │
│  │   · Records to /recordings volume (1-min fmp4 segments)                │ │
│  │   · Writes HLS .ts + .m3u8 to /hls volume                              │ │
│  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                     KAFKA EVENT BUS  (:9092, KRaft mode)                │ │
│  │                                                                         │ │
│  │   Topics:                                                               │ │
│  │   · camera.motion      — motion start/end events from ONVIF cameras    │ │
│  │   · camera.status      — online/offline state changes                  │ │
│  │   · recording.segments — segment upload completion metadata            │ │
│  │                                                                         │ │
│  └──────┬──────────────────────┬──────────────────────┬───────────────────┘ │
│         │                      │                      │                      │
│  ┌──────▼──────────┐  ┌────────▼────────┐  ┌─────────▼──────────────────┐  │
│  │  ONVIF PRODUCER │  │ MOTION CONSUMER │  │  WORKER POOL               │  │
│  │  (×2 instances) │  │  (×2 instances) │  │                            │  │
│  │                 │  │                 │  │  Upload Worker             │  │
│  │  Polls cameras  │  │  Reads          │  │  · /recordings → MinIO     │  │
│  │  via ONVIF SOAP │  │  camera.motion  │  │  · publishes segment events│  │
│  │  Publishes to   │  │  Writes to      │  │                            │  │
│  │  camera.motion  │  │  motion_event   │  │  Status Monitor            │  │
│  │  topic          │  │  table (PG)     │  │  · pings MediaMTX API      │  │
│  │                 │  │                 │  │  · publishes camera.status │  │
│  │                 │  │                 │  │                            │  │
│  │                 │  │                 │  │  MinIO Cleaner             │  │
│  │                 │  │                 │  │  · deletes old recordings  │  │
│  │                 │  │                 │  │  · enforces retention days │  │
│  └─────────────────┘  └─────────────────┘  └────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

External:  IP Cameras (RTSP :554 / ONVIF :80)  →  Server :8554
Clients:   Browser / Monitoring Workstation     →  Server :8000 (via Kong)
```

---

## Component Breakdown

### Kong API Gateway
The single, authenticated entry point for all client traffic. No internal service port is reachable from the network directly — everything goes through Kong. Kong validates JWT tokens on every API request, enforces rate limits, and proxies to the correct upstream service. The Konga web UI allows administrators to manage routes and consumers without touching configuration files.

### Django / FastAPI Application
The central management brain. It provides the REST API for camera registration, stream token generation, timeline queries, motion event retrieval, and user management. It is the only service that writes to PostgreSQL via its ORM. It does not handle video data — it generates URLs that point clients directly to Nginx or MinIO.

### MediaMTX Media Server
Receives RTSP streams from cameras and simultaneously converts them into HLS (for browser playback), WebRTC (for near-zero-latency monitoring), and on-disk recordings. A single MediaMTX instance can handle 20–50 concurrent camera streams comfortably on recommended hardware. It exposes a management REST API on port 9997 that workers use to check which camera paths are actively publishing.

### Nginx HLS Proxy
A lightweight Nginx instance that reads pre-generated HLS segments from the shared `hls_segments` Docker volume and serves them to browser players. By separating HLS delivery from MediaMTX, multiple clients can watch the same stream without adding load to the media server. Nginx also caches segment files, reducing disk I/O under concurrent viewers.

### MinIO Object Storage
An S3-compatible object store running locally on the server's recording disks. Stores all video segments (`.mp4` / `.fmp4`) under the `recordings` bucket and camera snapshots under `snapshots`. The application generates time-limited presigned URLs for playback so video data flows directly from MinIO to the client without passing through Django. A lifecycle policy automatically deletes objects older than the configured retention period (default: 30 days).

### Apache Kafka (KRaft Mode)
The internal message bus decoupling event producers from consumers. Running in KRaft mode means no Zookeeper dependency — a single Kafka broker handles all three topics with replayed delivery, consumer group offset tracking, and configurable retention. If a consumer crashes and restarts, it picks up exactly where it left off with no event loss.

### ONVIF Producers (×2)
Python workers that subscribe to camera motion events using the ONVIF event pull-point mechanism (SOAP over HTTP). Each instance manages a subset of active cameras discovered from the database. Two instances provide redundancy — if one crashes, the other continues processing its assigned cameras. They publish structured JSON events to the `camera.motion` Kafka topic.

### Motion Event Consumers (×2)
Python workers that consume from `camera.motion` and write motion start/end records to the `motion_event` PostgreSQL table. Two instances form a Kafka consumer group — Kafka distributes partitions between them for parallel processing. This table is what the dashboard queries to show motion alerts and event history.

### Upload Worker
Watches the `/recordings` volume for completed video segments (stabilised files not modified for 5+ seconds), uploads them to MinIO with their camera path preserved in the object key, marks them as uploaded, and publishes a `recording.segments` event so the database consumer can create the `video_segment` row that powers the timeline API.

### Status Monitor
Periodically checks each camera's liveness by querying the MediaMTX management API and attempting a TCP connection to the camera's RTSP port. On status change (online → offline or vice versa), it publishes a `camera.status` event and updates the `camera_master` table directly so the dashboard reflects the current state without waiting for a Kafka consumer cycle.

### MinIO Cleaner
A scheduled worker that runs every 6 hours, lists all objects in the `recordings` bucket, and deletes those whose `LastModified` timestamp exceeds the `RETENTION_DAYS` threshold. It also marks the corresponding `video_segment` rows as deleted in PostgreSQL, keeping the timeline API consistent with actual storage.

### PostgreSQL
The single source of truth for all persistent state: camera configurations, motion events, recording segment metadata, camera status logs, user accounts, and Kong's API gateway configuration (stored in a separate `kong` database on the same instance). All Django ORM migrations are applied automatically on container startup.

### Redis
In-memory store used by Django for session management, API response caching (camera list, stream token responses), and optionally as a Celery task broker if background jobs are introduced later.

---

## Data Flows

**Live Stream (low latency path)**
```
Camera → RTSP push → MediaMTX :8554
MediaMTX → writes HLS segments → /hls volume (shared)
Browser → GET /hls/cam_001/index.m3u8 → Kong → Nginx → reads /hls volume → serves .ts files
```

**Recording (storage path)**
```
MediaMTX → writes 1-min fmp4 → /recordings volume
Upload Worker → detects stable file → uploads → MinIO recordings bucket
Upload Worker → publishes event → Kafka recording.segments
Segment DB Consumer → reads event → inserts video_segment row → PostgreSQL
Browser → GET /api/v1/recordings/cam_001/timeline → Kong → Django → queries video_segment
Django → generates presigned URL → returns to browser
Browser → fetches video directly from MinIO presigned URL
```

**Motion Event (detection path)**
```
Camera → ONVIF PullMessages → ONVIF Producer
Producer → parses IsMotion=true/false → publishes JSON → Kafka camera.motion
Motion Consumer → reads event → writes/updates motion_event row → PostgreSQL
Dashboard → GET /api/v1/motion/?camera_id=1 → Kong → Django → queries motion_event → returns list
```

**Camera Health (monitoring path)**
```
Status Monitor → queries MediaMTX API :9997 every 30s
MediaMTX path ready=true/false → Status Monitor detects change
Status Monitor → publishes camera.status event → Kafka
Status Monitor → updates camera_master.is_online directly → PostgreSQL
Dashboard → GET /api/v1/health/cameras/ → Kong → Django → returns status summary
```

---

## Docker Volume Layout

| Volume | Type | Contents | Consumers |
|---|---|---|---|
| `hls_segments` | tmpfs / fast disk | Live HLS `.m3u8` + `.ts` files | MediaMTX (write), Nginx (read) |
| `recordings` | large HDD | Raw `.fmp4` / `.mp4` segments | MediaMTX (write), Upload Worker (read→delete after upload) |
| `minio_data` | large HDD | MinIO object store buckets | MinIO only |
| `postgres_data` | SSD | PostgreSQL data directory | PostgreSQL only |
| `redis_data` | SSD | Redis AOF persistence | Redis only |

---

## Port Reference

| Port | Protocol | Service | Accessible From |
|---|---|---|---|
| 8000 | HTTP | Kong Proxy (→ all API/UI traffic) | VLAN 200 clients |
| 8443 | HTTPS | Kong Proxy (TLS) | VLAN 200 clients |
| 8554 | RTSP | MediaMTX camera ingest | IP cameras on VLAN 200 |
| 8080 | HTTP | Nginx HLS (via Kong) | VLAN 200 clients |
| 8889 | HTTP/WS | MediaMTX WebRTC (via Kong) | VLAN 200 clients |
| 9000 | HTTP | MinIO S3 API (via Kong) | VLAN 200 clients, workers (internal) |
| 1337 | HTTP | Konga Admin UI | Admin workstation on VLAN 200 |
| 8001 | HTTP | Kong Admin API | Localhost / admin only |
| 9001 | HTTP | MinIO Console | Localhost / admin only |
| 9997 | HTTP | MediaMTX Management API | Internal Docker network only |
| 5432 | TCP | PostgreSQL | Internal Docker network only |
| 6379 | TCP | Redis | Internal Docker network only |
| 9092 | TCP | Kafka | Internal Docker network only |

Ports marked "Internal Docker network only" are never exposed on the host — they are accessible only between containers on the `surv_net` bridge network.

---

## Service Startup Order

```
PostgreSQL ──┐
             ├──► Kong Migration ──► Kong ──► Kong Config
Redis ───────┘
             │
Kafka ───────┼──► Kafka Init (topic creation)
             │        │
MinIO ───────┼──► MinIO Init (bucket creation)
             │        │
             ├──► Django / FastAPI (waits for PG + Redis)
             │
MediaMTX ────┼──► Nginx HLS Proxy (waits for MediaMTX)
             │
             ├──► ONVIF Producers (waits for Kafka + PG)
             ├──► Motion Consumers (waits for Kafka + PG)
             ├──► Upload Worker (waits for Kafka + MinIO + PG)
             ├──► Status Monitor (waits for Kafka + PG + MediaMTX)
             └──► MinIO Cleaner (waits for MinIO)
```

All services use Docker health checks and `depends_on: condition: service_healthy` to enforce this order automatically. No manual sequencing is required after initial `docker compose up`.

---

## Scalability Notes

The architecture is intentionally designed for single-server deployment within the BSNL intranet constraint. Horizontal scaling is possible without redesign:

- **More cameras:** Additional ONVIF producer instances can be added (each manages a camera subset). MediaMTX handles 50+ streams on recommended hardware.
- **More storage:** Additional disks mounted into `minio_data` — MinIO supports erasure coding for multi-disk configurations.
- **More viewers:** Nginx HLS serving is stateless and can be load-balanced if needed.
- **Multi-site:** Additional servers at other BSNL VLAN 200 nodes can each run their own MediaMTX + Upload Worker stack, pointing their cameras and workers to the central PostgreSQL and MinIO on the primary server via the BSNL backbone.

---

*Prepared by: Development Team — Sarvanetra Project*
*For review and approval by Technical Manager*