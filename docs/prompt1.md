You are performing a CODEBASE ARCHAEOLOGY, CURRENT-STATE RECOVERY, and DOCUMENTATION CONSOLIDATION exercise for the SARVANETRA project.

I have not actively worked on this repository for approximately two months.

There are many Markdown and other documentation files under docs/. I no longer trust that all of them accurately describe the current implementation.

Your primary source of truth MUST be the actual repository contents:

* source code
* configuration
* Docker files
* database models and migrations
* API routes
* frontend implementation
* scripts
* tests
* service configuration

Existing documentation is secondary evidence only.

==================================================
OBJECTIVE
=========

Recover the actual current state of SARVANETRA and leave the repository with two canonical project documents:

1. PROJECT_STATE.md
2. PROJECT_ROADMAP.md

The documents must allow a developer returning after a two-month absence to understand:

* what the system currently is
* what is actually implemented
* what is partially implemented
* what is broken
* what was only planned/documented
* what remains to be completed
* what should be worked on next

Do NOT modify application/source code during this exercise.

Only documentation may be created, updated, moved, or deleted.

==================================================
IMPORTANT RULES
===============

1. Never assume that documentation is correct.
2. Never mark a feature as implemented merely because a document says it is implemented.
3. Verify important claims against actual code/configuration.
4. Distinguish between:

   * code exists
   * feature is wired into the system
   * feature is tested
   * feature is likely operational
5. When evidence is insufficient, mark the item:
   UNKNOWN / REQUIRES VERIFICATION
6. Do not invent functionality.
7. Do not refactor or "fix" application code.
8. Do not delete useful historical information before preserving it.
9. Cite repository file paths as evidence wherever practical.
10. Clearly distinguish current implementation from intended/future architecture.
11. Do not trust old task lists blindly; derive remaining work from the current codebase.
12. Keep PROJECT_STATE.md and PROJECT_ROADMAP.md internally consistent.

==================================================
PHASE 1 — COMPLETE REPOSITORY INVENTORY
=======================================

Inspect the repository structure and identify:

* backend
* frontend
* APIs
* services
* database
* migrations
* authentication
* authorization
* infrastructure
* Docker
* networking
* scripts
* tests
* configuration
* documentation
* streaming/media components
* messaging/event infrastructure
* storage
* monitoring/logging

Identify the technologies actually in use.

Pay particular attention to the SARVANETRA architecture involving, where present:

* FastAPI
* PostgreSQL
* Redis
* Kafka
* Kong
* MediaMTX
* MinIO
* Nginx
* Docker Compose
* ONVIF
* RTSP
* HLS
* recording pipeline
* frontend application

Do not assume every listed technology is still active. Verify it.

==================================================
PHASE 2 — DOCUMENTATION INVENTORY
=================================

Inspect ALL files under docs/.

For each significant document determine:

* purpose
* feature/component covered
* major claims
* whether claims match the current code
* whether the document is current
* whether it describes planned work
* whether it conflicts with implementation
* whether it duplicates another document

Create a mapping between documentation and code evidence.

For example:

Document:
docs/camera-onboarding.md

Claims:

* ONVIF discovery
* camera registration
* credential validation
* MediaMTX path creation

Code evidence:

* backend/...
* frontend/...
* scripts/...

Status:
PARTIALLY_IMPLEMENTED

Reason:
Camera registration exists, but automatic discovery could not be verified.

==================================================
PHASE 3 — RECONSTRUCT THE CURRENT ARCHITECTURE
==============================================

Reconstruct the architecture from actual implementation.

Document:

* services
* service responsibilities
* dependencies
* networks
* ports
* data stores
* event flows
* authentication flows
* streaming flows
* recording flows
* frontend/backend interactions

Explicitly trace real end-to-end flows.

For example, where supported by evidence:

Camera
↓
ONVIF / RTSP
↓
MediaMTX
↓
Recording
↓
Storage / MinIO
↓
Backend / playback

And:

Frontend
↓
Gateway / Nginx / Kong
↓
FastAPI
↓
PostgreSQL / Redis / Kafka / Media services

Only document flows actually supported by implementation.

==================================================
PHASE 4 — BACKEND ANALYSIS
==========================

Inspect the backend thoroughly.

Identify:

* entry point
* configuration
* routers
* API endpoints
* services
* repositories/data-access layer
* models
* schemas
* authentication
* authorization
* database access
* Redis usage
* Kafka usage
* MediaMTX integration
* MinIO integration
* background workers
* health checks
* logging
* error handling

Create an API inventory with:

METHOD
PATH
PURPOSE
IMPLEMENTATION FILE
AUTH REQUIREMENT
DEPENDENCIES
CURRENT STATUS

==================================================
PHASE 5 — DATABASE ANALYSIS
===========================

Inspect:

* ORM models
* migrations
* relationships
* indexes
* constraints
* initialization
* seed/admin setup

Reconstruct the current database structure.

Identify important entities such as, where applicable:

* users
* roles
* cameras
* streams
* recordings
* events
* devices
* permissions

Identify:

* migration inconsistencies
* multiple heads
* missing migrations
* stale models
* unused tables
* schema/code mismatches

==================================================
PHASE 6 — FRONTEND ANALYSIS
===========================

Inspect:

* framework
* routing
* pages
* components
* authentication
* state management
* API clients
* camera UI
* dashboards
* live viewing
* recording UI
* playback
* error/loading states

Map frontend functionality to backend APIs.

Explicitly identify:

Frontend exists but backend functionality is missing.

And:

Backend functionality exists but frontend does not use it.

==================================================
PHASE 7 — CAMERA / ONVIF / RTSP / MEDIAMTX ANALYSIS
===================================================

This is a critical subsystem.

Trace the actual implementation of:

Camera onboarding
→ ONVIF
→ credentials
→ RTSP
→ MediaMTX
→ live stream
→ recording
→ storage
→ playback

Determine:

* how cameras are discovered
* how camera credentials are handled
* how RTSP paths are created
* how MediaMTX is configured
* how streams are authenticated
* how recordings are generated
* how recordings are transferred
* how MinIO is used
* how HLS is exposed
* how frontend obtains live streams
* what happens when cameras disconnect
* what happens when authentication fails

Inspect all relevant:

* scripts
* workers
* hooks
* APIs
* MediaMTX configuration
* Nginx configuration
* storage logic

==================================================
PHASE 8 — KAFKA / EVENTS
========================

Inspect:

* Kafka configuration
* topics
* producers
* consumers
* schemas
* event handlers
* retries
* error handling

Determine which event flows are actually implemented and which are merely configured or documented.

==================================================
PHASE 9 — INFRASTRUCTURE
========================

Inspect:

* docker-compose files
* Dockerfiles
* environment templates
* Nginx
* Kong
* MediaMTX
* PostgreSQL
* Redis
* MinIO
* Kafka
* health checks
* volumes
* networks
* dependencies

Determine which services are:

* required
* optional
* obsolete
* duplicated
* broken
* referenced but missing

Identify startup dependency problems and configuration inconsistencies.

==================================================
PHASE 10 — TEST ANALYSIS
========================

Inspect all tests.

Determine:

* tested features
* untested critical functionality
* stale tests
* broken tests
* missing integration tests
* missing end-to-end tests

Do not assume passing unit tests mean the complete system works.

==================================================
PHASE 11 — STATUS MATRIX
========================

Classify major features using exactly these statuses:

✅ IMPLEMENTED
🟡 PARTIALLY IMPLEMENTED
🔴 NOT IMPLEMENTED
⚠️ BROKEN / NEEDS FIX
❓ UNKNOWN / NEEDS VERIFICATION
📄 DOCUMENTED ONLY

For each major feature record:

Feature
Status
Evidence
Notes
Remaining work

==================================================
PHASE 12 — REMAINING WORK
=========================

Derive the remaining work from the actual repository.

Do not simply copy old TODO lists.

Categorize tasks as:

P0 — BLOCKING
P1 — CRITICAL
P2 — IMPORTANT
P3 — ENHANCEMENT

For every significant task include:

* task
* current state
* why it is needed
* affected components/files
* dependencies
* complexity: LOW / MEDIUM / HIGH

==================================================
PHASE 13 — TECHNICAL DEBT
=========================

Identify:

* dead code
* duplicated implementations
* stale documentation
* unused services
* broken configuration
* missing environment variables
* hard-coded configuration
* security weaknesses
* missing validation
* missing tests
* naming inconsistencies
* database migration issues
* Docker issues
* authentication issues
* networking assumptions
* fragile dependencies

Do not fix them.

Document them.

==================================================
PHASE 14 — RESUME-POINT ANALYSIS
================================

Determine where development currently stands.

Answer:

"What would I need to verify before making any new feature changes?"

Then identify:

1. immediate environment checks
2. blocking issues
3. broken components
4. incomplete functionality
5. safest development sequence
6. first meaningful development task

Base this entirely on the repository.

==================================================
PHASE 15 — CREATE PROJECT_STATE.md
==================================

Create:

PROJECT_STATE.md

Use this structure:

# SARVANETRA — Current Project State

## 1. Executive Summary

## 2. Current Implementation Status

## 3. Current Architecture

## 4. Repository Structure

## 5. Services and Responsibilities

## 6. Backend

## 7. Frontend

## 8. Database

## 9. Authentication & Authorization

## 10. Camera Management

## 11. ONVIF / RTSP

## 12. MediaMTX

## 13. Recording Pipeline

## 14. MinIO / Storage

## 15. HLS / Live Playback

## 16. Kafka / Event Processing

## 17. API Inventory

## 18. Docker / Infrastructure

## 19. Configuration

## 20. Testing

## 21. Known Problems

## 22. Documentation Conflicts

## 23. Technical Debt

## 24. End-to-End Data Flows

## 25. How to Run

## 26. What Is Currently Working

## 27. What Is Not Verified

## 28. Verification Checklist

This document is the canonical source of truth for:

"WHAT EXISTS NOW"

==================================================
PHASE 16 — CREATE PROJECT_ROADMAP.md
====================================

Create:

PROJECT_ROADMAP.md

Use this structure:

# SARVANETRA — Development Roadmap

## 1. Current Project Position

## 2. Completed Work

## 3. Partially Completed Work

## 4. Broken / Needs Fixing

## 5. Remaining Features

## 6. P0 — Blocking Tasks

## 7. P1 — Critical Tasks

## 8. P2 — Important Tasks

## 9. P3 — Enhancements

## 10. Technical Debt

## 11. Testing Roadmap

## 12. Security Hardening

## 13. Production Readiness

## 14. Recommended Development Sequence

## 15. Immediate Next Task

## 16. Future Architecture / Deferred Ideas

This document is the canonical source of truth for:

"WHAT NEEDS TO HAPPEN NEXT"

==================================================
PHASE 17 — DOCUMENTATION CLEANUP
================================

After generating the two canonical documents, review every file under docs/.

Classify each document as:

KEEP
MERGE
ARCHIVE
DELETE

Definitions:

KEEP

* current and useful
* not redundant with the two canonical documents

MERGE

* contains useful information
* useful information should be transferred into PROJECT_STATE.md or PROJECT_ROADMAP.md

ARCHIVE

* historically useful
* no longer represents the current system

DELETE

* obsolete
* duplicate
* empty
* misleading
* fully superseded
* contains no information worth retaining

IMPORTANT:

Do NOT immediately delete anything.

First create:

DOCUMENTATION_CLEANUP.md

with:

| Document | Classification | Reason | Information Preserved In |
| -------- | -------------- | ------ | ------------------------ |

Then:

1. Incorporate useful information from MERGE documents into the canonical documents.
2. Move ARCHIVE documents into:
   docs/archive/
3. Delete DELETE documents.
4. Keep genuinely useful current documents.
5. Do not delete README files, configuration, source code, migrations, secrets, or operational files.
6. Do not delete a document merely because it is old.
7. Before deletion, verify that its useful information is either preserved or genuinely obsolete.

==================================================
PHASE 18 — FINAL CONSISTENCY CHECK
==================================

Before finishing:

1. Re-read PROJECT_STATE.md.
2. Re-read PROJECT_ROADMAP.md.
3. Verify major claims against the repository.
4. Remove unsupported assumptions.
5. Mark uncertainty explicitly.
6. Confirm completed work is backed by implementation evidence.
7. Confirm remaining tasks are genuinely remaining.
8. Confirm the architecture description matches the code.
9. Confirm API descriptions match the current routes.
10. Confirm documentation cleanup did not remove useful information.
11. Confirm the two canonical documents do not contradict one another.
12. Do not modify application/source code.

==================================================
FINAL RESPONSE
==============

Return a concise report containing:

* major components identified
* implemented features
* partially implemented features
* broken features
* major remaining tasks
* documentation kept
* documentation merged
* documentation archived
* documentation deleted
* top 5 actions I should take when resuming the project
* major uncertainties requiring manual verification

The final repository should have:

PROJECT_STATE.md
PROJECT_ROADMAP.md
DOCUMENTATION_CLEANUP.md
docs/archive/    (where applicable)

and no unnecessary duplicate project-state documentation.

Do not modify application code.
