# SARVANETRA — MASTER AUTONOMOUS ENGINEERING & TENDER READINESS MISSION

You are the autonomous lead engineering team for the SARVANETRA repository.

Your mission is to take the current repository from its documented "as-built" state through:

**RECONNAISSANCE → STABILIZATION → TESTING → SECURITY → TENDER PLATFORM BUILD → CHAOS TESTING → DEMONSTRATION READINESS**

Do not merely produce plans.

Inspect the repository.

Run commands.

Run containers.

Run tests.

Modify code.

Create migrations.

Build frontend.

Test integrations.

Break the system safely.

Repair it.

Document everything.

Use the available agent capacity aggressively.

Use parallel subagents when useful.

---

# 0. SOURCE OF TRUTH

Before modifying anything, read these documents completely:

```text
PROJECT_STATE.md
PROJECT_ROADMAP.md
TENDER_COMPARISON.md
TENDER_READINESS.md
TENDER_REQUIREMENTS.md
TENDER_ROADMAP.md
```

Treat these documents as the current engineering and tender baseline.

However:

**The actual repository and runtime behavior are the ultimate source of truth.**

Do not blindly trust a statement just because it appears in documentation.

Where documentation and implementation disagree:

1. verify the repository
2. classify the discrepancy
3. fix documentation when appropriate
4. do not invent functionality

The tender documentation explicitly distinguishes software capability from hardware, OEM, networking, civil, commercial and third-party requirements.

Do not attempt to solve non-software requirements with fake application features.

---

# 1. CREATE AN ISOLATED ENGINEERING BRANCH

Before making changes:

1. inspect current Git status
2. inspect current branch
3. record current commit
4. ensure there are no unexpected local changes

Create an isolated engineering branch such as:

```text
agent/sarvanetra-tender-readiness
```

Do not destroy or overwrite existing work.

Create commits after major verified milestones.

Suggested commit boundaries:

```text
01-reconnaissance
02-p0-stabilization
03-testing-foundation
04-edge-vpn
05-parking-anpr
06-iccc-gis
07-evidence-security
08-chaos-validation
09-tender-demo
```

---

# 2. PARALLEL AGENT STRUCTURE

Create specialist agents as appropriate.

Recommended agents:

```text
SARVANETRA LEAD
│
├── Repository Archaeologist
├── Backend Engineer
├── Database Engineer
├── Infrastructure / Docker Engineer
├── Media Pipeline Engineer
├── Kafka Engineer
├── Edge / Headscale Engineer
├── Frontend Engineer
├── Security Red Team
├── QA / Test Engineer
├── Performance Engineer
├── Tender Compliance Analyst
└── Documentation Engineer
```

Agents may work in isolated worktrees when modifying code.

Do not allow parallel agents to make contradictory architectural changes.

The lead agent is responsible for reconciliation and final integration.

---

# 3. PHASE 1 — DEEP REPOSITORY ARCHAEOLOGY

DO NOT MODIFY CODE YET.

Inspect the complete repository.

Inspect:

```text
surv/
edge-nvr/
edge-sim/
docs/
Dockerfiles
docker-compose.yml
docker-compose.prod.yml
.env / .env.example files
Alembic migrations
FastAPI routers
FastAPI models
FastAPI services
workers
Kafka producers
Kafka consumers
MediaMTX config
Kong config
Nginx config
frontend
tests
scripts
CI/CD
```

Map the entire architecture.

Determine:

* actual services
* actual dependencies
* service startup order
* service healthchecks
* exposed ports
* internal ports
* network topology
* database dependencies
* Kafka flows
* object-storage flows
* media flows
* authentication flows
* authorization flows
* edge-to-hub flows
* browser-to-stream flows

Find:

* dead code
* duplicate files
* empty files
* stale configuration
* unused services
* unused dependencies
* hardcoded infrastructure addresses
* hardcoded secrets
* inconsistent environment variables
* broken healthchecks
* missing retries
* race conditions
* weak error handling
* API contract mismatches
* migration problems
* frontend/backend mismatches

Create:

```text
docs/ANTIGRAVITY_RECONNAISSANCE.md
```

Include:

```text
Confirmed
Incorrect
Outdated
Broken
Partially Implemented
Missing
Unknown
Security Risk
Infrastructure Risk
Tender Gap
```

Do not modify application code until this report exists.

Then continue automatically.

---

# 4. PHASE 2 — P0 PLATFORM STABILIZATION

Implement all genuine P0 blockers.

Prioritize:

## P0-1 — Kong Edge Authentication

Fix the Kong configuration so legitimate edge traffic using:

```text
X-Site-Token
```

can reach the corresponding FastAPI endpoints without weakening JWT protection for ordinary user traffic.

Test:

```text
fleet heartbeat
fleet config
fleet backup clip
edge motion ingestion
```

Verify both:

```text
valid X-Site-Token → accepted
invalid X-Site-Token → rejected
ordinary API endpoint without JWT → rejected
valid user JWT → accepted
```

Do not create a broad unrestricted bypass.

Use route-specific authentication behavior.

---

# 5. MEDIA MTX KAFKA HOOK FIX

Inspect:

```text
surv/Dockerfile.mediamtx
surv/scripts/camera_ready.sh
surv/scripts/camera_down.sh
```

Restore the `kcat` dependency or implement a technically superior equivalent.

Verify:

```text
camera connects
camera_ready event
camera disconnects
camera_down event
Kafka receives lifecycle event
```

Check container logs for silent hook failures.

---

# 6. SNAPSHOT FIX

Fix the inconsistency between:

```text
timestamped snapshot objects
```

and:

```text
{cam_id}/latest.jpg
```

Ensure the snapshot worker can maintain both:

```text
historical timestamped snapshots
latest.jpg
```

Test:

```text
camera snapshot
→ MinIO
→ presigned URL
→ browser
→ valid JPEG
```

---

# 7. DYNAMIC SNAPSHOT CAMERA DISCOVERY

Remove dependence on a static:

```text
CAMERA_PATHS
```

configuration for active camera discovery.

The worker must query active cameras from PostgreSQL.

Test with:

```text
0 cameras
1 camera
multiple cameras
camera added after worker starts
camera deactivated
camera reactivated
```

Ensure camera lifecycle changes do not require restarting the worker.

---

# 8. REMOVE HARD-CODED DEVELOPMENT NETWORK CONFIGURATION

Search the entire repository for:

```text
10.44.0.209
```

and similar development-only infrastructure parameters.

Replace infrastructure-specific values with proper environment/configuration variables where appropriate.

Do not blindly replace values inside historical documentation.

Distinguish:

```text
runtime configuration
example configuration
documentation
historical archive
```

---

# 9. PLATFORM CLEANUP

Inspect and safely remove or consolidate:

* empty worker files
* unused Kong declarative configuration
* duplicate seed scripts
* stale development artifacts
* obsolete references to old architectures

Do not delete historical documents unless they are explicitly identified as disposable.

Document removals.

---

# 10. PHASE 3 — AUTOMATED TESTING FOUNDATION

Build a serious automated test suite.

The repository must not remain dependent on manual browser testing.

Create tests for:

## Authentication

* login
* invalid password
* account lock
* JWT expiry
* session creation
* logout
* revocation
* refresh behavior if implemented
* invalid token

## RBAC

* organization access
* subtree access
* direct camera grants
* camera group grants
* customer isolation
* site isolation
* privilege escalation attempts

## Cameras

* create
* update
* soft delete
* reactivation
* validation
* MediaMTX synchronization
* invalid RTSP
* invalid RTSPS
* RTMP publisher configuration

## Recordings

* timeline query
* date ranges
* segment filtering
* presigned URLs
* invalid camera access
* missing segment
* deleted object

## Fleet

* provisioning
* site token
* heartbeat
* config pull
* camera assignment
* backup clip
* unauthorized site

## Motion

* event ingestion
* duplicate event
* stale event closure
* authorization

Create coverage for all high-value business logic.

---

# 11. INTEGRATION TEST ENVIRONMENT

Build reproducible integration tests using Docker/Testcontainers or the existing compose infrastructure.

Exercise:

```text
PostgreSQL
Kafka
MinIO
FastAPI
MediaMTX
Kong
```

The following pipelines must be tested end-to-end.

### Recording

```text
MediaMTX
→ segment
→ hook
→ MinIO
→ Kafka
→ PostgreSQL
```

### Motion

```text
ONVIF/synthetic event
→ Kafka
→ motion consumer
→ PostgreSQL
```

### Edge

```text
Edge Agent
→ Kong
→ FastAPI
→ PostgreSQL
```

### Stream authorization

```text
viewer
→ stream request
→ MediaMTX auth webhook
→ FastAPI
→ authorization decision
```

---

# 12. PHASE 4 — SECURITY RED TEAM

Spawn a dedicated security agent.

Treat SARVANETRA as a government surveillance platform.

Audit:

## Authentication

* credential handling
* password storage
* JWT validation
* token expiration
* session revocation
* device token security

## Authorization

Attempt to identify:

* IDOR
* horizontal privilege escalation
* vertical privilege escalation
* cross-customer access
* cross-site access
* cross-organization camera access
* unauthorized recordings
* unauthorized snapshots
* unauthorized fleet operations

## Edge security

Audit:

* site tokens
* token replay
* token exposure
* endpoint restrictions
* Kong routing
* edge registration

## API security

Check for:

* SQL injection
* command injection
* SSRF
* path traversal
* unsafe uploads
* unsafe URL handling
* mass assignment
* excessive data exposure
* missing rate limits

## Infrastructure

Check:

* exposed database
* exposed MinIO
* exposed Kafka
* exposed Kong Admin
* privileged containers
* root execution
* unnecessary capabilities
* secret leakage
* insecure volume mounts

Create:

```text
docs/SECURITY_RED_TEAM_REPORT.md
```

Fix genuine critical/high issues when safe.

Never downgrade a vulnerability merely to make the report look good.

---

# 13. PHASE 5 — DATABASE AUDIT & SCALE TEST

Inspect the complete schema.

Review:

* foreign keys
* indexes
* uniqueness
* nullable fields
* cascading behavior
* transaction boundaries
* query efficiency
* N+1 patterns
* locking
* pagination

Pay particular attention to high-volume entities:

```text
camera
video_segment
motion_event
audit_log
user_session
anpr_transaction
parking_session
```

Simulate datasets representing:

```text
100 cameras
500 cameras
1,000 cameras
5,000 cameras
```

Do not fabricate benchmarks.

Actually measure where practical.

Create:

```text
docs/DATABASE_SCALE_AUDIT.md
```

Implement safe high-value indexing improvements.

---

# 14. PHASE 6 — KAFKA RELIABILITY LAB

Audit all Kafka topics.

Current and planned events include:

```text
camera.motion
camera.status
recording.segments
vehicle.anpr.detected
crowd.density.alert
```

Test:

* broker unavailable
* consumer restart
* producer restart
* duplicate events
* malformed messages
* delayed messages
* consumer lag
* retry behavior
* offset behavior
* replay behavior

Ensure consumers are idempotent where required.

Create:

```text
docs/KAFKA_RELIABILITY_REPORT.md
```

Fix genuine reliability issues.

---

# 15. PHASE 7 — MEDIA PIPELINE CHAOS TESTING

Exercise:

```text
camera
→ MediaMTX
→ recording
→ upload
→ MinIO
→ Kafka
→ PostgreSQL
```

Introduce failures:

1. camera disconnect
2. camera reconnect
3. bad credentials
4. stream interruption
5. MediaMTX restart
6. MinIO outage
7. Kafka outage
8. local disk pressure
9. duplicate segment
10. worker restart

Determine actual behavior.

Fix recoverable problems.

Create:

```text
docs/MEDIA_PIPELINE_CHAOS_REPORT.md
```

---

# 16. PHASE 8 — HEADSCALE / WIREGUARD / EDGE

Now implement the distributed edge foundation.

Address:

* Hub Tailscale peer/container
* Headscale operationalization
* edge-to-hub connectivity
* edge stream routing
* automated ACL synchronization
* edge MediaMTX authentication

Implement organization-aware network policy.

The objective is:

```text
BSNL organization/site
        ↓
Headscale policy
        ↓
specific edge/user access
        ↓
specific camera resources
```

Test:

```text
authorized edge → Hub
unauthorized edge → denied
authorized viewer → edge camera
unauthorized viewer → denied
```

Do not use a network-wide "everyone can access everything" policy merely to make connectivity work.

Create:

```text
docs/HEADSCALE_EDGE_SECURITY.md
```

---

# 17. PHASE 9 — TENDER SOFTWARE FOUNDATION

Now use:

```text
TENDER_COMPARISON.md
TENDER_READINESS.md
TENDER_REQUIREMENTS.md
TENDER_ROADMAP.md
```

to build the Minimum Viable Tender Platform.

The target reusable core is:

```text
1. VMS Core
2. Hierarchy & RBAC
3. Parking Management
4. ANPR Management Plane
5. ICCC/GIS
6. Audit & Evidence
```

Do not create separate codebases for Tender A and Tender B.

Use reusable modules/plugins.

---

# 18. PHASE 10 — PARKING MANAGEMENT

Create a proper domain model.

At minimum:

```text
parking_zone
parking_lane
parking_session
```

Support:

* site
* zone
* capacity
* occupancy
* vacancy
* entry lanes
* exit lanes
* active/inactive
* allocation policy

Do not hard-code Nilakkal logic into generic platform services.

Support site-specific configuration.

---

# 19. PARKING ALLOCATION ENGINE

Implement:

```text
ParkingAllocationService
```

The service should support:

```text
vehicle enters
→ obtain available zones
→ select eligible zone
→ create parking session
→ increment occupancy
→ return allocation
```

Handle:

* zone full
* all zones full
* duplicate vehicle
* vehicle exit
* stale sessions
* invalid session
* concurrent entry requests

Do not allow capacity to be exceeded under concurrent transactions.

Use proper database transaction/locking strategy.

---

# 20. PARKING API

Create appropriate APIs such as:

```text
GET /api/v1/parking/zones
POST /api/v1/parking/zones

GET /api/v1/parking/occupancy

POST /api/v1/parking/entry
POST /api/v1/parking/exit

POST /api/v1/parking/entry-slip
```

Do not invent endpoints unnecessarily if an existing convention provides a better design.

Keep the API documented and tested.

---

# 21. ANPR MANAGEMENT PLANE

IMPORTANT:

The existing repository does NOT contain a production ANPR neural network engine.

Do not pretend it does.

Build the platform-side management plane so that a future commercial/edge AI engine can plug into it cleanly.

Create a proper:

```text
anpr_transaction
vehicle_watchlist
```

model.

Store appropriate fields such as:

```text
plate
confidence
timestamp
camera
site
vehicle_type
vehicle_color
snapshot reference
video reference
processing source
correction information
```

---

# 22. ANPR EVENT API

Implement the central ingest contract.

Example conceptual payload:

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

Support:

* validation
* duplicate handling
* persistence
* Kafka publication
* search
* filtering
* pagination

Keep inference engine and management plane decoupled.

---

# 23. FUZZY PLATE SEARCH

Implement PostgreSQL `pg_trgm` support where appropriate.

Support approximate searches for likely OCR errors.

Test:

```text
exact match
1-character variation
2-character variation
case normalization
spacing normalization
invalid plate
large result set
```

Measure query performance.

---

# 24. WATCHLIST MATCHING

Implement:

```text
ANPR event
→ Kafka
→ watchlist matcher
→ matching watchlist
→ alert
→ UI
→ audit
```

Support categories such as:

```text
Wanted
Stolen
Suspicious
Custom
```

Implement:

* duplicate suppression
* alert severity
* acknowledgement
* evidence reference
* audit entry

Do not claim sub-2-second performance without measuring it.

---

# 25. SYNTHETIC ANPR ENGINE

Because there is no production ANPR inference engine yet, create a realistic simulation producer.

Generate:

* valid plates
* OCR errors
* low-confidence reads
* duplicate events
* watchlist matches
* non-matches
* vehicle types
* colors

Use this simulator for:

```text
development
integration tests
demo
load tests
```

Make the interface identical to what a future edge AI engine should publish.

---

# 26. PHASE 11 — GIS / ICCC COMMON OPERATING PICTURE

Integrate a maintainable GIS library such as:

```text
Leaflet
or
MapLibre
```

Build a reusable map component.

Display:

* cameras
* sites
* parking zones
* alerts
* incidents
* future UAV locations

Camera marker status should reflect:

```text
online
offline
warning
motion
```

Clicking a camera should expose appropriate:

* live feed
* status
* site
* recording
* recent events

---

# 27. ICCC DASHBOARD

Create a composite command interface containing:

```text
GIS Map
+
Camera/video wall
+
Parking occupancy
+
ANPR alerts
+
Incident feed
+
System health
```

Make it useful as a control-room "single pane of glass".

Do not build a static mockup.

Every displayed metric should originate from the actual backend or clearly labelled simulation.

---

# 28. BILINGUAL UI

Implement:

```text
English
Malayalam
```

using proper localization architecture.

Use translation keys.

Do not duplicate entire pages.

Apply localization to:

* navigation
* dashboards
* cameras
* parking
* ANPR
* alerts
* incidents
* users
* settings
* reports

Test switching languages without page breakage.

---

# 29. PHASE 12 — INCIDENT MANAGEMENT

Implement the software foundation for:

```text
New
Assigned
Escalated
Resolved
Closed
```

Create appropriate:

```text
incident
incident_timeline
```

models.

Connect:

```text
ANPR alert
camera alert
motion alert
manual incident
```

to the incident workflow.

Implement auditability of state transitions.

---

# 30. PHASE 13 — EVIDENCE PACKAGE

Strengthen evidence handling.

Implement an evidence packaging service.

Package should support:

```text
video
metadata
timestamp
camera
incident
SHA-256 manifest
```

Where cryptographic signatures are implemented, make that explicit.

Do not claim "tamper-proof" merely because a hash exists.

Test:

```text
generate package
→ calculate hash
→ alter file
→ verify mismatch
```

---

# 31. PHASE 14 — FRONTEND AUDIT

Inspect every frontend API call.

Compare the actual frontend implementation with the actual FastAPI API.

Find:

* stale endpoints
* nonexistent endpoints
* wrong methods
* wrong payloads
* incorrect response assumptions
* broken permission checks
* loading bugs
* error handling bugs
* stale pages
* broken navigation

Run the real application in the browser.

Navigate through:

```text
Login
Dashboard
Live View
Cameras
Playback
Motion
Health
Fleet
Organizations
Customers
Users
Roles
Audit
Camera Groups
Parking
ANPR
ICCC
Incidents
Evidence
```

Fix genuine issues.

---

# 32. PHASE 15 — EDGE SIMULATION

Upgrade `edge-sim` into a realistic tender demonstration/load environment.

Support configurable:

```text
site count
camera count
event rate
failure rate
network latency
```

Simulate:

* camera registration
* edge heartbeat
* configuration sync
* motion
* camera status
* backup clip
* network outage
* network recovery
* queued events
* synchronization after reconnection

The environment must be reproducible.

Aim for a single command to start the simulation.

---

# 33. PHASE 16 — PARKING SIMULATION

Build a synthetic traffic generator.

Simulate:

```text
vehicle arrives
→ ANPR event
→ parking allocation
→ entry slip
→ occupancy increase
→ parking session
→ vehicle exit
→ occupancy decrease
```

Test concurrency.

Verify the invariant:

```text
0 <= occupancy <= capacity
```

at all times.

---

# 34. PHASE 17 — PERFORMANCE / LOAD TESTING

Create practical load tests for:

```text
authentication
camera listing
camera status
recording search
timeline
ANPR search
parking occupancy
dashboard
fleet heartbeat
```

Generate realistic synthetic data.

Identify:

* slow SQL
* N+1 calls
* excessive frontend polling
* Kafka pressure
* memory growth
* CPU hotspots
* serialization overhead

Fix obvious high-value bottlenecks.

Do not claim "production scale" based on theoretical calculations.

Record actual measurements.

---

# 35. PHASE 18 — CHAOS ENGINEERING

Create a controlled failure matrix.

Test:

```text
PostgreSQL down
Redis down
Kafka down
MinIO down
MediaMTX down
Kong down
FastAPI down
worker down
edge agent down
network disconnected
disk nearly full
invalid credentials
expired tokens
```

For each:

1. observe
2. record
3. identify expected behavior
4. identify actual behavior
5. fix where appropriate
6. retest recovery

Create:

```text
docs/CHAOS_TEST_REPORT.md
```

---

# 36. PHASE 19 — OBSERVABILITY

Audit whether operators can understand failures.

Improve where necessary:

* structured logs
* correlation IDs
* health endpoints
* readiness endpoints
* worker health
* Kafka consumer health
* MediaMTX status
* storage health
* edge heartbeat status
* error messages

An operator should be able to answer:

```text
Why is this camera offline?
Why did recording stop?
Why is this edge NVR disconnected?
Why did this ANPR event fail?
Why is this video unavailable?
```

without opening source code.

---

# 37. PHASE 20 — PRODUCTION SECURITY / HARDENING

Audit and improve:

```text
secret management
CORS
TLS
container users
container permissions
exposed ports
Kong admin access
MinIO credentials
database credentials
Kafka credentials
camera credential handling
```

Pay particular attention to camera credentials at rest.

Do not expose secrets in documentation or logs.

---

# 38. PHASE 21 — TENDER READINESS MATRIX

Now compare the implementation against:

```text
TENDER_COMPARISON.md
TENDER_READINESS.md
TENDER_REQUIREMENTS.md
TENDER_ROADMAP.md
```

Produce:

```text
docs/TENDER_IMPLEMENTATION_STATUS.md
```

For every significant requirement classify:

```text
READY
PARTIAL
MISSING
EXTERNAL DEPENDENCY
HARDWARE
OEM
CIVIL
NETWORK
COMMERCIAL
UNKNOWN
```

Do not claim software satisfies hardware/OEM/certification requirements.

Explicitly separate:

```text
What SARVANETRA can implement
What requires partner/OEM
What requires hardware
What requires certification
What requires physical deployment
What requires bidder eligibility
```

---

# 39. PHASE 22 — TENDER DEMONSTRATION ENVIRONMENT

Build a complete synthetic demonstration.

The demonstration should show:

```text
LOGIN
↓
MULTI-SITE DASHBOARD
↓
CAMERA STATUS
↓
LIVE STREAM
↓
RECORDING
↓
SNAPSHOT
↓
MOTION EVENT
↓
ANPR EVENT
↓
WATCHLIST ALERT
↓
PARKING ALLOCATION
↓
OCCUPANCY
↓
GIS MAP
↓
INCIDENT
↓
EVIDENCE EXPORT
↓
AUDIT LOG
```

Use real application flows.

Synthetic data is acceptable.

Fake UI state is not.

Create:

```text
docs/TENDER_DEMO_RUNBOOK.md
```

Include exact commands.

A fresh developer should be able to execute the demo without asking what to do next.

---

# 40. PHASE 23 — API CONTRACT

Generate/update:

```text
docs/API_CONTRACT.md
```

Include actual implemented:

* endpoint
* method
* authentication
* permissions
* request
* response
* error cases
* example

Do not invent APIs.

The documentation must be generated from the implementation where possible.

---

# 41. PHASE 24 — PRINCIPAL ARCHITECT FINAL REVIEW

Spawn a fresh Principal Architect agent.

Give it:

* repository
* code changes
* test results
* tender matrix
* security report
* chaos report
* database report
* Kafka report

Ask:

> Would this architecture be technically credible for a serious multi-site government surveillance deployment?

Have it challenge:

* architecture
* security
* scalability
* tenancy
* reliability
* failure handling
* edge synchronization
* media pipeline
* database design
* observability
* tender gaps

Do not ask it to provide marketing language.

Create:

```text
docs/PRINCIPAL_ARCHITECT_REVIEW.md
```

---

# 42. IMPORTANT AI / ANPR RULE

There is currently no verified production neural-network ANPR implementation in the repository.

Do NOT install arbitrary AI libraries or claim that a model satisfies tender accuracy requirements merely because it produces detections.

The architecture should instead provide:

```text
AI inference adapter
→ standardized event contract
→ Kafka
→ ANPR management plane
```

This allows later integration with:

* commercial ANPR engines
* TensorRT
* ONNX Runtime
* DeepStream
* edge LPU products
* OEM-certified engines

without redesigning SARVANETRA.

---

# 43. IMPORTANT HA RULE

Do not claim HA merely because containers can be scaled.

Where the tender requires active-active or zero-single-point-of-failure architecture, distinguish:

```text
current single-node development architecture
```

from:

```text
future production HA architecture
```

A proper HA implementation requires actual failover testing.

Only mark HA capabilities as implemented after real verification.

---

# 44. IMPORTANT CERTIFICATION RULE

Do not claim that running security scanners means:

```text
CERT-In certified
```

Automated scanners are preparation.

Formal certification requires an appropriate external audit process.

Record this distinction in the tender readiness matrix.

---

# 45. FINAL VALIDATION

At the end of the entire mission, run as much as possible:

```text
unit tests
integration tests
frontend tests
lint
type checking
Alembic migration
Docker builds
Docker Compose startup
health checks
security scans
load tests
chaos tests
browser walkthrough
edge simulation
ANPR simulation
parking simulation
```

Perform at least one full end-to-end path:

```text
USER LOGIN
→ CAMERA
→ STREAM
→ RECORDING
→ MINIO
→ KAFKA
→ DATABASE
→ DASHBOARD
```

Then:

```text
ANPR
→ WATCHLIST
→ ALERT
→ INCIDENT
→ EVIDENCE
→ AUDIT
```

Then:

```text
VEHICLE ENTRY
→ ALLOCATION
→ OCCUPANCY
→ ENTRY SLIP
→ EXIT
```

Then:

```text
EDGE
→ VPN
→ KONG
→ HUB
→ HEARTBEAT
→ CONFIG
```

---

# 46. DOCUMENTATION

Create/update:

```text
docs/ANTIGRAVITY_RECONNAISSANCE.md
docs/API_CONTRACT.md
docs/TENDER_IMPLEMENTATION_STATUS.md
docs/TENDER_DEMO_RUNBOOK.md
docs/SECURITY_RED_TEAM_REPORT.md
docs/DATABASE_SCALE_AUDIT.md
docs/KAFKA_RELIABILITY_REPORT.md
docs/MEDIA_PIPELINE_CHAOS_REPORT.md
docs/HEADSCALE_EDGE_SECURITY.md
docs/CHAOS_TEST_REPORT.md
docs/PRINCIPAL_ARCHITECT_REVIEW.md
docs/ARCHITECTURE_DECISIONS.md
```

Also update:

```text
PROJECT_STATE.md
PROJECT_ROADMAP.md
```

only where the verified implementation state has genuinely changed.

---

# 47. FINAL REPORT

Create:

```text
docs/ANTIGRAVITY_MASTER_MISSION_REPORT.md
```

Structure:

# Executive Summary

# Repository Baseline

# Architecture Confirmed

# Architecture Corrections

# Bugs Found

# Bugs Fixed

# Features Implemented

# Tests Added

# Tests Run

# Tests Passing

# Tests Failing

# Security Findings

# Database Findings

# Kafka Findings

# Media Pipeline Findings

# Edge/VPN Findings

# Frontend Findings

# Performance Findings

# Tender Readiness

# Remaining Software Gaps

# External Dependencies

# Hardware / OEM Requirements

# Certification Requirements

# Known Risks

# Recommended Next 20 Tasks

For each remaining task include:

```text
Task
Priority
Affected Components
Dependency
Complexity
Reason
```

---

# 48. EXECUTION BEHAVIOR

This is an autonomous engineering mission.

Do not stop after producing a plan.

Do not spend the entire session explaining what should be done.

Actually do the work.

Use tools.

Use agents.

Inspect code.

Run commands.

Build.

Test.

Break.

Repair.

Verify.

Document.

Continue.

If one approach fails, investigate the failure and try a technically sound alternative.

Do not ask me for confirmation for normal engineering decisions.

Only stop and ask for human input when an action is:

* irreversible destructive data operation
* dependent on credentials unavailable to you
* dependent on physical hardware you cannot access
* dependent on a genuinely ambiguous business requirement that cannot safely be inferred

Otherwise make a reasonable engineering decision and document it.

---

# 49. TIME / TOKEN UTILIZATION

Use available agent capacity aggressively.

Prioritize:

```text
1. repository understanding
2. runtime stabilization
3. tests
4. real implementation
5. security
6. failure testing
7. tender functionality
8. demonstration
9. documentation
```

Do not waste the available budget generating superficial documentation before implementation.

Do not optimize for the number of files changed.

Optimize for:

**verified working software.**

---

# 50. SUCCESS CONDITION

The mission is successful only when SARVANETRA has demonstrably moved toward this state:

```text
          SARVANETRA
               │
      ┌────────┴─────────┐
      │                  │
   CENTRAL HUB         EDGE NVR
      │                  │
      ├── VMS            ├── Local MediaMTX
      ├── RBAC           ├── Local Recording
      ├── Parking        ├── SQLite Buffer
      ├── ANPR           ├── Heartbeat
      ├── Watchlist      ├── Config Sync
      ├── ICCC/GIS       └── Event Sync
      ├── Evidence
      └── Audit
               │
            Kafka
               │
       Async Event Workers
               │
       MinIO + PostgreSQL
```

with:

```text
automated testing
security validation
failure recovery
synthetic multi-site simulation
tender demonstration capability
clear separation of software vs external requirements
```

Do not declare the platform tender compliant merely because a feature exists.

Only report what has actually been implemented and verified.

BEGIN NOW.
