You are a Senior Solution Architect and Government Surveillance Tender
Analyst.

I have provided TWO tender documents:

TENDER A:
Pathanamthitta District Police / Government of Kerala
Integrated ANPR, AI-based Parking Management System, CCTV Surveillance,
Redundant Network, UPS/Power Backup and Control Room modernization.

TENDER B:
KELTRON EOI
Selection of an End-to-End Custom Development, Implementation,
and Financing Partner for AI-Based Surveillance Projects.

I also have the SARVANETRA codebase and its current project documentation.

Your task is to perform a THREE-WAY COMPARISON:

TENDER A
vs
TENDER B
vs
CURRENT SARVANETRA

The goal is to identify the common platform capabilities that SARVANETRA
should build or strengthen so that the same core product can support
multiple government surveillance tenders rather than becoming a
one-tender-specific application.

============================================================
1. COMPARE THE TWO TENDERS
============================================================

Create a requirement comparison between Tender A and Tender B.

For every major capability classify it as:

COMMON TO BOTH
TENDER A ONLY
TENDER B ONLY
RELATED BUT DIFFERENT
NOT COMPARABLE

Cover at minimum:

- CCTV / Video Management
- Live video
- Recording
- Playback
- Evidence export
- Camera management
- ONVIF
- RTSP
- ANPR
- Vehicle classification
- Vehicle tracking
- Watchlist / blacklist
- Parking management
- Parking occupancy
- Parking allocation
- People counting
- Queue analytics
- Crowd density
- Heat maps
- Traffic analytics
- Predictive analytics
- Missing person identification
- Face search
- Incident management
- Alerts
- Event correlation
- GIS
- Command and Control Centre
- Public Address
- Digital signage / VMS
- Drone integration
- IoT integration
- Mobile access
- Reporting
- Audit
- RBAC
- APIs
- Third-party integration
- High availability
- Disaster recovery
- Cloud deployment
- On-premises deployment
- Hybrid deployment
- Cybersecurity
- Privacy
- Data retention
- Source code / IP
- Training
- SLA / support
- Hardware
- Networking
- UPS / power

Do not assume that similar words mean identical requirements.

Explain the actual distinction.

============================================================
2. CREATE A REQUIREMENT MATRIX
============================================================

Create a table:

| Capability | Tender A | Tender B | Common Requirement | Difference |

For each row explain the difference in practical engineering terms.

Example:

| ANPR | Entry/exit + vehicle data + 90-day retention |
| ANPR | broader vehicle intelligence/search/tracking |
| Common | Yes |
| Difference | Tender B expects ANPR as part of a broader mobility/intelligence platform |

Do this systematically.

============================================================
3. IDENTIFY THE "COMMON CORE PLATFORM"
============================================================

From both tenders, determine the smallest common platform that could
serve as the foundation for both.

Think in terms of modules:

1. Device / Camera Management
2. Video Ingestion
3. Streaming
4. Recording
5. Object Storage
6. Event Engine
7. AI Analytics
8. ANPR
9. Parking
10. Alert Management
11. Incident Management
12. Investigation / Evidence
13. GIS
14. Command Centre
15. Reporting
16. IAM / RBAC
17. Audit
18. Integration/API Gateway
19. Observability
20. HA / DR

Mark each module:

CORE COMMON
PROJECT-SPECIFIC
OPTIONAL
THIRD-PARTY

============================================================
4. COMPARE WITH CURRENT SARVANETRA
============================================================

Now compare the common platform against the actual SARVANETRA codebase.

For every common capability determine:

CURRENTLY IMPLEMENTED
PARTIALLY IMPLEMENTED
ARCHITECTURALLY PRESENT
NOT IMPLEMENTED
THIRD-PARTY DEPENDENCY
HARDWARE DEPENDENCY
UNKNOWN

Use actual source-file evidence.

Do NOT treat documentation as proof of implementation.

============================================================
5. IDENTIFY SARVANETRA'S CURRENT POSITION
============================================================

Answer:

What kind of system is SARVANETRA today?

For example, determine whether the current implementation is primarily:

- VMS
- surveillance backend
- video ingestion platform
- recording platform
- event platform
- AI surveillance platform
- command-and-control platform
- or a combination

Base the answer only on the repository.

============================================================
6. FIND THE BIGGEST GAP BETWEEN SARVANETRA
AND THE COMMON REQUIREMENTS
============================================================

Identify the major architectural gaps.

Group them under:

A. Video Platform
B. AI/Analytics
C. Event Architecture
D. ANPR
E. Parking
F. Investigation
G. ICCC
H. GIS
I. Integrations
J. Security
K. HA/DR
L. Reporting
M. Operations / O&M

For each gap provide:

Current State
Required State
Gap
Affected Components
Implementation Difficulty
Dependencies

============================================================
7. DISTINGUISH PRODUCT CAPABILITIES FROM INTEGRATIONS
============================================================

For each capability determine whether SARVANETRA should:

BUILD IT
INTEGRATE IT
ORCHESTRATE IT
STORE ITS DATA
DISPLAY ITS OUTPUT
OR LEAVE IT TO OEM HARDWARE

Examples:

ANPR:
Could be performed by camera/edge AI while SARVANETRA manages
events, search, storage, correlation and investigation.

Drone:
SARVANETRA may integrate drone video rather than build drone
hardware/software.

PA:
SARVANETRA may issue commands through an external PA platform.

GIS:
SARVANETRA may consume GIS services and display surveillance data.

Make these architectural boundaries explicit.

============================================================
8. COMPARE THE ARCHITECTURAL DEMANDS
============================================================

Determine how the architecture implied by Tender A differs from
Tender B.

Tender A may represent a more focused deployment involving:

- specific site
- parking
- ANPR
- CCTV
- networking
- control room
- power
- fixed operational workflows

Tender B represents a broader reusable platform.

Explain what architectural features SARVANETRA needs in order to support
both without duplicating the codebase.

Focus on:

- modularity
- plugin architecture
- event-driven architecture
- APIs
- multi-site
- hierarchy
- multi-tenancy
- integrations
- AI providers
- device abstraction
- storage abstraction
- workflow abstraction

============================================================
9. COMMON VS PROJECT-SPECIFIC
============================================================

Produce two lists:

COMMON PLATFORM CAPABILITIES

and

PROJECT-SPECIFIC CAPABILITIES

For example:

COMMON:
- camera management
- live streaming
- recording
- alerts
- RBAC
- audit
- evidence
- APIs
- analytics
- ANPR integration
- event processing

PROJECT-SPECIFIC:
- Nilakkal 12-zone parking allocation
- particular OFC topology
- UPS replacement
- specific camera quantities
- specific control room equipment
- particular government integrations

This distinction is extremely important.

============================================================
10. PRODUCT STRATEGY FROM AN ENGINEERING PERSPECTIVE
============================================================

Without making commercial predictions, determine what the technical
comparison implies for SARVANETRA architecture.

Answer:

"What should be reusable platform functionality?"

and:

"What should be implemented as site/project-specific modules?"

Create:

SARVANETRA CORE
+
PLUGIN / MODULE LAYER
+
INTEGRATION LAYER
+
PROJECT CONFIGURATION

Explain which tender capabilities belong in each layer.

============================================================
11. DEVELOPMENT PRIORITY
============================================================

Using BOTH tender requirements, rank development priorities by:

P0 — foundational/blocking
P1 — common high-value capability
P2 — tender-specific capability
P3 — future enhancement

Do NOT rank the tenders themselves.

Rank engineering work only.

The priority should reflect architectural dependency, not personal
preference.

============================================================
12. TARGET ARCHITECTURE
============================================================

Produce a target architecture that can support both tenders.

Show:

Cameras / Sensors
        ↓
Edge / AI
        ↓
Video Ingestion
        ↓
Media / Streaming
        ↓
Recording / Object Storage
        ↓
Event Bus
        ↓
AI Analytics
        ↓
Event Correlation
        ↓
Investigation / Evidence
        ↓
Command Centre / GIS / Dashboards
        ↓
External Integrations

Also show:

IAM
Audit
Observability
API Gateway
HA / DR

around the platform.

============================================================
13. FINAL COMPARISON
============================================================

Create these tables:

### Table 1 — Tender A vs Tender B

| Capability | Tender A | Tender B | Common/Unique | Notes |

### Table 2 — Common Platform vs SARVANETRA

| Common Capability | SARVANETRA Status | Evidence | Gap | Work Required |

### Table 3 — Build vs Integrate

| Capability | Build in SARVANETRA | Integrate | External Hardware/OEM | Reason |

### Table 4 — Development Roadmap

| Priority | Capability | Why | Dependency | SARVANETRA Component |

============================================================
14. MOST IMPORTANT FINAL QUESTION
============================================================

Answer this clearly:

"If we continue developing SARVANETRA, what architecture and capabilities
should we build so that the SAME CORE PLATFORM can subsequently be
configured for:

1. Nilakkal / Sabarimala-type surveillance and parking projects
2. KELTRON-type broader AI surveillance / ICCC projects
3. Similar future government surveillance projects?"

Do not propose building everything from scratch.

Reuse the existing SARVANETRA architecture wherever practical.

Identify:

KEEP
EXTEND
REFACTOR
ADD
INTEGRATE
DEFER

============================================================
15. OUTPUT
============================================================

Create one Markdown file:

TENDER_COMPARISON.md

Structure:

# SARVANETRA — Tender Comparison

## 1. Executive Summary
## 2. Tender A Overview
## 3. Tender B Overview
## 4. Tender A vs Tender B
## 5. Common Requirements
## 6. Tender-Specific Requirements
## 7. Common Platform Architecture
## 8. Current SARVANETRA Position
## 9. SARVANETRA vs Common Requirements
## 10. Build vs Integrate
## 11. Architecture Gaps
## 12. Data Model Implications
## 13. API Implications
## 14. AI/Analytics Implications
## 15. ICCC Implications
## 16. Security/Compliance Implications
## 17. Reusable Core vs Project Modules
## 18. Development Priorities
## 19. Target Architecture
## 20. Recommended Development Sequence
## 21. Remaining Unknowns
## 22. Final Engineering Conclusions

============================================================
RULES
============================================================

- Tender documents are the authoritative source for tender requirements.
- SARVANETRA source code is the authoritative source for current
  implementation.
- Do not invent missing requirements.
- Do not mark something implemented without code evidence.
- Clearly separate source-derived facts from architectural inference.
- Do not modify application code.
- Do not modify the existing tender documents.
- Only create/update TENDER_COMPARISON.md.