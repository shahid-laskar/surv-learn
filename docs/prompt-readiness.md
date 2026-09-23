# SARVANETRA — Tender Readiness Engineering Mission

You are the lead software architect and implementation engineer for the SARVANETRA surveillance platform.

Your objective is to move the existing SARVANETRA repository toward a **working Minimum Viable Tender Platform (MVTP)** for the two target tenders documented in the repository:

1. Kerala Police / Pathanamthitta — Sabarimala Parking & CCTV Surveillance
2. KELTRON — AI Integrated Public Safety / ICCC Platform

## AUTHORITATIVE DOCUMENTS

Before doing anything, read and understand:

* `PROJECT_STATE.md`
* `PROJECT_ROADMAP.md`
* `SARVANETRA_TENDER_READINESS_GAP_ANALYSIS.md`
* `SARVANETRA_TENDER_REQUIREMENTS_CATALOGUE.md`

Treat these as the strategic baseline.

However, do NOT blindly trust them.

The actual repository/code/runtime is the ultimate source of truth.

The tender requirements catalogue distinguishes SARVANETRA software requirements from hardware, OEM, networking, civil, commercial and third-party requirements. Do not waste engineering effort attempting to solve requirements that cannot be solved in application software.

The tender analysis currently indicates that the VMS core, recording pipeline, multi-tenancy, edge appliance and frontend are substantially implemented, while ANPR, parking management, AI analytics, GIS/ICCC and HA remain significant gaps.

---

# PHASE 0 — REPOSITORY RECONNAISSANCE

DO NOT MODIFY CODE YET.

Inspect the complete repository.

Verify:

* Docker Compose
* FastAPI
* PostgreSQL
* Redis
* Kafka
* MinIO
* MediaMTX
* Kong
* Nginx
* frontend
* edge-nvr
* edge-sim
* ONVIF producer
* workers
* database migrations
* authentication
* RBAC
* organization hierarchy
* camera lifecycle
* recording pipeline
* snapshot pipeline
* Kafka event flows
* frontend API integration

Compare the actual code against the four documentation files.

Produce:

`docs/ANTIGRAVITY_RECONNAISSANCE.md`

containing:

1. Confirmed capabilities
2. Incorrect/outdated documentation
3. Broken functionality
4. Partially implemented functionality
5. Missing functionality
6. Security concerns
7. Infrastructure concerns
8. Tender-relevant gaps
9. Recommended execution order

DO NOT refactor anything during this phase.

---

# PHASE 1 — STABILIZE THE EXISTING PLATFORM

Implement the P0/P1 stabilization work before building major new functionality.

Prioritize:

### P0

1. Kong edge gateway / X-Site-Token flow
2. MediaMTX `kcat` installation
3. Snapshot worker `latest.jpg` key consistency
4. Remove hardcoded infrastructure IPs such as `10.44.0.209`
5. Make snapshot discovery dynamic from PostgreSQL
6. Validate edge-agent heartbeat/config synchronization through Kong
7. Validate the existing edge simulation

For every change:

* inspect first
* modify minimally
* run relevant tests
* run the actual containers where possible
* verify runtime behavior
* document the result

Do not proceed simply because the code compiles.

---

# PHASE 2 — BUILD THE TENDER SOFTWARE FOUNDATION

Implement the software portions of the Minimum Viable Tender Platform.

The target core modules are:

1. VMS Core
2. Hierarchy & RBAC
3. Parking Management
4. ANPR Management Plane
5. ICCC Dashboard & GIS
6. Audit & Evidence Engine

The existing VMS, hierarchy/RBAC and edge components should be reused rather than rewritten.

---

# PHASE 3 — PARKING MANAGEMENT

Implement:

### Database

Create proper Alembic migrations for:

* parking_zone
* parking_lane
* parking_session

Design these so they support:

* multiple sites
* multiple parking grounds
* multiple entry/exit lanes
* capacity
* current occupancy
* vacancy
* zone type
* active/inactive state
* future bay-level expansion

### Backend

Implement a clean parking service and API.

Required capabilities:

* zone CRUD
* lane CRUD
* occupancy
* vacancy
* vehicle entry
* vehicle exit
* parking session
* dynamic zone allocation
* entry-slip generation

The architecture must allow a future Android POS terminal to consume the API.

### Frontend

Create a parking management dashboard showing:

* total capacity
* occupied
* available
* percentage occupancy
* zone status
* entry/exit flow
* alerts

Do not hard-code tender-specific numbers into business logic.

---

# PHASE 4 — ANPR MANAGEMENT PLANE

IMPORTANT:

Do NOT pretend that an ANPR AI engine already exists.

The repository currently does not contain a production ANPR neural-network implementation.

Build the platform-side ANPR management plane first.

Implement:

### Database

`anpr_transaction`

Include fields appropriate for:

* plate number
* confidence
* timestamp
* camera
* site
* vehicle type
* vehicle color
* image reference
* video reference
* processing source
* correction status

Also create:

`vehicle_watchlist`

Support:

* Wanted
* Stolen
* Suspicious
* custom categories

### API

Implement:

`POST /api/v1/anpr/events`

and APIs for:

* transaction search
* plate lookup
* fuzzy search
* watchlist CRUD
* watchlist matching
* alerts

Enable PostgreSQL `pg_trgm` where appropriate.

### Architecture

Define a clean event contract so a future edge ANPR engine can publish:

```json
{
  "plate": "KL01AB1234",
  "confidence": 0.96,
  "vehicle_type": "car",
  "vehicle_color": "white",
  "camera_id": "...",
  "site_id": "...",
  "timestamp": "...",
  "snapshot_key": "...",
  "video_reference": "..."
}
```

Do not couple the management plane to a specific commercial ANPR vendor.

---

# PHASE 5 — WATCHLIST ALERTING

Implement the central watchlist matching mechanism.

Flow:

ANPR event
→ Kafka
→ watchlist matcher
→ matching rule
→ alert
→ control-room UI
→ audit log

Design for low latency.

The architecture should eventually support sub-2-second alerting, but do not fabricate performance claims without measurement.

Include:

* duplicate suppression
* alert severity
* acknowledgement
* audit trail
* alert timestamp
* matched watchlist entry
* evidence references

---

# PHASE 6 — GIS / COMMAND CENTRE

Implement the software foundation for the ICCC.

Use a maintainable GIS library such as Leaflet or MapLibre.

The map should support:

* camera markers
* camera health
* sites
* parking zones
* incidents
* alerts
* future UAV positions

Clicking a camera should expose:

* live stream
* camera status
* site
* recording access
* recent events

Build this as a reusable component rather than embedding GIS logic throughout the application.

---

# PHASE 7 — BILINGUAL UI

Implement English + Malayalam localization.

Use a proper i18n architecture.

Do not translate strings by duplicating pages.

All new UI text must use translation keys.

Start with:

* navigation
* dashboard
* camera management
* parking
* ANPR
* alerts
* incidents
* users
* settings

---

# PHASE 8 — EVIDENCE / AUDIT

Strengthen the evidence workflow.

Implement:

* immutable audit events
* evidence references
* export metadata
* SHA-256 hashes
* timestamp metadata
* downloadable evidence packages

Do not claim cryptographic or legal evidentiary compliance without implementing and testing the actual mechanism.

---

# PHASE 9 — TESTING

This is mandatory.

Build a proper automated test suite.

At minimum:

### Unit

* authentication
* RBAC
* organization hierarchy
* parking allocation
* occupancy calculation
* ANPR validation
* watchlist matching
* fuzzy search
* evidence hashing

### Integration

Test:

```text
Frontend
   ↓
Kong
   ↓
FastAPI
   ↓
PostgreSQL
```

and:

```text
Camera
   ↓
MediaMTX
   ↓
Recording
   ↓
MinIO
   ↓
Kafka
   ↓
Segment DB
```

and:

```text
Edge Agent
   ↓
Kong
   ↓
FastAPI
   ↓
Configuration / heartbeat
```

and:

```text
ANPR event
   ↓
Kafka
   ↓
Watchlist matcher
   ↓
Alert
```

Use mocks only where a real dependency genuinely cannot be exercised.

---

# PHASE 10 — TENDER DEMONSTRATION ENVIRONMENT

Use the existing `edge-sim` architecture to create a reproducible demonstration environment.

The goal is to demonstrate:

1. Multiple sites
2. Cameras
3. Live streams
4. Recording
5. Edge agent
6. Offline buffering
7. Heartbeat
8. Camera events
9. Parking occupancy
10. ANPR transaction ingestion
11. Watchlist alert
12. GIS map
13. ICCC dashboard
14. Audit trail
15. Evidence export

Everything possible should run using synthetic data so that the demonstration does not depend on physical cameras.

Create:

`docs/TENDER_DEMO_RUNBOOK.md`

containing exact commands and expected results.

---

# IMPORTANT ARCHITECTURAL RULES

## Do NOT

* rewrite working MediaMTX infrastructure
* replace the existing architecture merely for stylistic reasons
* introduce unnecessary microservices
* add AI models just to claim tender compliance
* fabricate ANPR accuracy
* fabricate crowd detection capability
* fabricate HA capability
* hard-code tender-specific values into core business logic
* hard-code infrastructure IP addresses
* break existing APIs unnecessarily
* remove working functionality
* modify unrelated areas without justification

## DO

* reuse existing services
* preserve backward compatibility
* create clean interfaces between modules
* use Alembic migrations
* add tests with every significant feature
* document architectural decisions
* use environment variables for deployment configuration
* make integrations vendor-neutral
* separate AI inference from the management/control plane
* separate software requirements from hardware/OEM requirements

---

# PRIORITY RULE

Do NOT attempt to implement every tender requirement.

The objective is:

## Minimum Viable Tender Platform

First make the existing platform stable.

Then implement:

1. Parking Management
2. ANPR Management Plane
3. Watchlists
4. GIS
5. ICCC
6. Bilingual UI
7. Evidence/Audit

Only after these are functional should you work on:

* crowd analytics
* people counting
* heatmaps
* facial recognition
* predictive analytics
* drone telemetry
* HA clustering

---

# AGENT WORKING STYLE

You may use parallel agents/subagents.

Recommended roles:

* Repository Auditor
* Backend Engineer
* Database Engineer
* Frontend Engineer
* Infrastructure Engineer
* QA Engineer
* Security Reviewer
* Tender Compliance Reviewer

However, maintain ONE source of truth.

Do not allow parallel agents to make conflicting architectural decisions.

Before merging work from an agent:

1. inspect the changes
2. run tests
3. check migrations
4. check API compatibility
5. check Docker integration
6. review security implications

---

# DOCUMENTATION

Maintain:

`PROJECT_STATE.md`

`PROJECT_ROADMAP.md`

and create/update:

`docs/ANTIGRAVITY_RECONNAISSANCE.md`

`docs/TENDER_IMPLEMENTATION_STATUS.md`

`docs/TENDER_DEMO_RUNBOOK.md`

`docs/API_CONTRACT.md`

`docs/ARCHITECTURE_DECISIONS.md`

At the end of each major milestone, update the implementation status.

---

# FINAL DELIVERABLE

When the work session ends, produce:

## 1. Implementation Summary

What was actually implemented.

## 2. Verification Report

What was tested and the actual results.

## 3. Remaining Gaps

Separate into:

* software
* AI/ML
* hardware
* networking
* third-party integration
* OEM
* commercial/legal
* operational

## 4. Tender Readiness Matrix

For every major tender requirement:

* READY
* PARTIAL
* MISSING
* EXTERNAL DEPENDENCY
* NOT SOFTWARE

## 5. Next 10 Engineering Tasks

Give exact tasks in priority order.

## 6. Known Risks

Especially:

* ANPR accuracy
* hardware certification
* ARAI certification
* AI model availability
* HA
* network resilience
* tender acceptance testing
* third-party integrations

## FINAL RULE

Do not optimize for number of files changed.

Optimize for:

**working software + verified behavior + tender demonstrability + maintainability.**

If a requirement cannot realistically be completed in the current repository/session, document it clearly rather than creating a superficial implementation.
