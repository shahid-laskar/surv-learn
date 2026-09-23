"""
app/services/incident_service.py
ICCC Incident Lifecycle Management Service.
Enforces the operational state machine (NEW -> ASSIGNED -> ESCALATED -> RESOLVED -> CLOSED)
with immutable timeline auditing and trigger links from ANPR, motion, and camera alerts.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.incident import Incident, IncidentTimeline
from app.schemas.incident import (
    IncidentCreate,
    IncidentOut,
    IncidentTimelineOut,
    IncidentTransitionIn,
    IncidentUpdate,
)

VALID_STATUSES = {"NEW", "ASSIGNED", "ESCALATED", "RESOLVED", "CLOSED"}

ALLOWED_TRANSITIONS = {
    "NEW": {"ASSIGNED", "ESCALATED", "RESOLVED", "CLOSED"},
    "ASSIGNED": {"ESCALATED", "RESOLVED", "CLOSED"},
    "ESCALATED": {"ASSIGNED", "RESOLVED", "CLOSED"},
    "RESOLVED": {"CLOSED", "ASSIGNED"},
    "CLOSED": {"ASSIGNED"},
}


class IncidentService:
    @staticmethod
    async def create_incident(
        db: AsyncSession,
        data: IncidentCreate,
        user_id: Optional[int] = None,
    ) -> Incident:
        now = datetime.now(timezone.utc)
        unique_id = uuid.uuid4().hex[:6].upper()
        inc_number = f"INC-{now.strftime('%Y%m%d%H%M')}-{unique_id}"

        incident = Incident(
            incident_number=inc_number,
            title=data.title.strip(),
            description=data.description.strip() if data.description else None,
            status="NEW",
            severity=data.severity.upper(),
            source_type=data.source_type.lower(),
            source_id=data.source_id,
            camera_id=data.camera_id,
            customer_site_id=data.customer_site_id,
            assigned_to_user_id=data.assigned_to_user_id,
            created_by_user_id=user_id,
            created_at=now,
            updated_at=now,
        )
        db.add(incident)
        await db.flush()
        await db.refresh(incident)

        # Record initial timeline audit entry
        initial_log = IncidentTimeline(
            incident_id=incident.id,
            from_status=None,
            to_status="NEW",
            changed_by_user_id=user_id,
            notes="Incident logged into ICCC control grid",
            created_at=now,
        )
        db.add(initial_log)

        await db.commit()
        await db.refresh(incident)
        return incident

    @staticmethod
    async def transition_incident(
        db: AsyncSession,
        incident_id: int,
        transition: IncidentTransitionIn,
        user_id: Optional[int] = None,
    ) -> Incident:
        stmt = (
            select(Incident)
            .options(selectinload(Incident.timeline))
            .where(Incident.id == incident_id)
        )
        res = await db.execute(stmt)
        incident = res.scalar_one_or_none()
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

        current_status = incident.status
        next_status = transition.to_status.upper()

        if next_status not in VALID_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid incident status '{next_status}'. Must be one of {sorted(VALID_STATUSES)}",
            )

        if next_status == current_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Incident is already in status '{current_status}'",
            )

        allowed = ALLOWED_TRANSITIONS.get(current_status, set())
        if next_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Illegal transition from '{current_status}' to '{next_status}'. Allowed: {sorted(allowed)}",
            )

        now = datetime.now(timezone.utc)
        incident.status = next_status
        incident.updated_at = now

        # Add timeline entry
        log_entry = IncidentTimeline(
            incident_id=incident.id,
            from_status=current_status,
            to_status=next_status,
            changed_by_user_id=user_id,
            notes=transition.notes.strip() if transition.notes else None,
            created_at=now,
        )
        db.add(log_entry)

        await db.commit()
        await db.refresh(incident)
        return incident

    @staticmethod
    async def get_incident(db: AsyncSession, incident_id: int) -> Optional[Incident]:
        stmt = (
            select(Incident)
            .options(selectinload(Incident.timeline))
            .where(Incident.id == incident_id)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_incidents(
        db: AsyncSession,
        status_filter: Optional[str] = None,
        severity_filter: Optional[str] = None,
        site_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Incident]:
        stmt = (
            select(Incident)
            .options(selectinload(Incident.timeline))
            .order_by(Incident.created_at.desc())
        )
        if status_filter:
            stmt = stmt.where(Incident.status == status_filter.upper())
        if severity_filter:
            stmt = stmt.where(Incident.severity == severity_filter.upper())
        if site_id is not None:
            stmt = stmt.where(Incident.customer_site_id == site_id)

        stmt = stmt.offset(offset).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())
