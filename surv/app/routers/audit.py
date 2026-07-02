"""
app/routers/audit.py
Read-only audit log endpoint. Requires system.audit permission.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies.auth import require_permission, CurrentUser
from app.models.rbac import AuditLog
from pydantic import BaseModel
from datetime import datetime

log = logging.getLogger(__name__)
router = APIRouter(prefix="/audit", tags=["audit"])


class AuditLogOut(BaseModel):
    id:          int
    user_id:     Optional[int]
    username:    Optional[str]
    action:      str
    entity_type: Optional[str]
    entity_id:   Optional[str]
    old_value:   Optional[dict]
    new_value:   Optional[dict]
    ip_address:  Optional[str]
    created_at:  datetime

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[AuditLogOut])
async def list_audit_logs(
    entity_type: Optional[str] = Query(None),
    entity_id:   Optional[str] = Query(None),
    user_id:     Optional[int] = Query(None),
    action:      Optional[str] = Query(None),
    limit:       int = Query(100, le=1000),
    offset:      int = Query(0),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("system.audit")),
):
    """
    Query audit logs. Filterable by entity_type, entity_id, user_id, action.
    Requires system.audit permission.
    """
    q = select(AuditLog).order_by(AuditLog.created_at.desc())
    if entity_type:
        q = q.where(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.where(AuditLog.entity_id == entity_id)
    if user_id:
        q = q.where(AuditLog.user_id == user_id)
    if action:
        q = q.where(AuditLog.action == action)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()
