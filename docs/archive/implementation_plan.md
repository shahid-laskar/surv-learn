# Company Hierarchy Architecture — Implementation Plan

## Background

Phases 0–8 of Sarvanetra are **fully complete**. The current system is a working single-tenant surveillance platform with JWT auth (simple `role = admin | operator`), flat camera table, flat user table, and no org/customer/site structure.

The `company_hierarchy_arch.md` defines a full **Pan-India BSNL-grade multi-tenant architecture** with:
- Organization tree (ROOT → CIRCLE → BA → SSA → DISTRICT → SITE → NOC)
- Customers with hierarchy (ENTERPRISE, BANK, etc.)
- Customer Sites with geo-coordinates
- Fine-grained RBAC (Roles + Permission tables, replacing the current flat `role` string)
- Camera grouping (CameraGroup + mappings)
- Audit log, notifications, password reset, user sessions, device tokens

The goal of this plan is to implement all of this **on top of the existing running system** — non-destructively, in phases.

---

## User Review Required

> [!IMPORTANT]
> **Existing `survapp_user` table will be altered**, not replaced. The current `role VARCHAR(50)` column stays for backward-compatibility during migration, but new `organization_id`, `customer_id`, `user_type`, and related columns are added via Alembic migration. Existing `admin`/`operator` users continue to work.

> [!IMPORTANT]
> **Existing `survapp_camera_master` table will be altered** to add `customer_id`, `customer_site_id`, `organization_id`, `camera_model`, `manufacturer` columns. Existing camera rows get these fields as `NULL` — no data is lost.

> [!WARNING]
> **JWT payload structure changes.** The current token carries `{"sub": "username", "role": "admin"}`. The new token must carry `{"sub": user_id, "user_type": "EMPLOYEE", "org_id": 20, "customer_id": null, "roles": ["SSA_ADMIN"], "permissions": ["camera.view", ...]}`. All existing sessions become invalid on deploy — users will need to log in again.

> [!WARNING]
> **Kong JWT plugin:** Kong validates the token signature but does NOT know about roles/permissions — it only validates the `iss` claim and signature. All RBAC checks remain in FastAPI. This is unchanged from the current design.

> [!NOTE]
> **Approach — Two-phase migration strategy:**
> - **Phase A (DB + models)**: Add all new tables via Alembic migration 0003. Alter existing tables. No app code breaks.
> - **Phase B (RBAC + API)**: Update models, auth service, dependencies, and add new routers. Legacy `role` field deprecated but kept for one release.

---

## Open Questions

> [!IMPORTANT]
> **Q1: Seed data scope** — Should the migration auto-seed the organization tree (BSNL INDIA → Circles → BAs) and default roles + permissions, or leave that to a separate seed script?  
> *Recommendation: Separate seed script (`scripts/seed_hierarchy.py`) so it can be rerun and customized per deployment.*

> [!IMPORTANT]
> **Q2: Password reset flow** — The arch doc includes `password_reset_token`. Do we need email-based reset now, or just add the table for future use?  
> *Recommendation: Add the table now but wire the API in a later phase.*

> [!IMPORTANT]
> **Q3: Camera access control model** — The arch doc has two mechanisms:
> - **Role-scoped access**: user with `CIRCLE_ADMIN` role sees all cameras in their org subtree (via `organization_closure` table)
> - **Direct override**: `survapp_user_camera` for fine-grained per-user camera grants
>
> Should both be enforced simultaneously (union of access)? Recommendation: Yes — check org-subtree first, then fall back to direct grants.

> [!IMPORTANT]
> **Q4: Frontend scope** — Do we build the new org/customer/site management UI in this plan, or backend only?  
> *Recommendation: Backend first (all APIs), frontend pages in a follow-up.*

---

## Proposed Changes

### Phase A — Database Layer (Migration 0003)

#### [NEW] [0003_company_hierarchy.py](file:///opt/surv-learn/surv/app/alembic/versions/0003_company_hierarchy.py)

Single Alembic migration that creates all new tables and alters existing ones:

**New tables** (in dependency order):
1. `organization` — tree of org nodes (BIGSERIAL PK, self-referencing `parent_id`)
2. `organization_closure` — precomputed ancestor/descendant pairs for fast subtree queries
3. `customer` — customer entity, references `organization`
4. `customer_site` — physical sites of a customer (lat/lon)
5. `survapp_role` — named roles (SUPER_ADMIN, CIRCLE_ADMIN, etc.)
6. `survapp_permission` — permission codes (camera.view, camera.live, etc.)
7. `survapp_role_permission` — M2M role ↔ permission
8. `survapp_user_role` — M2M user ↔ role
9. `survapp_user_camera` — per-user camera overrides
10. `camera_group` — named camera groups
11. `camera_group_mapping` — M2M group ↔ camera
12. `user_group_mapping` — M2M user ↔ group
13. `user_session` — refresh token sessions (UUID PK)
14. `device_token` — FCM push tokens
15. `audit_log` — immutable audit trail (JSONB old/new value)
16. `notification` — user notifications (JSONB payload)
17. `password_reset_token` — time-boxed reset tokens

**Alterations to existing tables:**

`survapp_user` — add columns:
- `email VARCHAR(255)`
- `mobile VARCHAR(20)`
- `first_name VARCHAR(100)`, `last_name VARCHAR(100)`
- `user_type VARCHAR(30) DEFAULT 'EMPLOYEE'`
- `organization_id BIGINT REFERENCES organization(id)`
- `customer_id BIGINT REFERENCES customer(id)`
- `is_locked BOOLEAN DEFAULT FALSE`
- `failed_login_count INTEGER DEFAULT 0`
- `last_password_change TIMESTAMPTZ`
- `created_by BIGINT`, `updated_by BIGINT`
- `updated_at TIMESTAMPTZ DEFAULT NOW()`

`survapp_camera_master` — add columns:
- `customer_id BIGINT REFERENCES customer(id)`
- `customer_site_id BIGINT REFERENCES customer_site(id)`
- `organization_id BIGINT REFERENCES organization(id)`
- `camera_model VARCHAR(100)`
- `manufacturer VARCHAR(100)`

---

### Phase B — SQLAlchemy Models

#### [MODIFY] [models/user.py](file:///opt/surv-learn/surv/app/models/user.py)
Expand `User` model with all new columns. Add new models:
- `Organization` + `OrganizationClosure`
- `Customer` + `CustomerSite`
- `Role` + `Permission` + `RolePermission` + `UserRole`
- `UserCamera` + `CameraGroup` + `CameraGroupMapping` + `UserGroupMapping`
- `UserSession` + `DeviceToken`
- `AuditLog` + `Notification` + `PasswordResetToken`

#### [MODIFY] [models/camera.py](file:///opt/surv-learn/surv/app/models/camera.py)
Add `customer_id`, `customer_site_id`, `organization_id`, `camera_model`, `manufacturer` columns to `Camera` model. Add relationships to `Customer`, `CustomerSite`, `Organization`.

#### [NEW] [models/\_\_init\_\_.py](file:///opt/surv-learn/surv/app/models/__init__.py)
Re-export all models so Alembic's `env.py` can discover them from a single import.

---

### Phase C — Auth Service & JWT Overhaul

#### [MODIFY] [services/auth_service.py](file:///opt/surv-learn/surv/app/services/auth_service.py)
- `create_access_token` now takes `user_id: int`, `user_type: str`, `org_id: int | None`, `customer_id: int | None`, `roles: list[str]`, `permissions: list[str]`
- JWT payload becomes the structure defined in `company_hierarchy_arch.md`:
  ```json
  {"sub": 125, "user_type": "EMPLOYEE", "org_id": 20, "customer_id": null, "roles": ["SSA_ADMIN"], "permissions": ["camera.view"], "session_id": "uuid", "iss": "sarvanetra-app", "exp": ...}
  ```
- Add `create_session(user_id, device_info, ip) -> UserSession` that persists a session row and returns the `session_id` UUID embedded in the JWT
- Add `revoke_session(session_id)` for logout

#### [MODIFY] [dependencies/auth.py](file:///opt/surv-learn/surv/app/dependencies/auth.py)
- `CurrentUser` dataclass expands to hold `user_id`, `user_type`, `org_id`, `customer_id`, `roles: list[str]`, `permissions: list[str]`, `session_id`
- `get_current_user` now resolves `CurrentUser` from the richer JWT payload
- Replace `require_admin` with a general `require_permission(perm: str)` dependency factory:
  ```python
  def require_permission(perm: str):
      async def checker(user: CurrentUser = Depends(get_current_user)):
          if perm not in user.permissions:
              raise HTTPException(403, f"Permission '{perm}' required")
          return user
      return checker
  ```
- Add `require_role(role: str)` for role-level checks
- Keep `require_admin` as `require_role("SUPER_ADMIN")` for backward-compat

---

### Phase D — New Routers

#### [NEW] [routers/organizations.py](file:///opt/surv-learn/surv/app/routers/organizations.py)
```
GET    /api/v1/org/                        # list all (admin)
POST   /api/v1/org/                        # create org node (admin)
GET    /api/v1/org/{id}                    # get node + children
GET    /api/v1/org/{id}/subtree            # all descendants via closure table
PATCH  /api/v1/org/{id}                   # update name/type
DELETE /api/v1/org/{id}                   # soft delete
```

#### [NEW] [routers/customers.py](file:///opt/surv-learn/surv/app/routers/customers.py)
```
GET    /api/v1/customers/
POST   /api/v1/customers/
GET    /api/v1/customers/{id}
PATCH  /api/v1/customers/{id}
GET    /api/v1/customers/{id}/sites
POST   /api/v1/customers/{id}/sites
```

#### [NEW] [routers/roles.py](file:///opt/surv-learn/surv/app/routers/roles.py)
```
GET    /api/v1/roles/
POST   /api/v1/roles/
GET    /api/v1/roles/{id}/permissions
POST   /api/v1/roles/{id}/permissions    # assign permission to role
DELETE /api/v1/roles/{id}/permissions/{perm_id}
POST   /api/v1/users/{id}/roles          # assign role to user
DELETE /api/v1/users/{id}/roles/{role_id}
```

#### [MODIFY] [routers/auth.py](file:///opt/surv-learn/surv/app/routers/auth.py)
- `POST /login` — query user's roles + permissions from DB, embed in JWT, create `UserSession` row
- `POST /logout` — revoke the session (set `is_active=False` on `user_session`)
- `GET /me` — return expanded user info (org, customer, roles, permissions)
- `POST /users` — expanded `UserCreate` with `user_type`, `organization_id`, `customer_id`, `first_name`, `last_name`, `email`, `mobile`

#### [NEW] [routers/audit.py](file:///opt/surv-learn/surv/app/routers/audit.py)
```
GET /api/v1/audit/?entity_type=camera&entity_id=...&user_id=...
```
Requires `system.audit` permission.

#### [NEW] [routers/camera_groups.py](file:///opt/surv-learn/surv/app/routers/camera_groups.py)
```
GET    /api/v1/camera-groups/
POST   /api/v1/camera-groups/
POST   /api/v1/camera-groups/{id}/cameras
DELETE /api/v1/camera-groups/{id}/cameras/{cam_id}
```

---

### Phase E — Camera Access Control Layer

#### [NEW] [services/access_service.py](file:///opt/surv-learn/surv/app/services/access_service.py)

Core access-check logic used by all camera endpoints:

```python
async def get_accessible_cameras(user: CurrentUser, db: AsyncSession) -> list[int]:
    """
    Returns list of camera IDs the user can access.
    
    Priority:
    1. SUPER_ADMIN / NATIONAL_NOC → all cameras (no filter)
    2. Org-scoped roles (CIRCLE_ADMIN, BA_ADMIN, etc.) →
       cameras whose organization_id is in the user's org subtree
       (uses organization_closure table)
    3. Direct grants in survapp_user_camera → union with above
    4. Camera group membership → union with above
    """
```

#### [MODIFY] [routers/cameras.py](file:///opt/surv-learn/surv/app/routers/cameras.py)
- `GET /cameras/` filters by `get_accessible_cameras()` instead of returning all
- `POST /cameras/` requires `camera.create` permission
- `PATCH /cameras/{id}` requires `camera.update` permission
- `DELETE /cameras/{id}` requires `camera.delete` permission

#### [MODIFY] [routers/streams.py](file:///opt/surv-learn/surv/app/routers/streams.py)
- Stream URL endpoints check `camera.live` permission

#### [MODIFY] [routers/recordings.py](file:///opt/surv-learn/surv/app/routers/recordings.py)
- Timeline + download endpoints check `camera.playback` / `camera.download` permissions

---

### Phase F — Seed Script

#### [NEW] [scripts/seed_hierarchy.py](file:///opt/surv-learn/surv/scripts/seed_hierarchy.py)

Idempotent seed script (safe to rerun). Seeds:
1. **Organizations**: BSNL INDIA → Kerala Circle → Trivandrum BA → sample SSAs/Sites
2. **All roles**: SUPER_ADMIN, NATIONAL_NOC, CIRCLE_ADMIN, BA_ADMIN, SSA_ADMIN, SITE_ADMIN, OPERATOR, VIEWER, CUSTOMER_ADMIN, CUSTOMER_OPERATOR, CUSTOMER_VIEWER, PARTNER_ADMIN, PARTNER_ENGINEER, AUDITOR
3. **All permissions**: `camera.*`, `user.*`, `customer.*`, `report.*`, `system.*`
4. **Role-permission mappings**: logical defaults (SUPER_ADMIN gets all, VIEWER gets only view/live, etc.)
5. **Upgrades the existing `admin` user**: assigns `SUPER_ADMIN` role + `user_type = EMPLOYEE`

---

### Phase G — Schemas

#### [MODIFY] [schemas/auth.py](file:///opt/surv-learn/surv/app/schemas/auth.py)
- `TokenResponse` adds `roles: list[str]`, `permissions: list[str]`, `user_type: str`
- `UserCreate` adds `user_type`, `organization_id`, `customer_id`, `first_name`, `last_name`, `email`, `mobile`
- `UserOut` adds same fields + `roles: list[str]`, `permissions: list[str]`

#### [NEW] [schemas/organization.py](file:///opt/surv-learn/surv/app/schemas/organization.py)
- `OrganizationCreate`, `OrganizationOut`, `OrganizationTree`

#### [NEW] [schemas/customer.py](file:///opt/surv-learn/surv/app/schemas/customer.py)
- `CustomerCreate`, `CustomerOut`, `CustomerSiteCreate`, `CustomerSiteOut`

#### [NEW] [schemas/rbac.py](file:///opt/surv-learn/surv/app/schemas/rbac.py)
- `RoleOut`, `PermissionOut`, `RolePermissionAssign`, `UserRoleAssign`

---

### Phase H — main.py

#### [MODIFY] [main.py](file:///opt/surv-learn/surv/app/main.py)
Register new routers: `organizations`, `customers`, `roles`, `audit`, `camera_groups`.

---

## Migration Sequence (Final Order)

```
0001_initial          ← already applied (camera, motion_event, video_segment)
0002_add_users        ← already applied (survapp_user)
0003_company_hierarchy ← NEW: all new tables + alters existing tables
```

Migration 0003 must handle the fact that the `survapp_user` table already exists — it uses `op.add_column()` on the existing table, not `op.create_table()`.

---

## Verification Plan

### Automated Tests
```bash
# After applying migration
docker compose build app
docker compose run --rm db_migrate

# Verify all tables created
docker compose exec postgres psql -U surv -d sarvanetra -c "\dt"

# Run seed script
docker compose exec app python3 scripts/seed_hierarchy.py

# Smoke test: login still works for existing admin user
curl -X POST http://10.44.0.209:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"<your-password>"}'

# New JWT should contain roles + permissions
# Decode and verify payload at jwt.io

# Verify camera list still works with new access control
curl -H "Authorization: Bearer <token>" http://10.44.0.209:8000/api/v1/cameras/

# Verify org creation
curl -X POST http://10.44.0.209:8000/api/v1/org/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"BSNL INDIA","code":"ROOT","type":"ROOT"}'
```

### Manual Verification
- Existing camera streams still play after migration
- Existing motion events still appear
- Admin user can create sub-org nodes and customers
- VIEWER-role user cannot access `POST /cameras/`
- CIRCLE_ADMIN user only sees cameras in their org subtree
- Audit log row is created for camera create/update/delete actions

---

## Implementation Order (Execution)

1. `0003_company_hierarchy.py` — Alembic migration (additive, non-breaking)
2. Update SQLAlchemy models (user.py, camera.py, new model files)
3. Update auth_service.py — richer JWT payload
4. Update dependencies/auth.py — new `CurrentUser`, `require_permission()`
5. Update schemas (auth.py + new schema files)
6. New routers: organizations, customers, roles, audit, camera_groups
7. Update existing routers: cameras, streams, recordings (permission checks)
8. Update auth router: login/logout/me/users
9. Update main.py — register new routers
10. Write seed script and run it
11. Phase I — BSNL Masters Integration (migration 0004, models, API updates)
12. Build + deploy + verify

---

### Phase I — Architecture Update: Preserve BSNL Masters

Per the updated `company_hierarchy_arch.md`, we must retain the legacy `circle_master` and `ba_master` tables.

#### 1. Database & Models
- Create `circle_master` and `ba_master` tables via a new Alembic migration (`0004_bsnl_masters.py`).
- Add foreign keys `circle_id` and `ba_id` to `organization`, `customer`, `survapp_user`, and `survapp_camera_master` tables in the same migration.
- Add `CircleMaster` and `BAMaster` models in `app/models/organization.py`.
- Update `Organization`, `Customer`, `User`, and `Camera` models to include `circle_id` and `ba_id` columns and relationships.

#### 2. Schemas & Routers
- Update Pydantic schemas in `app/schemas` (`UserCreate`, `UserOut`, `OrganizationCreate`, `CustomerCreate`, `CameraCreate`, etc.) to include optional `circle_id` and `ba_id` fields.
- Create simple CRUD routers for `circle_master` and `ba_master` if management endpoints are needed (or they can be read-only if synced from BSNL systems). Let's build basic read endpoints to support the frontend dropdowns.

#### 3. Seed Script
- Update `scripts/seed_hierarchy.py` to populate `circle_master` and `ba_master` tables before generating the `organization` tree.
- Map the created `circle_id` and `ba_id` into the corresponding `organization` entries during seeding.

---

*Current system baseline: Phases 0–8 complete (✅). Phases 9–11 (Health Monitoring, Retention, Hardening) remain pending and are unaffected by this plan.*
