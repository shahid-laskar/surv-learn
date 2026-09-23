"""
app/routers/incidents.py
FastAPI router for ICCC Incident Lifecycle Management.
Supports incident creation, status transition workflow (NEW -> ASSIGNED -> ESCALATED -> RESOLVED -> CLOSED),
and timeline history inspection.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, CurrentUser
from app.schemas.incident import (
    IncidentCreate,
    IncidentOut,
    IncidentTransitionIn,
)
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("/", response_model=List[IncidentOut])
async def list_incidents(
    status_filter: Optional[str] = Query(None, description="NEW | ASSIGNED | ESCALATED | RESOLVED | CLOSED"),
    severity: Optional[str] = Query(None, description="CRITICAL | HIGH | MEDIUM | LOW"),
    site_id: Optional[int] = Query(None, description="Filter by customer site ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """List operational incidents and their historical transition timelines."""
    items = await IncidentService.list_incidents(
        db, status_filter=status_filter, severity_filter=severity,
        site_id=site_id, limit=limit, offset=offset
    )
    return [IncidentOut.model_validate(inc) for inc in items]


@router.post("/", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
async def create_incident(
    payload: IncidentCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Log a new incident into the ICCC control room grid."""
    incident = await IncidentService.create_incident(db, payload, user_id=user.user_id)
    return IncidentOut.model_validate(incident)


@router.get("/{incident_id}", response_model=IncidentOut)
async def get_incident(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Get full incident details with complete audit timeline."""
    incident = await IncidentService.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return IncidentOut.model_validate(incident)


@router.post("/{incident_id}/transition", response_model=IncidentOut)
async def transition_incident_state(
    incident_id: int,
    payload: IncidentTransitionIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Advance or escalate an incident through the state machine:
    NEW -> ASSIGNED -> ESCALATED -> RESOLVED -> CLOSED.
    Records operator notes and timestamped audit trail.
    """
    incident = await IncidentService.transition_incident(
        db, incident_id=incident_id, transition=payload, user_id=user.user_id
    )
    return IncidentOut.model_validate(incident)
