# Frontend Wiring — Implementation Plan

## Background

The backend (Phases A–I) is fully implemented with the new multi-tenant hierarchy architecture.
The frontend is still the old Phase 0–8 single-tenant UI with:
- `client.ts` — old `LoginResponse` (no `roles`, `permissions`), no org/customer/role/audit API calls
- `ProtectedRoute.tsx` — only clears `role` from localStorage (legacy flat role)
- `Login.tsx` — stores `res.role` (legacy string)
- `Sidebar.tsx` — reads `role` from localStorage, no permission-based nav hiding
- No pages for: Organizations, Customers, Roles/Permissions, Audit Log, Users, Camera Groups

## New Pages to Build

| Page | Route | Backend APIs Used |
|------|-------|-------------------|
| Organizations | `/org` | `GET /api/v1/org/`, `POST /api/v1/org/`, `GET /api/v1/org/{id}/subtree` |
| Customers | `/customers` | `GET /api/v1/customers/`, `POST /api/v1/customers/`, sites CRUD |
| Users | `/users` | `GET /auth/users`, `POST /auth/users`, `POST /users/{id}/roles` |
| Roles & Permissions | `/roles` | `GET /roles/`, `GET /permissions/`, assign/remove |
| Audit Log | `/audit` | `GET /audit/` |
| Camera Groups | `/camera-groups` | `GET /camera-groups/`, `POST`, camera assign |

---

## Proposed Changes

### 1. `api/client.ts` — Expand types & add API calls

**Types to add/update:**
- `LoginResponse` — add `roles: string[]`, `permissions: string[]`, `user_type`, `org_id`, `customer_id`
- `CurrentUser` — add `email`, `mobile`, `first_name`, `last_name`, `user_type`, `is_locked`, `organization_id`, `customer_id`, `circle_id`, `ba_id`, `roles`, `permissions`
- New: `Organization`, `OrganizationCreate`, `Customer`, `CustomerCreate`, `CustomerSite`, `CustomerSiteCreate`, `Role`, `Permission`, `RoleCreate`, `CameraGroup`, `CameraGroupCreate`, `AuditLog`

**API functions to add:**
- `callLogout()` — `POST /auth/logout` (server-side session revocation) before clearing localStorage
- `fetchUsers()`, `createUser()`, `assignRoleToUser(userId, roleId)`, `removeRoleFromUser(userId, roleId)`
- `fetchOrgs()`, `createOrg()`, `fetchSubtree(orgId)`
- `fetchCustomers()`, `createCustomer()`, `fetchCustomerSites(customerId)`, `createCustomerSite()`
- `fetchRoles()`, `createRole()`, `fetchPermissions()`, `assignPermissionToRole()`, `removePermissionFromRole()`
- `fetchCameraGroups()`, `createCameraGroup()`, `addCameraToGroup()`, `removeCameraFromGroup()`
- `fetchAuditLogs(params)` — filterable by entity_type, entity_id, user_id, action
- `fetchCircles()`, `fetchBAs(circleId?)` — BSNL master data for dropdowns

---

### 2. `lib/auth.ts` — NEW permission helper utility

```ts
export const getPermissions = (): string[] =>
  JSON.parse(localStorage.getItem('permissions') ?? '[]')

export const getRoles = (): string[] =>
  JSON.parse(localStorage.getItem('roles') ?? '[]')

export const hasPermission = (perm: string): boolean =>
  getPermissions().includes(perm)

export const hasRole = (role: string): boolean =>
  getRoles().includes(role)
```

---

### 3. `pages/Login.tsx` — Store enriched JWT fields

On login success, store `roles` (JSON array), `permissions` (JSON array), `user_type` in localStorage alongside the existing `username` and `role` keys.

---

### 4. `components/ProtectedRoute.tsx` — Clear new localStorage keys

On token rejection, also clear `roles`, `permissions`, `user_type` keys.

---

### 5. `components/Sidebar.tsx` — Permission-aware nav

- Read `roles` and `permissions` from localStorage via `lib/auth.ts`
- Add new nav entries (conditionally shown):
  - **Organizations** — `system.settings` permission
  - **Customers** — all authenticated users
  - **Users** — `user.view` permission
  - **Roles** — `system.settings` permission
  - **Audit Log** — `system.audit` permission
  - **Camera Groups** — `camera.view` permission
- Show richer user info: `user_type` badge + actual role codes

---

### 6. `App.tsx` — Register new routes

Add 6 new routes inside `AppShell` wrapped in `ProtectedRoute`.

---

### 7. `pages/Organizations.tsx` — NEW

Tree view of org nodes:
- Indented tree by `parent_id`, color-coded type badges (ROOT/CIRCLE/BA/SSA/DISTRICT/SITE/NOC)
- "Add Node" form: `name`, `code`, `type` dropdown, `parent_id` dropdown, `circle_id`/`ba_id` BSNL dropdowns
- Subtree expand button per node (calls `/org/{id}/subtree`)
- Create/edit gated to `system.settings`

---

### 8. `pages/Customers.tsx` — NEW

Customer management with expandable sites:
- Table: name, code, type, org, circle/BA, contact, status
- "Add Customer" modal with all `CustomerCreate` fields
- Expandable row for Customer Sites (`GET /customers/{id}/sites`)
- "Add Site" sub-form per customer
- Create/edit gated to `customer.create`/`customer.update`

---

### 9. `pages/Users.tsx` — NEW

User management:
- Table: username, email, user_type, role chips, org/circle/BA, locked status
- "Add User" modal — full `UserCreate` fields with role multi-select
- Role assignment panel per user (assign/remove via `/users/{id}/roles`)
- Gated to `SUPER_ADMIN` role

---

### 10. `pages/Roles.tsx` — NEW

Roles & Permissions management:
- Left panel: roles list; click to see its permissions
- Right panel: all permissions grouped by prefix (`camera.*`, `user.*`, `system.*`, etc.)
- Toggle to assign/remove permission from role
- "Add Role" and "Add Permission" inline forms
- Gated to `system.settings`

---

### 11. `pages/AuditLog.tsx` — NEW

Read-only audit trail:
- Table: timestamp, username, action, entity_type, entity_id, IP
- Filters: action, entity_type
- Offset-based "Load more" pagination
- Gated to `system.audit`

---

### 12. `pages/CameraGroups.tsx` — NEW

Camera group management:
- Table of groups with camera count
- Expandable row showing assigned cameras (with remove)
- "Add Group" form, "Add Camera to Group" camera picker
- Gated to `camera.view` / `camera.update`

---

## Implementation Order

1. `lib/auth.ts`
2. `api/client.ts`
3. `pages/Login.tsx`
4. `components/ProtectedRoute.tsx`
5. `components/Sidebar.tsx`
6. `App.tsx`
7. `pages/Organizations.tsx`
8. `pages/Customers.tsx`
9. `pages/Users.tsx`
10. `pages/Roles.tsx`
11. `pages/AuditLog.tsx`
12. `pages/CameraGroups.tsx`

## Verification Plan

- Login stores `roles`/`permissions` correctly
- SUPER_ADMIN sees all nav items; VIEWER sees only Live View/Playback/Motion/Cameras/CameraGroups
- Org tree CRUD works end-to-end
- Customer creation with sites
- Role assignment reflected in user row
- Audit log shows LOGIN events
- Camera group creation and camera assignment

> [!NOTE]
> `Cameras.tsx` does not need changes in this phase. The `organization_id` / `customer_id` fields on camera creation can be wired in a follow-up.
