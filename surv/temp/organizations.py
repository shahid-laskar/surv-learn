"""
app/routers/organizations.py
CRUD for the organization tree + organization_closure maintenance.

Closure table strategy:
  On creation of a new org node, we insert closure rows so that
  every ancestor of the new node has a (ancestor_id, new_id, depth) row.
  This enables fast subtree queries: SELECT child_id FROM organization_closure
  WHERE parent_id = ? — returns all descendants.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timezone

from app.database import get_db
from app.dependencies.auth import get_current_user, require_permission, CurrentUser
from app.models.organization import Organization, OrganizationClosure
from app.schemas.organization import OrganizationCreate, OrganizationUpdate, OrganizationOut, OrganizationTree

log = logging.getLogger(__name__)
router = APIRouter(prefix="/org", tags=["organizations"])


async def _insert_closure_rows(db: AsyncSession, new_id: int, parent_id: int | None) -> None:
    """
    Insert organization_closure rows for the newly created org node.
    Each node always has a self-reference (depth=0).
    If parent_id is set, inherits all ancestor rows from the parent.
    """
    # Self-reference
    db.add(OrganizationClosure(parent_id=new_id, child_id=new_id, depth=0))

    if parent_id is not None:
        # Copy all of parent's ancestor rows with depth+1
        result = await db.execute(
            select(OrganizationClosure)
            .where(OrganizationClosure.child_id == parent_id)
        )
        for row in result.scalars().all():
            db.add(OrganizationClosure(
                parent_id=row.parent_id,
                child_id=new_id,
                depth=row.depth + 1,
            ))


@router.get("/", response_model=list[OrganizationOut])
async def list_orgs(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """List all organization nodes the caller can see."""
    result = await db.execute(select(Organization).order_by(Organization.id))
    return result.scalars().all()


@router.post("/", response_model=OrganizationOut, status_code=201)
async def create_org(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("system.settings")),
):
    """Create a new organization node. Requires system.settings permission."""
    if payload.parent_id:
        parent = await db.get(Organization, payload.parent_id)
        if not parent:
            raise HTTPException(404, f"Parent organization {payload.parent_id} not found")

    org = Organization(
        parent_id=payload.parent_id,
        code=payload.code,
        name=payload.name,
        type=payload.type,
    )
    db.add(org)
    await db.flush()   # get org.id assigned

    await _insert_closure_rows(db, org.id, payload.parent_id)
    await db.commit()
    await db.refresh(org)
    log.info(f"Organization created: {org.code} (id={org.id})")
    return org


@router.get("/{org_id}", response_model=OrganizationOut)
async def get_org(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(404, "Organization not found")
    return org


@router.get("/{org_id}/subtree", response_model=list[OrganizationOut])
async def get_subtree(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Return all descendants of an org node (using closure table)."""
    result = await db.execute(
        select(Organization)
        .join(OrganizationClosure, OrganizationClosure.child_id == Organization.id)
        .where(OrganizationClosure.parent_id == org_id)
        .order_by(OrganizationClosure.depth)
    )
    return result.scalars().all()


@router.patch("/{org_id}", response_model=OrganizationOut)
async def update_org(
    org_id: int,
    payload: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("system.settings")),
):
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(404, "Organization not found")
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(org, k, v)
    org.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(org)
    return org
