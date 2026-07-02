"""
app/services/access_service.py
Camera access control logic.

Access is granted via UNION of three mechanisms:
  1. Role-scope: SUPER_ADMIN / NATIONAL_NOC → all cameras (no filter).
     Org-scoped roles (CIRCLE_ADMIN, BA_ADMIN, SSA_ADMIN, SITE_ADMIN) →
     cameras whose organization_id is in the user's org subtree
     (uses the organization_closure precomputed table for O(1) subtree check).
  2. Direct override: survapp_user_camera → explicit per-user camera grants
     (regardless of org scope).
  3. Camera group membership: user_group_mapping → camera_group_mapping →
     cameras in any group the user belongs to.

Returns a list of camera *primary key IDs* (survapp_camera_master.id).
Returning None means "no filter — all cameras accessible" (for super-users).
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies.auth import CurrentUser

# Roles that bypass all filtering
UNRESTRICTED_ROLES = {"SUPER_ADMIN", "NATIONAL_NOC"}

# Roles that are scoped to an org subtree
ORG_SCOPED_ROLES = {
    "CIRCLE_ADMIN", "BA_ADMIN", "SSA_ADMIN", "SITE_ADMIN",
    "OPERATOR", "VIEWER",
}


async def get_accessible_camera_ids(
    user: CurrentUser,
    db: AsyncSession,
) -> Optional[list[int]]:
    """
    Returns:
      None           → no filter (SUPER_ADMIN / NATIONAL_NOC / no roles set yet)
      list[int]      → explicit set of accessible camera primary key IDs
    """
    from app.models.camera import Camera
    from app.models.rbac import (
        UserCamera, CameraGroupMapping, UserGroupMapping,
    )
    from app.models.organization import OrganizationClosure

    user_roles = set(user.roles)

    # 1. Unrestricted access
    if user_roles & UNRESTRICTED_ROLES:
        return None

    accessible: set[int] = set()

    # 2. Org-subtree access
    if user.org_id and (user_roles & ORG_SCOPED_ROLES):
        # All org IDs in user's subtree (including their own)
        result = await db.execute(
            select(OrganizationClosure.child_id)
            .where(OrganizationClosure.parent_id == user.org_id)
        )
        subtree_org_ids = [r for (r,) in result.all()]

        if subtree_org_ids:
            result = await db.execute(
                select(Camera.id)
                .where(Camera.organization_id.in_(subtree_org_ids))
                .where(Camera.is_active == True)  # noqa: E712
            )
            accessible.update(r for (r,) in result.all())

    # 3. Direct user-camera grants
    result = await db.execute(
        select(UserCamera.camera_id)
        .where(UserCamera.user_id == user.user_id)
    )
    accessible.update(r for (r,) in result.all())

    # 4. Camera group membership
    result = await db.execute(
        select(CameraGroupMapping.camera_id)
        .join(UserGroupMapping, UserGroupMapping.group_id == CameraGroupMapping.group_id)
        .where(UserGroupMapping.user_id == user.user_id)
    )
    accessible.update(r for (r,) in result.all())

    # Legacy: if user has no roles (old admin/operator token) allow all
    if not user.roles:
        return None

    return list(accessible)
