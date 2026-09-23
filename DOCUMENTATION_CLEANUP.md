# SARVANETRA — Documentation Cleanup Plan & Audit Trail
**Date:** September 22, 2026  
**Canonical Sources Established:** [`PROJECT_STATE.md`](file:///opt/surv-learn/PROJECT_STATE.md) and [`PROJECT_ROADMAP.md`](file:///opt/surv-learn/PROJECT_ROADMAP.md)

---

## 1. Document Classification Summary

Every existing documentation file under `docs/` and root/subsystem directories has been audited against the actual codebase implementation. Files are classified into four actions:

- **KEEP:** Retained in place. The document is current, authoritative, and contains external domain specifications or compliance briefs not redundant with the canonical documents.
- **ARCHIVE:** Moved to [`docs/archive/`](file:///opt/surv-learn/docs/archive/). The document contains valuable historical context, phase design evolution, or operational walkthroughs that have been incorporated into canonical documents, but is no longer the current source of truth.
- **MERGE:** Information synthesized and merged into [`PROJECT_STATE.md`](file:///opt/surv-learn/PROJECT_STATE.md) or [`PROJECT_ROADMAP.md`](file:///opt/surv-learn/PROJECT_ROADMAP.md) prior to archiving.
- **DELETE:** Permanently deleted. The document is an unreferenced duplicate, raw scratch snippet, or obsolete DDL superseded by the codebase.

---

## 2. Master Cleanup Table

| Document | Classification | Reason | Information Preserved In |
|---|---|---|---|
| `docs/prompt1.md` | **KEEP** | Primary task prompt defining the Codebase Archaeology and Documentation Consolidation exercise. | Retained in place as project reference. |
| `docs/prompt2.md` | **KEEP** | Architectural review and validation prompt specification. | Retained in place as project reference. |
| `docs/tender_prompt.md` | **KEEP** | Analysis specification for Keltron and Kerala Police surveillance tenders. | Retained in place as tender compliance reference. |
| `docs/1789370597 (1).pdf` | **KEEP** | Pathanamthitta District Police / Kerala Home Dept Surveillance Tender document (PDF). | Retained in place as external tender requirements source. |
| `docs/Surveillance Tender-KELTRON (1).pdf` | **KEEP** | KELTRON Expression of Interest (EOI) for AI-based surveillance partner selection (PDF). | Retained in place as external tender requirements source. |
| `docs/setup/sarvanetra_technical_network_bf.md` | **KEEP** | Authoritative technical briefing explaining BSNL GPON FTTH dedicated VLAN 200 architecture and optical plant network design. | Retained in place; summarized in `PROJECT_STATE.md §1, §3`. |
| `docs/setup/company_hierarchy_arch.md` | **KEEP** | Foundational architectural model for Pan-India BSNL organization tree, closure table schema, and RBAC design. | Retained in place; summarized in `PROJECT_STATE.md §8, §9`. |
| `docs/setup/tls_setup.md` | **ARCHIVE** | Setup guide for mounting BSNL wildcard TLS certificates into Kong and Caddy. | `docs/archive/tls_setup.md`; details in `PROJECT_STATE.md §5, §18` and `PROJECT_ROADMAP.md §13`. |
| `docs/setup/implementation_plan_mediamtx.md` | **ARCHIVE** | Historical plan for MediaMTX REST API dynamic path registration. Fully implemented in `mediamtx_client.py`. | `docs/archive/implementation_plan_mediamtx.md`; details in `PROJECT_STATE.md §10, §12`. |
| `docs/setup/implementation_plan.md` | **ARCHIVE** | Historical implementation plan for multi-tenant hierarchy and RBAC. Fully implemented in migrations `0003` and `0004`. | `docs/archive/implementation_plan.md`; details in `PROJECT_STATE.md §8, §9`. |
| `docs/setup/implementation_plan_phase9+.md` | **ARCHIVE** | Historical plan for camera health monitoring, MinIO cleaner, and hardening. Fully implemented in code. | `docs/archive/implementation_plan_phase9+.md`; details in `PROJECT_STATE.md §14, §18`. |
| `docs/setup/workthrough_phase9.md` | **ARCHIVE** | Production readiness walkthrough of completed Phases 9, 10, 11. | `docs/archive/workthrough_phase9.md`; details in `PROJECT_STATE.md §14, §18`. |
| `docs/setup/sarvanetra_initial_build_plan.md` | **ARCHIVE** | Initial Phase 0–11 build plan. Superseded by actual codebase implementation and canonical state doc. | `docs/archive/sarvanetra_initial_build_plan.md`; details in `PROJECT_STATE.md §1, §5`. |
| `surv/sarvanetra_initial_build_plan.md` | **DELETE** | Exact byte-for-byte duplicate of `docs/setup/sarvanetra_initial_build_plan.md` placed in `surv/` directory. | Identical content preserved in `docs/archive/sarvanetra_initial_build_plan.md`. |
| `docs/setup/sarvanetra_status_plan.md` | **ARCHIVE** | Early phase tracking doc with outdated table names. Superseded by `sarvanetra_final_implementation_plan.md`. | `docs/archive/sarvanetra_status_plan.md`; details in `PROJECT_STATE.md §2, §22`. |
| `docs/setup/sarvanetra_architecture.md` | **ARCHIVE** | Early architecture document containing outdated references to Django and Konga. Superseded by `PROJECT_STATE.md`. | `docs/archive/sarvanetra_architecture.md`; details in `PROJECT_STATE.md §3, §22`. |
| `docs/setup/implementation_plan_frontend.md` | **ARCHIVE** | Historical frontend wiring plan for multi-tenant hierarchy pages. Fully implemented in React SPA. | `docs/archive/implementation_plan_frontend.md`; details in `PROJECT_STATE.md §7`. |
| `docs/frontend/plan.md` | **ARCHIVE** | Comprehensive frontend feature enhancement plan for video player, timeline, and themes. | `docs/archive/frontend_plan.md`; key items merged into `PROJECT_ROADMAP.md §8, §9`. |
| `docs/ftp.md` | **ARCHIVE** | Scratch sysadmin notes for vsftpd FTP server configuration. | `docs/archive/ftp.md`; referenced in `PROJECT_STATE.md §14`. |
| `docs/workflow/secret_rotation.md` | **ARCHIVE** | Operational runbook for Kong JWT secret rotation without service downtime. | `docs/archive/secret_rotation.md`; procedure in `PROJECT_STATE.md §9` and `PROJECT_ROADMAP.md §12`. |
| `docs/workflow/temp.md` | **DELETE** | Scratch raw SQL DDL statements (`CREATE TABLE...`) used before Alembic migrations existed. Completely obsolete. | Preserved in Alembic migrations `0001` & `0002`, and `PROJECT_STATE.md §8`. |
| `docs/workflow/workflow.md` | **DELETE** | Scratch dev snippets containing ad-hoc curl commands and duplicate docker-compose blocks. | Active configuration preserved in `surv/docker-compose.yml` and `PROJECT_STATE.md §25`. |
| `docs/status/sarvanetra_final_implementation_plan.md` | **ARCHIVE** | Prior authoritative implementation plan (2026-07-09). Superseded by `PROJECT_STATE.md` and `PROJECT_ROADMAP.md`. | `docs/archive/sarvanetra_final_implementation_plan.md`; core state in `PROJECT_STATE.md`. |
| `docs/status/phase_a_completion.md` | **ARCHIVE** | Completion sign-off note for Phase A (camera access enforcement gate). | `docs/archive/phase_a_completion.md`; details in `PROJECT_STATE.md §9`. |
| `docs/status/phase_b_completion.md` | **ARCHIVE** | Completion sign-off note for Phase B (Edge NVR core restructuring). | `docs/archive/phase_b_completion.md`; details in `PROJECT_STATE.md §4, §17`. |
| `docs/status/implementation_status.md` | **ARCHIVE** | Historical handoff document covering Phases 0–8 and known bugs hit. Already marked superseded. | `docs/archive/implementation_status.md`; details in `PROJECT_STATE.md §21, §22`. |
| `docs/status/sarvanetra_edge_vpn_extension.md` | **ARCHIVE** | Extension plan for Phases 12–14 (Edge NVR + WireGuard overlay). Already marked superseded. | `docs/archive/sarvanetra_edge_vpn_extension.md`; details in `PROJECT_STATE.md §1, §3`. |
| `docs/status/implementation_plan_phase 12+.md` | **ARCHIVE** | Early draft of Phase 12+ edge plan. Already marked superseded. | `docs/archive/implementation_plan_phase_12+.md`; details in `PROJECT_STATE.md §3`. |
| `docs/status/sarvanetra_vpn_access_plan_extends_phase_14.md` | **ARCHIVE** | Specification for remote access using official Tailscale client. Already marked superseded. | `docs/archive/sarvanetra_vpn_access_plan_extends_phase_14.md`; details in `PROJECT_ROADMAP.md §7`. |
| `docs/status/phase15_implementation.md` | **ARCHIVE** | Implementation proposal for same-VM edge simulation. Already implemented in `edge-sim/`. | `docs/archive/phase15_implementation.md`; details in `PROJECT_STATE.md §20`. |
| `docs/status/test_simulation.md` | **ARCHIVE** | Test simulation strategy without physical cameras. | `docs/archive/test_simulation.md`; details in `PROJECT_STATE.md §20`. |
| `docs/status/mobile_desin.md` | **ARCHIVE** | Specification for Expo/React Native mobile client with embedded WireGuard. | `docs/archive/mobile_desin.md`; details in `PROJECT_ROADMAP.md §9, §16`. |

---

## 3. Post-Cleanup Directory State

Following execution of this plan:
1. **Canonical Docs:**
   - [`PROJECT_STATE.md`](file:///opt/surv-learn/PROJECT_STATE.md) (The complete, code-verified state of what exists now)
   - [`PROJECT_ROADMAP.md`](file:///opt/surv-learn/PROJECT_ROADMAP.md) (The development roadmap of what must happen next)
   - [`DOCUMENTATION_CLEANUP.md`](file:///opt/surv-learn/DOCUMENTATION_CLEANUP.md) (This audit log)
2. **Current Project Specifications:**
   - `docs/setup/sarvanetra_technical_network_bf.md` (BSNL FTTH GPON VLAN 200 Brief)
   - `docs/setup/company_hierarchy_arch.md` (BSNL Pan-India Hierarchy Model)
   - `docs/tender_prompt.md` (Tender Analysis Prompt)
   - `docs/1789370597 (1).pdf` & `docs/Surveillance Tender-KELTRON (1).pdf` (Original Tender Documents)
   - `docs/prompt1.md` & `docs/prompt2.md` (Archaeology and Validation Prompts)
3. **Historical Archive:**
   - `docs/archive/` (Contains all superseded and historical phase documentation)
