Act as a senior software architect performing an INDEPENDENT REVIEW of the SARVANETRA project after a documentation consolidation exercise.

The repository now contains:

* PROJECT_STATE.md
* PROJECT_ROADMAP.md
* DOCUMENTATION_CLEANUP.md

Your job is to determine whether these documents accurately represent the ACTUAL CODEBASE.

Do not trust the documents simply because they were generated previously.

Use the repository itself as the source of truth.

==================================================
REVIEW OBJECTIVES
=================

Find anything that could cause me to resume development with an incorrect understanding of the project.

Specifically look for:

1. Features incorrectly marked as implemented
2. Missing implemented features
3. Features described as partial when they are actually complete
4. Features described as complete when important parts are missing
5. Incorrect architecture
6. Incorrect service dependencies
7. Incorrect API documentation
8. Incorrect database descriptions
9. Incorrect authentication flow
10. Incorrect camera/ONVIF/RTSP flow
11. Incorrect MediaMTX/recording flow
12. Incorrect Kafka/event flow
13. Incorrect frontend/backend integration
14. Broken infrastructure assumptions
15. Stale roadmap tasks
16. Missing roadmap tasks
17. Documentation claims unsupported by code
18. Important historical information that may have been lost
19. Documentation cleanup decisions that should be reversed

==================================================
REVIEW PROCESS
==============

For every major subsystem:

1. Inspect the relevant code.
2. Compare it against PROJECT_STATE.md.
3. Compare it against PROJECT_ROADMAP.md.
4. Report discrepancies.
5. Provide file-path evidence.

Pay particular attention to:

* FastAPI
* PostgreSQL
* Redis
* Kafka
* Kong
* MediaMTX
* MinIO
* Nginx
* Docker Compose
* frontend
* ONVIF
* RTSP
* HLS
* recordings
* authentication
* background workers
* scripts
* migrations
* tests

==================================================
STATUS VALIDATION
=================

Validate each major feature using:

✅ IMPLEMENTED
🟡 PARTIALLY IMPLEMENTED
🔴 NOT IMPLEMENTED
⚠️ BROKEN / NEEDS FIX
❓ UNKNOWN / NEEDS VERIFICATION

Do not upgrade a status without evidence.

==================================================
ROADMAP VALIDATION
==================

Check whether the roadmap reflects the actual repository.

Identify:

* missing blocking issues
* tasks that are already complete
* tasks that are no longer relevant
* dependencies between tasks
* important technical debt omitted from the roadmap
* important testing/security/production work omitted

Do not provide political or subjective judgments about product direction. Focus only on technical state and documented implementation needs.

==================================================
CORRECTIONS
===========

You may modify ONLY:

* PROJECT_STATE.md
* PROJECT_ROADMAP.md
* DOCUMENTATION_CLEANUP.md

Do not modify:

* application source code
* tests
* Docker configuration
* database migrations
* scripts
* deployment configuration

Correct any factual/documentation errors you find.

==================================================
FINAL OUTPUT
============

At the end, provide:

## Verification Result

### Confirmed Accurate

What the documents correctly captured.

### Corrections Made

What you changed and why.

### Remaining Uncertainty

What cannot be verified from the repository alone.

### Critical Issues

Technical issues that should be addressed before major feature development resumes.

### Resume Point

State the concrete technical area I should inspect first when I begin working on SARVANETRA again.

### First 5 Actions

Give five concrete actions, including relevant files, commands, services, or tests where possible.

Do not modify application code.
