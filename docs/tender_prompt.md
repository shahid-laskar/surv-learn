You are a Senior Solution Architect, Surveillance Systems Architect,
AI Video Analytics Architect, System Integrator, and Government Tender
Compliance Analyst.

PROJECT:
SARVANETRA

OBJECTIVE:
Determine how ready the existing SARVANETRA codebase and architecture are
to satisfy the requirements described in the TWO ATTACHED TENDER DOCUMENTS.

The two tender documents are the primary external requirements source.

Do NOT assume that SARVANETRA already satisfies a requirement simply because
a similar concept exists in the code.

Your job is to perform a rigorous:

CODEBASE -> TENDER REQUIREMENT -> CAPABILITY -> GAP -> IMPLEMENTATION PLAN

analysis.

============================================================
TENDER DOCUMENTS
============================================================

Tender A:
Pathanamthitta District Police / Home Department, Government of Kerala

Subject includes:
- Integrated ANPR
- AI-based Parking Management System
- CCTV Surveillance
- Redundant Network
- Pampa/Sannidhanam UPS and power backup
- CCTV relocation
- Control-room modernization
- Public Address
- 36-month warranty/support

Tender B:
KELTRON EOI

Subject:
Selection of an End-to-End Custom Development, Implementation,
and Financing Partner for AI-Based Surveillance Projects.

Tender B covers a much broader platform including:
- AI video analytics
- people counting and flow analytics
- crowd density monitoring
- predictive crowd intelligence
- journey intelligence
- ANPR
- smart parking
- missing person identification
- drone surveillance
- operational response
- Video Management System
- Integrated Command and Control Centre
- GIS
- IoT
- public address
- digital signage
- emergency systems
- open APIs
- interoperability
- cloud/on-prem/hybrid deployment
- high availability
- database clustering
- cybersecurity
- privacy
- audit
- source-code/IP handover
- SLA/support

============================================================
MOST IMPORTANT RULE
============================================================

The actual SARVANETRA CODEBASE is the source of truth for current
implementation.

The tender documents are the source of truth for requirements.

Existing SARVANETRA documentation is secondary.

Do not trust:
- old docs
- README claims
- TODO lists
- architecture diagrams
- previous plans
- comments

unless verified against code/configuration/tests.

Do not modify application source code.

This task is analysis and planning only.

============================================================
PHASE 1 — UNDERSTAND THE TENDERS
============================================================

Read both tender documents completely.

Do not only summarize them.

Extract every significant requirement.

Create a normalized requirement catalogue.

Give every requirement a unique ID.

Use IDs such as:

T1-ANPR-001
T1-PMS-001
T1-CCTV-001
T1-NET-001
T1-STORAGE-001
T1-SEC-001

T2-AI-001
T2-CROWD-001
T2-ANPR-001
T2-ICC-001
T2-SEC-001
T2-HA-001
etc.

For each requirement record:

Requirement ID
Tender
Section
Requirement
Type
Mandatory / Scored / Optional / Future
Evidence/Page
Software / Hardware / Network / Integration / Operational /
Eligibility / Documentation / Support

============================================================
PHASE 2 — CLASSIFY THE REQUIREMENTS
============================================================

Classify every requirement into one of these categories:

A. SARVANETRA SOFTWARE PLATFORM
B. AI/ML CAPABILITY
C. CAMERA / EDGE DEVICE
D. SERVER / STORAGE
E. NETWORKING
F. POWER / UPS / ELECTRICAL
G. FIELD INSTALLATION / CIVIL WORK
H. THIRD-PARTY INTEGRATION
I. OEM REQUIREMENT
J. BIDDER ELIGIBILITY / COMMERCIAL
K. SUPPORT / SLA / O&M
L. DOCUMENTATION / COMPLIANCE
M. FUTURE / SCALABILITY

This is important.

Do NOT pretend that software can solve:
- OEM certifications
- bidder turnover
- government work references
- physical OFC installation
- UPS installation
- civil works
- camera certification
- manpower qualification

Instead explicitly mark such requirements as:

NOT A SOFTWARE PLATFORM REQUIREMENT

and explain what external capability/partner is needed.

============================================================
PHASE 3 — DEEPLY ANALYZE SARVANETRA
============================================================

Inspect the entire repository.

Identify the actual implementation of:

Backend
Frontend
Database
Authentication
Authorization
Camera management
ONVIF
RTSP
MediaMTX
HLS
Recording
MinIO
Kafka
Redis
Kong
Nginx
Docker
Monitoring
Alerts
Events
AI/video analytics
Search
Reporting
Users/roles
Audit
Notifications
Storage
APIs
Background workers

Pay particular attention to what is ACTUALLY WORKING versus what is
just scaffolded.

============================================================
PHASE 4 — BUILD A SARVANETRA CAPABILITY MAP
============================================================

Create a capability map.

Example:

SARVANETRA
|
+-- Camera Management
|   +-- camera registration
|   +-- RTSP
|   +-- ONVIF
|   +-- health monitoring
|
+-- Video
|   +-- MediaMTX
|   +-- live streaming
|   +-- HLS
|   +-- recording
|   +-- MinIO
|
+-- Events
|   +-- Kafka
|   +-- alerts
|
+-- Analytics
|   +-- motion
|   +-- intrusion
|   +-- people counting
|   +-- etc.
|
+-- Command Centre
|   +-- dashboard
|   +-- maps
|   +-- cameras
|   +-- alerts
|
etc.

For every capability give actual source-file evidence.

============================================================
PHASE 5 — TENDER-TO-CODE MAPPING
============================================================

This is the MOST IMPORTANT deliverable.

For EVERY significant tender requirement create a mapping:

Requirement ID
Tender
Requirement
SARVANETRA Capability
Evidence in Code
Current Status
Gap
Required Work
External Dependency

Use these statuses:

GREEN  = CURRENTLY SATISFIED
YELLOW = PARTIALLY SATISFIED
ORANGE = IMPLEMENTABLE BUT NOT YET BUILT
BLUE   = REQUIRES THIRD-PARTY INTEGRATION
RED    = NOT CURRENTLY SUPPORTED
GRAY   = NOT A SOFTWARE REQUIREMENT
BLACK  = UNKNOWN / REQUIRES VERIFICATION

Do not use subjective "good/bad" judgments.

============================================================
PHASE 6 — VERY IMPORTANT: DISTINGUISH PLATFORM FROM PRODUCT
============================================================

For each requirement answer:

Can SARVANETRA itself provide this?

OR

Does SARVANETRA need:

- camera OEM
- ANPR engine
- AI inference engine
- VMS
- NVR
- GPU
- edge computer
- GIS provider
- drone platform
- public address platform
- parking hardware
- network infrastructure
- UPS
- external mobile application
- government API
- third-party integration

For example:

Requirement:
ANPR recognition

Possible result:

SARVANETRA CORE:
Provides event ingestion, storage, APIs, dashboard, search, alerts.

ANPR ENGINE:
Third-party or dedicated AI module required.

EDGE:
LPU/GPU may be required.

CAMERA:
Certified ANPR camera required.

This distinction must appear throughout the analysis.

============================================================
PHASE 7 — FIRST TENDER SPECIFIC ANALYSIS
============================================================

Analyze Tender A in detail.

Explicitly evaluate SARVANETRA against:

1. 12 parking zones
2. automated parking allocation
3. parking occupancy
4. dynamic vacancy
5. parking dashboards
6. POS-generated parking slips
7. ANPR entry/exit tracking
8. vehicle classification
9. vehicle make
10. vehicle color
11. hotlist/watchlist
12. event alerts
13. 90-day CCTV retention
14. 7-day local ANPR storage
15. 90-day central ANPR storage
16. historical analytics
17. vehicle volume analytics
18. traffic trends
19. pilgrim estimation
20. IP public address
21. live monitoring
22. PTZ
23. centralized CCTV
24. video export
25. redundant network
26. control room
27. seasonal camera-view relocation
28. UPS integration
29. health monitoring
30. audit logs
31. role-based access
32. reporting
33. API/integration
34. warranty/O&M support requirements

Also compare against the detailed technical requirements for:
- cameras
- ANPR
- LPU
- NVR
- servers
- network switches
- storage
- cybersecurity
- ONVIF
- HLS/video
- recording
- analytics

Do not merely state "compatible".

Explain exactly HOW SARVANETRA would satisfy the requirement.

============================================================
PHASE 8 — SECOND TENDER SPECIFIC ANALYSIS
============================================================

Analyze Tender B separately.

Evaluate SARVANETRA against:

AI VIDEO ANALYTICS
- perimeter intrusion
- unauthorized access
- loitering
- abandoned objects
- unattended objects
- fall detection
- suspicious behaviour
- abnormal behaviour
- object classification
- vehicle tracking
- pedestrian tracking
- rule-based event detection
- real-time alerts

PEOPLE / FLOW ANALYTICS
- entry/exit counting
- occupancy
- queue estimation
- queue progression
- movement direction
- dwell time
- pedestrian analytics
- flow visualization
- heat maps
- historical analytics

CROWD INTELLIGENCE
- density estimation
- congestion identification
- zone monitoring
- heat-map visualization
- density threshold alerts
- risk indicators
- historical trends
- predictive crowd build-up
- congestion prediction
- queue formation forecasting
- demand forecasting
- capacity utilization
- operational risk

JOURNEY INTELLIGENCE
- transport integration
- parking integration
- access control
- entry/exit
- queue management
- CCTV analytics
- pedestrian analytics
- journey insights

MOBILITY
- ANPR
- vehicle tracking
- entry/exit
- traffic analytics
- vehicle search
- whitelist/blacklist
- incident investigation
- parking occupancy
- parking availability
- overstay detection
- parking optimization

MISSING PERSONS
- face-based search
- video analytics
- camera correlation
- last-seen location
- alert generation
- investigation workflow

DRONE
- live video
- situational awareness
- incident assessment
- emergency response
- GIS integration
- recording
- mission management

OPERATIONAL RESPONSE
- access regulation
- pedestrian routing
- queue management
- public announcement
- variable message signs
- digital signage
- field notifications
- automated alert generation
- SOP workflows

VIDEO MANAGEMENT
- live monitoring
- intelligent recording
- search
- storage management
- playback
- event-based recording
- investigation
- evidence export

ICCC
- CCTV
- AI analytics
- crowd analytics
- ANPR
- parking
- drone
- GIS
- IoT
- PA
- digital signage
- emergency systems
- incident management
- dashboards
- COP
- real-time alerts
- GIS visualization
- event correlation
- incident lifecycle
- workflow automation
- reporting
- audit
- mobile access

TECHNICAL EXPECTATIONS
- modular
- scalable
- open standards
- APIs
- third-party interoperability
- cloud
- on-prem
- hybrid
- high availability
- disaster recovery
- role-based access
- audit logging
- privacy
- information security
- active-active / active-passive
- load balancing
- database clustering
- replication
- DPDP Act
- ISO 27001
- CERT-In audit

DELIVERABLES
- source code
- documentation
- IP handover
- SLA
- annual support
- commissioning
- training

============================================================
PHASE 9 — AI CAPABILITY GAP ANALYSIS
============================================================

Do not assume that having an AI-capable camera means SARVANETRA supports
the corresponding analytics.

For each AI use case determine whether it is:

1. detected directly by camera
2. detected by edge AI
3. detected by centralized AI
4. detected by third-party AI
5. not implemented

Create an AI capability matrix:

Use Case
Camera Edge
SARVANETRA
Central AI
Third Party
Current Status
Effort
Tender Compatibility

============================================================
PHASE 10 — ARCHITECTURE GAP ANALYSIS
============================================================

Determine whether current SARVANETRA architecture can scale from its
existing surveillance implementation to the broader tender architecture.

Analyze:

- multi-site architecture
- multi-tenancy
- hierarchy
- state/district/zone/site/camera
- central command centre
- edge processing
- centralized processing
- message bus
- event correlation
- storage architecture
- object storage
- database scaling
- HA
- failover
- load balancing
- disaster recovery
- GPU workloads
- AI inference architecture
- API gateway
- authentication
- authorization
- audit
- observability

============================================================
PHASE 11 — DATA MODEL GAP
============================================================

Compare the current database model with what the tenders require.

Identify missing entities such as:

- parking zones
- parking slots
- parking transactions
- vehicle events
- ANPR observations
- watchlists
- alerts
- incidents
- people
- journeys
- crowd measurements
- analytics events
- sites
- districts
- locations
- evidence
- investigations
- workflows
- SOPs
- audit events
- devices
- integrations

Do not assume all entities are required for immediate implementation.

Separate:
CURRENT
REQUIRED
FUTURE

============================================================
PHASE 12 — API GAP ANALYSIS
============================================================

Compare current SARVANETRA APIs with the requirements.

Identify APIs needed for:

- camera management
- streams
- recordings
- search
- ANPR
- vehicle events
- watchlists
- alerts
- incidents
- analytics
- parking
- crowd
- GIS
- evidence
- reports
- users
- roles
- audit
- integrations

For each missing API include:

Endpoint concept
Purpose
Data model dependency
Authentication
Implementation complexity

============================================================
PHASE 13 — SECURITY / COMPLIANCE GAP
============================================================

Evaluate:

- authentication
- authorization
- RBAC
- location-based access
- audit logs
- tamper resistance
- encryption in transit
- encryption at rest
- secrets management
- key management
- secure boot assumptions
- API security
- vulnerability management
- logging
- monitoring
- incident response
- privacy
- data retention
- evidence integrity

Do NOT claim legal certification.

Instead distinguish:

TECHNICAL CAPABILITY
from
FORMAL CERTIFICATION / AUDIT REQUIREMENT

============================================================
PHASE 14 — PRODUCTION READINESS
============================================================

Evaluate SARVANETRA for a government production deployment.

Analyze:

- HA
- backup
- disaster recovery
- monitoring
- alerting
- logging
- upgrade strategy
- rollback
- configuration management
- health checks
- capacity planning
- storage growth
- video retention
- network failure
- camera failure
- database failure
- Kafka failure
- Redis failure
- MinIO failure
- MediaMTX failure
- gateway failure

============================================================
PHASE 15 — BIDDER/OEM READINESS
============================================================

Create a separate section:

"NOT SOLVABLE BY CODE"

Extract requirements such as:

- bidder turnover
- previous government projects
- Kerala office
- OEM presence
- OEM certifications
- ISO
- CMMI
- STQC/BIS
- CERT-In assessment
- OEM authorization
- project references
- qualified manpower
- support personnel
- financial/security requirements

Explain exactly what organizational/commercial actions would be required.

============================================================
PHASE 16 — REQUIREMENT PRIORITIZATION
============================================================

Classify each gap as:

P0 - required to respond / qualify
P1 - required for minimum functional compliance
P2 - important for successful deployment
P3 - enhancement / future capability

Also classify implementation effort:

LOW
MEDIUM
HIGH
VERY HIGH

============================================================
PHASE 17 — MINIMUM VIABLE TENDER PLATFORM
============================================================

Define the smallest SARVANETRA platform that could credibly form the
software core of these tender solutions.

Do NOT attempt to build everything from Tender B immediately.

Create:

SARVANETRA CORE
+
AI ANALYTICS LAYER
+
ANPR MODULE
+
PARKING MODULE
+
ICCC MODULE
+
INTEGRATION LAYER
+
EVIDENCE / INVESTIGATION
+
SECURITY / AUDIT
+
OBSERVABILITY

Explain which modules are:

CORE
OPTIONAL
THIRD-PARTY
PROJECT-SPECIFIC

============================================================
PHASE 18 — RECOMMENDED TARGET ARCHITECTURE
============================================================

Design the target architecture required to make SARVANETRA tender-ready.

Include:

- edge layer
- camera layer
- AI inference layer
- streaming layer
- event layer
- API layer
- database
- object storage
- search
- analytics
- GIS
- ICCC
- notification
- authentication
- audit
- observability
- high availability

Show logical data flows.

============================================================
PHASE 19 — IMPLEMENTATION ROADMAP
============================================================

Create a practical sequence.

Do NOT create a giant list of disconnected tasks.

Group the roadmap into:

PHASE A — Stabilize Existing SARVANETRA

PHASE B — Tender Compliance Foundation

PHASE C — AI Analytics Platform

PHASE D — ANPR

PHASE E — Parking

PHASE F — ICCC / Command Centre

PHASE G — Integrations

PHASE H — Security / Compliance

PHASE I — HA / Production

PHASE J — Deployment / O&M

For every phase identify:

Goal
Features
Dependencies
Repositories/files affected
Expected output
Verification criteria

============================================================
PHASE 20 — WHAT SHOULD I BUILD FIRST?
============================================================

This is critical.

Answer this question:

"If I have my current SARVANETRA project today, what should I build
next so that the project becomes progressively capable of satisfying
both tenders?"

Give a sequence of concrete technical milestones.

Avoid generic advice.

Use actual SARVANETRA components.

============================================================
OUTPUT FILES
============================================================

Create these Markdown files:

1. TENDER_REQUIREMENTS.md

Contains the normalized requirement catalogue for both tenders.

2. TENDER_READINESS.md

Contains:

- current SARVANETRA capability
- tender mapping
- current status
- evidence
- gaps
- third-party dependencies
- hardware dependencies
- compliance dependencies

3. TENDER_ROADMAP.md

Contains:

- P0
- P1
- P2
- P3
- implementation phases
- dependencies
- target architecture
- recommended sequence

Do NOT modify source code.

============================================================
FINAL REVIEW
============================================================

Before finishing:

1. Cross-check all requirements against the tender PDFs.
2. Cross-check SARVANETRA claims against actual source code.
3. Remove unsupported assumptions.
4. Clearly mark unknowns.
5. Never mark a feature green without implementation evidence.
6. Separate hardware requirements from software requirements.
7. Separate OEM/eligibility requirements from technical requirements.
8. Separate "can implement" from "already implemented".
9. Identify contradictory or ambiguous tender requirements.
10. Identify requirements that require clarification from the tender authority.
11. Identify requirements that should be handled by third-party OEM products.
12. Identify requirements that SARVANETRA should own as the software platform.

============================================================
FINAL REPORT
============================================================

At the end provide:

## Executive Summary

## Tender A Readiness

## Tender B Readiness

## Current SARVANETRA Strengths

## Major Gaps

## Requirements That Need Third-Party Products

## Requirements Outside the Software Platform

## Critical Architecture Changes

## Top 10 Development Priorities

## Immediate Next Development Task

## Tender Clarifications / Ambiguities

## Risks

## Recommended Target Architecture

Be precise and evidence-based.

Do not claim tender compliance merely because something is architecturally
possible.

Use this distinction rigorously:

ALREADY IMPLEMENTED
PARTIALLY IMPLEMENTED
ARCHITECTURALLY POSSIBLE
REQUIRES DEVELOPMENT
REQUIRES THIRD-PARTY
REQUIRES HARDWARE
REQUIRES OEM/CERTIFICATION
REQUIRES ORGANIZATIONAL QUALIFICATION
UNKNOWN