# Sarvanetra Commercial Architecture Model (Pan-India Deployment)

## Goals

- BSNL hierarchy support
- Enterprise and retail customers
- Multi-tenancy
- Fine-grained RBAC
- Camera sharing and grouping
- Audit and compliance
- Scalable to 50,000+ users and 100,000+ cameras

---

# 1. Organization Hierarchy

```sql
CREATE TABLE organization (
    id BIGSERIAL PRIMARY KEY,
    parent_id BIGINT REFERENCES organization(id),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

Types:

- ROOT
- CIRCLE
- BA
- SSA
- DISTRICT
- SITE
- NOC

Example:

```text
BSNL INDIA
 ├── Kerala Circle
 │     ├── Trivandrum BA
 │     │      ├── Nedumangad Site
 │     │      └── Kazhakuttam Site
 │     └── Kollam BA
 └── Tamil Nadu Circle
```

---

# 2. Organization Closure Table

```sql
CREATE TABLE organization_closure (
    parent_id BIGINT NOT NULL,
    child_id BIGINT NOT NULL,
    depth INTEGER NOT NULL,
    PRIMARY KEY (parent_id, child_id)
);
```

---

# 3. Customer

```sql
CREATE TABLE customer (
    id BIGSERIAL PRIMARY KEY,
    parent_customer_id BIGINT REFERENCES customer(id),
    customer_code VARCHAR(100) UNIQUE,
    name VARCHAR(200) NOT NULL,
    customer_type VARCHAR(50),
    organization_id BIGINT REFERENCES organization(id),
    email VARCHAR(255),
    phone VARCHAR(30),
    address TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

Customer types:

- ENTERPRISE
- BANK
- SCHOOL
- HOSPITAL
- APARTMENT
- GOVERNMENT
- INDIVIDUAL
- PARTNER

---

# 4. Customer Site

```sql
CREATE TABLE customer_site (
    id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customer(id),
    site_code VARCHAR(100),
    name VARCHAR(200),
    state VARCHAR(100),
    district VARCHAR(100),
    city VARCHAR(100),
    address TEXT,
    latitude NUMERIC(10,7),
    longitude NUMERIC(10,7),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

# 5. Users

```sql
CREATE TABLE survapp_user (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    mobile VARCHAR(20),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    password_hash TEXT NOT NULL,
    user_type VARCHAR(30) NOT NULL,
    organization_id BIGINT REFERENCES organization(id),
    customer_id BIGINT REFERENCES customer(id),
    is_active BOOLEAN DEFAULT TRUE,
    is_locked BOOLEAN DEFAULT FALSE,
    failed_login_count INTEGER DEFAULT 0,
    last_login TIMESTAMPTZ,
    last_password_change TIMESTAMPTZ,
    created_by BIGINT,
    updated_by BIGINT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

User types:

- EMPLOYEE
- CUSTOMER
- PARTNER
- SYSTEM

---

# 6. Roles

```sql
CREATE TABLE survapp_role (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(100) UNIQUE,
    name VARCHAR(100),
    description TEXT
);
```

Recommended roles:

- SUPER_ADMIN
- NATIONAL_NOC
- CIRCLE_ADMIN
- BA_ADMIN
- SSA_ADMIN
- SITE_ADMIN
- OPERATOR
- VIEWER
- CUSTOMER_ADMIN
- CUSTOMER_OPERATOR
- CUSTOMER_VIEWER
- PARTNER_ADMIN
- PARTNER_ENGINEER
- AUDITOR

---

# 7. Permissions

```sql
CREATE TABLE survapp_permission (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(100) UNIQUE,
    name VARCHAR(200),
    description TEXT
);
```

Examples:

- camera.view
- camera.create
- camera.update
- camera.delete
- camera.live
- camera.playback
- camera.download
- user.create
- user.update
- user.delete
- customer.create
- customer.update
- report.view
- report.export
- system.settings
- system.audit

---

# 8. Role Permission Mapping

```sql
CREATE TABLE survapp_role_permission (
    role_id BIGINT REFERENCES survapp_role(id),
    permission_id BIGINT REFERENCES survapp_permission(id),
    PRIMARY KEY(role_id, permission_id)
);
```

---

# 9. User Role Mapping

```sql
CREATE TABLE survapp_user_role (
    user_id BIGINT REFERENCES survapp_user(id),
    role_id BIGINT REFERENCES survapp_role(id),
    PRIMARY KEY(user_id, role_id)
);
```

---

# 10. Camera Master

```sql
CREATE TABLE survapp_camera_master (
    id BIGSERIAL PRIMARY KEY,
    cam_id VARCHAR(100) UNIQUE,
    cam_name VARCHAR(200),
    customer_id BIGINT REFERENCES customer(id),
    customer_site_id BIGINT REFERENCES customer_site(id),
    organization_id BIGINT REFERENCES organization(id),
    cam_ip VARCHAR(100),
    cam_port INTEGER,
    rtsp_url TEXT,
    onvif_username VARCHAR(100),
    onvif_password TEXT,
    camera_model VARCHAR(100),
    manufacturer VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_online BOOLEAN DEFAULT FALSE,
    motion_active BOOLEAN DEFAULT TRUE,
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

# 11. User Camera Override

```sql
CREATE TABLE survapp_user_camera (
    user_id BIGINT REFERENCES survapp_user(id),
    camera_id BIGINT REFERENCES survapp_camera_master(id),
    PRIMARY KEY(user_id, camera_id)
);
```

---

# 12. Camera Groups

```sql
CREATE TABLE camera_group (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200),
    organization_id BIGINT,
    customer_id BIGINT
);
```

```sql
CREATE TABLE camera_group_mapping (
    group_id BIGINT,
    camera_id BIGINT,
    PRIMARY KEY(group_id, camera_id)
);
```

```sql
CREATE TABLE user_group_mapping (
    user_id BIGINT,
    group_id BIGINT,
    PRIMARY KEY(user_id, group_id)
);
```

---

# 13. User Sessions

```sql
CREATE TABLE user_session (
    id UUID PRIMARY KEY,
    user_id BIGINT REFERENCES survapp_user(id),
    refresh_token_hash TEXT,
    device_name VARCHAR(200),
    device_type VARCHAR(100),
    ip_address VARCHAR(100),
    created_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE
);
```

---

# 14. Device Tokens

```sql
CREATE TABLE device_token (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES survapp_user(id),
    platform VARCHAR(20),
    token TEXT,
    created_at TIMESTAMPTZ
);
```

---

# 15. Audit Logs

```sql
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    username VARCHAR(100),
    action VARCHAR(100),
    entity_type VARCHAR(100),
    entity_id VARCHAR(100),
    old_value JSONB,
    new_value JSONB,
    ip_address VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

# 16. Notifications

```sql
CREATE TABLE notification (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    title VARCHAR(500),
    message TEXT,
    payload JSONB,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

# 17. Password Reset

```sql
CREATE TABLE password_reset_token (
    id UUID PRIMARY KEY,
    user_id BIGINT,
    token_hash TEXT,
    expires_at TIMESTAMPTZ,
    used BOOLEAN DEFAULT FALSE
);
```

---

# JWT Structure

```json
{
  "sub": 125,
  "user_type": "EMPLOYEE",
  "org_id": 20,
  "customer_id": null,
  "roles": ["SSA_ADMIN"],
  "permissions": [
    "camera.view",
    "camera.live",
    "user.create"
  ],
  "session_id": "uuid",
  "iss": "sarvanetra-app",
  "exp": 1783011111
}
```

---

# Kong Architecture

Consumers:

- sarvanetra-app
- mobile-app
- external-api (optional)

Do not create one Kong consumer per user.

---

# Final Hierarchy

```text
Organization
     ↓
Customer
     ↓
Customer Site
     ↓
Camera Group
     ↓
Camera
     ↓
User
     ↓
Roles
     ↓
Permissions
```


---

# Architecture Update: Preserve BSNL Masters

To maintain compatibility with the earlier BSNL system and simplify reporting and migration, the following master tables should be retained.

# 0. Circle Master

```sql
CREATE TABLE circle_master (
    id BIGSERIAL PRIMARY KEY,
    cir_code VARCHAR(50) UNIQUE NOT NULL,
    cir_name VARCHAR(200) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

# 0.1 BA Master

```sql
CREATE TABLE ba_master (
    id BIGSERIAL PRIMARY KEY,
    ba_code VARCHAR(50) NOT NULL,
    ba_name VARCHAR(200) NOT NULL,
    circle_id BIGINT NOT NULL REFERENCES circle_master(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

These tables remain the source of truth for BSNL operational hierarchy and reporting.

Example:

```text
Kerala Circle
 ├── Trivandrum BA
 ├── Kollam BA
 └── Ernakulam BA
```

They are not replaced by `organization`; instead, they complement it.

# Updated Hierarchy

```text
circle_master
      ↓
ba_master
      ↓
organization
      ↓
customer
      ↓
customer_site
      ↓
camera_group
      ↓
camera
      ↓
users / roles / permissions
```

# Recommended References

The following entities should carry optional references to these master tables:

## organization

```text
organization
------------
id
parent_id
org_type
circle_id
ba_id
```

## customer

```text
customer
--------
id
organization_id
circle_id
ba_id
```

## survapp_user

```text
survapp_user
------------
id
organization_id
circle_id
ba_id
customer_id
```

## survapp_camera_master

```text
survapp_camera_master
---------------------
id
organization_id
circle_id
ba_id
customer_id
customer_site_id
```

# Camera ID Strategy

Retain the existing BSNL-style camera identifier generation.

Example:

```text
CAMKRTVM00001
CAMKRTVM00002
CAMKREKM00001
```

Pattern:

```text
CAM + CircleCode + BACode + Sequence
```

This is significantly easier for operations, support teams, and reporting than UUID-based identifiers.

# Final Recommendation

Keep:

- circle_master
- ba_master

Add:

- organization
- organization_closure
- customer
- customer_site
- full RBAC and audit architecture

This provides:

- Easy migration from the old BSNL application
- Familiar reporting for operations teams
- Support for future hierarchy expansion
- Pan-India scalability
- Compatibility with commercial multi-tenant deployments
