#!/usr/bin/env python3
"""
scripts/seed_hierarchy.py
Idempotent seed script — safe to rerun.

Seeds (in order):
  1. BSNL organization tree (ROOT → sample Circles → sample BAs)
  2. All 14 standard roles
  3. All 16 standard permissions
  4. Default role-permission mappings
  5. Upgrades existing admin user: assigns SUPER_ADMIN role + user_type = EMPLOYEE

Usage (inside Docker app container):
  docker compose exec app python3 /code/scripts/seed_hierarchy.py

Or as a one-off container:
  docker compose run --rm -v ./scripts:/code/scripts app \
      python3 /code/scripts/seed_hierarchy.py
"""

import os
import sys
import logging

# Add /code to path so `from app.xxx import ...` works
sys.path.insert(0, "/code")

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("seed")

DATABASE_URL = os.environ.get(
    "SYNC_DATABASE_URL",
    os.environ.get("DATABASE_URL", "postgresql://surv:changeme@postgres:5432/sarvanetra"),
)

# Remove asyncpg prefix if present
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

engine = create_engine(DATABASE_URL, echo=False)


# ── Data definitions ──────────────────────────────────────────────────────────

ORG_TREE = [
    # (code, name, type, parent_code)
    ("BSNL_INDIA",     "BSNL India",        "ROOT",    None),
    ("CIRCLE_KL",      "Kerala Circle",     "CIRCLE",  "BSNL_INDIA"),
    ("CIRCLE_TN",      "Tamil Nadu Circle", "CIRCLE",  "BSNL_INDIA"),
    ("CIRCLE_KA",      "Karnataka Circle",  "CIRCLE",  "BSNL_INDIA"),
    ("BA_KL_TVM",      "Trivandrum BA",     "BA",      "CIRCLE_KL"),
    ("BA_KL_KLM",      "Kollam BA",         "BA",      "CIRCLE_KL"),
    ("BA_TN_CHN",      "Chennai BA",        "BA",      "CIRCLE_TN"),
    ("SSA_TVM_NEDUMANGAD", "Nedumangad SSA","SSA",     "BA_KL_TVM"),
    ("SSA_TVM_KAZHAKUTTAM","Kazhakuttam SSA","SSA",    "BA_KL_TVM"),
    ("NOC_BSNL_NATIONAL",  "National NOC",  "NOC",     "BSNL_INDIA"),
]

BSNL_MASTERS = {
    "CIRCLE_KL": {"name": "Kerala Circle", "bas": [("BA_KL_TVM", "Trivandrum BA"), ("BA_KL_KLM", "Kollam BA")]},
    "CIRCLE_TN": {"name": "Tamil Nadu Circle", "bas": [("BA_TN_CHN", "Chennai BA")]},
    "CIRCLE_KA": {"name": "Karnataka Circle", "bas": []},
}

ROLES = [
    ("SUPER_ADMIN",       "Super Administrator",      "Full system access"),
    ("NATIONAL_NOC",      "National NOC",             "Nationwide read + alert access"),
    ("CIRCLE_ADMIN",      "Circle Administrator",     "Manages a BSNL circle's cameras and users"),
    ("BA_ADMIN",          "BA Administrator",         "Manages a Business Area"),
    ("SSA_ADMIN",         "SSA Administrator",        "Manages a Secondary Switching Area"),
    ("SITE_ADMIN",        "Site Administrator",       "Manages a single site"),
    ("OPERATOR",          "Operator",                 "Live view and recordings"),
    ("VIEWER",            "Viewer",                   "Live view only"),
    ("CUSTOMER_ADMIN",    "Customer Administrator",   "Manages customer's own cameras/users"),
    ("CUSTOMER_OPERATOR", "Customer Operator",        "Customer live view and recordings"),
    ("CUSTOMER_VIEWER",   "Customer Viewer",          "Customer live view only"),
    ("PARTNER_ADMIN",     "Partner Administrator",    "Partner-level management"),
    ("PARTNER_ENGINEER",  "Partner Engineer",         "Installation and diagnostics"),
    ("AUDITOR",           "Auditor",                  "Audit log and report access only"),
]

PERMISSIONS = [
    # Camera
    ("camera.view",       "View camera list and details"),
    ("camera.create",     "Register new cameras"),
    ("camera.update",     "Modify camera settings"),
    ("camera.delete",     "Deactivate cameras"),
    ("camera.live",       "Access live stream"),
    ("camera.playback",   "Access recording playback timeline"),
    ("camera.download",   "Download recording segments"),
    # User
    ("user.create",       "Create new users"),
    ("user.update",       "Modify user accounts"),
    ("user.delete",       "Deactivate user accounts"),
    # Customer
    ("customer.create",   "Create customers"),
    ("customer.update",   "Modify customers and sites"),
    # Reports
    ("report.view",       "View reports and dashboards"),
    ("report.export",     "Export reports"),
    # System
    ("system.settings",   "Manage system settings, orgs, roles, permissions"),
    ("system.audit",      "Access audit log"),
]

# Role → list of permission codes it gets
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "SUPER_ADMIN": [p[0] for p in PERMISSIONS],   # All permissions

    "NATIONAL_NOC": [
        "camera.view", "camera.live", "camera.playback",
        "report.view", "system.audit",
    ],

    "CIRCLE_ADMIN": [
        "camera.view", "camera.create", "camera.update", "camera.delete",
        "camera.live", "camera.playback", "camera.download",
        "user.create", "user.update", "user.delete",
        "customer.create", "customer.update",
        "report.view", "report.export", "system.audit",
    ],

    "BA_ADMIN": [
        "camera.view", "camera.create", "camera.update", "camera.delete",
        "camera.live", "camera.playback", "camera.download",
        "user.create", "user.update",
        "customer.create", "customer.update",
        "report.view", "report.export",
    ],

    "SSA_ADMIN": [
        "camera.view", "camera.create", "camera.update",
        "camera.live", "camera.playback", "camera.download",
        "user.create", "user.update",
        "report.view",
    ],

    "SITE_ADMIN": [
        "camera.view", "camera.update",
        "camera.live", "camera.playback", "camera.download",
        "report.view",
    ],

    "OPERATOR": [
        "camera.view", "camera.live", "camera.playback", "camera.download",
        "report.view",
    ],

    "VIEWER": [
        "camera.view", "camera.live",
    ],

    "CUSTOMER_ADMIN": [
        "camera.view", "camera.update",
        "camera.live", "camera.playback", "camera.download",
        "user.create", "user.update",
        "report.view", "report.export",
    ],

    "CUSTOMER_OPERATOR": [
        "camera.view", "camera.live", "camera.playback", "camera.download",
    ],

    "CUSTOMER_VIEWER": [
        "camera.view", "camera.live",
    ],

    "PARTNER_ADMIN": [
        "camera.view", "camera.create", "camera.update",
        "user.create", "user.update",
        "customer.create", "customer.update",
        "report.view",
    ],

    "PARTNER_ENGINEER": [
        "camera.view", "camera.update", "camera.live",
    ],

    "AUDITOR": [
        "camera.view", "report.view", "report.export", "system.audit",
    ],
}


# ── Seeding logic ─────────────────────────────────────────────────────────────

def seed_bsnl_masters(session: Session) -> tuple[dict[str, int], dict[str, int]]:
    """Seed circle_master and ba_master."""
    from app.models.organization import CircleMaster, BAMaster
    circle_ids = {}
    ba_ids = {}

    for cir_code, data in BSNL_MASTERS.items():
        circle = session.execute(select(CircleMaster).where(CircleMaster.cir_code == cir_code)).scalar_one_or_none()
        if not circle:
            circle = CircleMaster(cir_code=cir_code, cir_name=data["name"])
            session.add(circle)
            session.flush()
            log.info(f"  CIRCLE MASTER created: {cir_code}")
        circle_ids[cir_code] = circle.id

        for ba_code, ba_name in data["bas"]:
            ba = session.execute(select(BAMaster).where(BAMaster.ba_code == ba_code)).scalar_one_or_none()
            if not ba:
                ba = BAMaster(ba_code=ba_code, ba_name=ba_name, circle_id=circle.id)
                session.add(ba)
                session.flush()
                log.info(f"  BA MASTER created: {ba_code}")
            ba_ids[ba_code] = ba.id
            
    return circle_ids, ba_ids

def seed_organizations(session: Session, circle_ids: dict[str, int], ba_ids: dict[str, int]) -> dict[str, int]:
    """
    Seed org tree and closure table. Returns {code: id} mapping.
    """
    from app.models.organization import Organization, OrganizationClosure

    code_to_id: dict[str, int] = {}

    for code, name, org_type, parent_code in ORG_TREE:
        existing = session.execute(
            select(Organization).where(Organization.code == code)
        ).scalar_one_or_none()

        if existing:
            code_to_id[code] = existing.id
            log.info(f"  ORG already exists: {code}")
            continue

        parent_id = code_to_id.get(parent_code) if parent_code else None
        
        # Link to BSNL masters if applicable
        circle_id = circle_ids.get(code) if org_type == "CIRCLE" else None
        ba_id = ba_ids.get(code) if org_type == "BA" else None
        
        org = Organization(code=code, name=name, type=org_type, parent_id=parent_id, circle_id=circle_id, ba_id=ba_id)
        session.add(org)
        session.flush()
        code_to_id[code] = org.id

        # Closure: self-reference
        session.add(OrganizationClosure(parent_id=org.id, child_id=org.id, depth=0))

        # Closure: inherit from parent's ancestors
        if parent_id:
            parent_rows = session.execute(
                select(OrganizationClosure)
                .where(OrganizationClosure.child_id == parent_id)
            ).scalars().all()
            for row in parent_rows:
                session.add(OrganizationClosure(
                    parent_id=row.parent_id,
                    child_id=org.id,
                    depth=row.depth + 1,
                ))

        log.info(f"  ORG created: {code} (id={org.id}, parent={parent_code})")

    session.flush()
    return code_to_id


def seed_roles(session: Session) -> dict[str, int]:
    """Seed roles. Returns {code: id}."""
    from app.models.rbac import Role

    code_to_id: dict[str, int] = {}
    for code, name, description in ROLES:
        existing = session.execute(
            select(Role).where(Role.code == code)
        ).scalar_one_or_none()

        if existing:
            code_to_id[code] = existing.id
            log.info(f"  ROLE already exists: {code}")
        else:
            role = Role(code=code, name=name, description=description)
            session.add(role)
            session.flush()
            code_to_id[code] = role.id
            log.info(f"  ROLE created: {code}")

    return code_to_id


def seed_permissions(session: Session) -> dict[str, int]:
    """Seed permissions. Returns {code: id}."""
    from app.models.rbac import Permission

    code_to_id: dict[str, int] = {}
    for code, description in PERMISSIONS:
        existing = session.execute(
            select(Permission).where(Permission.code == code)
        ).scalar_one_or_none()

        if existing:
            code_to_id[code] = existing.id
            log.info(f"  PERM already exists: {code}")
        else:
            perm = Permission(code=code, name=code, description=description)
            session.add(perm)
            session.flush()
            code_to_id[code] = perm.id
            log.info(f"  PERM created: {code}")

    return code_to_id


def seed_role_permissions(
    session: Session,
    role_ids: dict[str, int],
    perm_ids: dict[str, int],
) -> None:
    """Seed role-permission mappings (idempotent)."""
    from app.models.rbac import RolePermission

    for role_code, perm_codes in ROLE_PERMISSIONS.items():
        role_id = role_ids.get(role_code)
        if not role_id:
            continue
        for perm_code in perm_codes:
            perm_id = perm_ids.get(perm_code)
            if not perm_id:
                continue
            existing = session.execute(
                select(RolePermission)
                .where(RolePermission.role_id == role_id)
                .where(RolePermission.permission_id == perm_id)
            ).scalar_one_or_none()
            if not existing:
                session.add(RolePermission(role_id=role_id, permission_id=perm_id))

    session.flush()
    log.info("  Role-permission mappings seeded.")


def upgrade_admin_user(session: Session, role_ids: dict[str, int]) -> None:
    """
    Find existing admin user and:
      - set user_type = EMPLOYEE
      - assign SUPER_ADMIN role
    """
    from app.models.user import User
    from app.models.rbac import UserRole

    result = session.execute(
        select(User).where(User.role == "admin")
    ).scalars().all()

    for user in result:
        # Update user_type
        user.user_type = "EMPLOYEE"

        # Assign SUPER_ADMIN role
        super_admin_id = role_ids.get("SUPER_ADMIN")
        if super_admin_id:
            existing_role = session.execute(
                select(UserRole)
                .where(UserRole.user_id == user.id)
                .where(UserRole.role_id == super_admin_id)
            ).scalar_one_or_none()
            if not existing_role:
                session.add(UserRole(user_id=user.id, role_id=super_admin_id))
                log.info(f"  Assigned SUPER_ADMIN to user '{user.username}'")
            else:
                log.info(f"  User '{user.username}' already has SUPER_ADMIN")

    session.flush()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    # Import all models so SQLAlchemy mapper is populated
    import app.models  # noqa: F401

    with Session(engine) as session:
        log.info("=== Seeding BSNL Masters ===")
        circle_ids, ba_ids = seed_bsnl_masters(session)

        log.info("=== Seeding Organizations ===")
        org_ids = seed_organizations(session, circle_ids, ba_ids)

        log.info("=== Seeding Roles ===")
        role_ids = seed_roles(session)

        log.info("=== Seeding Permissions ===")
        perm_ids = seed_permissions(session)

        log.info("=== Seeding Role-Permission Mappings ===")
        seed_role_permissions(session, role_ids, perm_ids)

        log.info("=== Upgrading Admin User ===")
        upgrade_admin_user(session, role_ids)

        session.commit()
        log.info("=== Seed complete ✓ ===")


if __name__ == "__main__":
    main()
