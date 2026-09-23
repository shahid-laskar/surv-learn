"""
surv/app/tests/test_incidents.py
Unit tests for ICCC Incident Lifecycle Management:
State transitions, state machine validation, and timeline audit logging.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.models.incident import Incident, IncidentTimeline
from app.schemas.incident import IncidentCreate, IncidentTransitionIn
from app.services.incident_service import IncidentService


@pytest.mark.asyncio
async def test_create_incident_success():
    db = AsyncMock()
    db.add = MagicMock()

    payload = IncidentCreate(
        title="Unattended baggage at Nilakkal Ground 2",
        description="Suspicious black backpack found near ticket counter",
        severity="HIGH",
        source_type="manual",
        camera_id=3,
        customer_site_id=1,
    )

    inc = await IncidentService.create_incident(db, payload, user_id=10)

    assert inc.status == "NEW"
    assert inc.severity == "HIGH"
    assert inc.incident_number.startswith("INC-")
    assert inc.created_by_user_id == 10
    # Verified that both the incident and initial timeline entry were added
    assert db.add.call_count == 2
    assert db.commit.called


@pytest.mark.asyncio
async def test_transition_incident_success():
    db = AsyncMock()
    db.add = MagicMock()

    existing_inc = Incident(
        id=5,
        incident_number="INC-20260923-TEST",
        title="Stolen vehicle detected",
        status="NEW",
        severity="HIGH",
        timeline=[],
    )
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = existing_inc
    db.execute.return_value = mock_res

    transition = IncidentTransitionIn(
        to_status="ASSIGNED",
        notes="Dispatched Patrol Unit 4 to intercept",
    )

    updated = await IncidentService.transition_incident(db, 5, transition, user_id=42)

    assert updated.status == "ASSIGNED"
    assert db.add.called
    assert db.commit.called


@pytest.mark.asyncio
async def test_transition_incident_invalid_status():
    db = AsyncMock()
    existing_inc = Incident(id=5, status="NEW")
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = existing_inc
    db.execute.return_value = mock_res

    transition = IncidentTransitionIn(to_status="FLYING_DRONE")

    with pytest.raises(HTTPException) as exc:
        await IncidentService.transition_incident(db, 5, transition, user_id=42)
    assert exc.value.status_code == 400
    assert "Invalid incident status" in exc.value.detail


@pytest.mark.asyncio
async def test_transition_incident_illegal_reopen_closed_to_escalated():
    db = AsyncMock()
    # CLOSED can only transition to ASSIGNED (re-open)
    existing_inc = Incident(id=5, status="CLOSED")
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = existing_inc
    db.execute.return_value = mock_res

    transition = IncidentTransitionIn(to_status="ESCALATED")

    with pytest.raises(HTTPException) as exc:
        await IncidentService.transition_incident(db, 5, transition, user_id=42)
    assert exc.value.status_code == 400
    assert "Illegal transition from 'CLOSED' to 'ESCALATED'" in exc.value.detail
