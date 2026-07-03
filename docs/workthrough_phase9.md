# Production Readiness Walkthrough

We have successfully completed all remaining phases (9, 10, and 11) of the Sarvanetra project to prepare it for production deployment.

## What was completed

### 1. Phase 9: Camera Health Monitoring
- **Backend Infrastructure:** Created an Alembic migration for the `camera_status_log` table.
- **Workers:** Upgraded `workers/status_monitor.py` to maintain status duration logs and trigger alerts when cameras go offline. Also implemented `workers/notifier.py` to handle webhook-based alerting.
- **Health Dashboard:** Implemented a new dashboard view (`/health`) that provides a real-time aggregate of offline cameras, overall worker connectivity, and historical uptime tracking.

### 2. Phase 10: Retention & Cleanup Governance
- **Automated Cleanup Worker:** Added `minio_cleaner` as a dedicated service within Docker Compose. It enforces per-camera retention policies by scanning the MinIO storage backend and scrubbing old recordings.
- **Database Tracking:** Added a `retention_days` column to the `survapp_camera_master` table to allow per-camera overrides of the global retention limit.
- **Global Lifecycle Safety Net:** Implemented an S3-level lifecycle configuration in MinIO to act as a fallback safeguard against orphaned objects.

### 3. Phase 11: Hardening & Security
- **Production Overrides:** Created `docker-compose.prod.yml` to close all unnecessary internal ports. This ensures that the only entry points to the server are through the Kong Gateway and Nginx.
- **TLS Configuration:** Provided complete support for wildcard TLS deployment (`*.bsnl.co.in`). Kong will dynamically load your `star_bsnl_co_in.crt` and `star_bsnl_co_in.key` at startup. Nginx is configured to serve the frontend via `8443 ssl`.
- **CORS Hardening:** Configured FastAPI to whitelist strict origins from `CORS_ALLOWED_ORIGINS` instead of accepting wildcard requests.
- **Non-Root Execution:** Restricted Docker containers (`Dockerfile.worker`, `app/Dockerfile`, `Dockerfile.frontend`) to execute under unprivileged user accounts (`appuser` and `nginx-unprivileged`) to minimize the potential attack surface.

## Verification & Next Steps

1. **Deploying the Application:** When running on your production VM, you can now launch the stack in secure mode:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```
2. **Reviewing Guides:** Two new documentation guides have been placed in your `docs` folder:
   - [tls_setup.md](file:///opt/surv-learn/docs/tls_setup.md): Walkthrough of providing your BSNL SSL certificates to the volume mount.
   - [secret_rotation.md](file:///opt/surv-learn/docs/secret_rotation.md): Instructions for performing zero-downtime JWT secret rotations.

The codebase is now fully configured and hardened to support production deployment!
