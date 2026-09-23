"""
surv/app/tests/test_parking.py
Unit tests for Parking Management System:
Zone allocation, concurrency locking constraints, duplicate entry prevention,
entry slip generation, and exit fee calculation.
"""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.parking import ParkingSession, ParkingZone
from app.schemas.parking import (
    ParkingEntryRequest,
    ParkingExitRequest,
    ParkingZoneCreate,
    ParkingZoneUpdate,
)
from app.services.parking_service import ParkingAllocationService, normalize_plate


def test_normalize_plate():
    assert normalize_plate("kl-07-bh-9999") == "KL07BH9999"
    assert normalize_plate(" KL 01 AB 1234 ") == "KL01AB1234"
    assert normalize_plate("dl.3c.aa.1111") == "DL3CAA1111"
    assert normalize_plate("") == ""


@pytest.mark.asyncio
async def test_get_occupancy_summary():
    db = AsyncMock()
    z1 = ParkingZone(
        id=1, customer_site_id=1, zone_code="G01", name="Ground 1",
        vehicle_type="LMV", total_capacity=100, current_occupancy=40,
        is_active=True, display_order=1, created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    z2 = ParkingZone(
        id=2, customer_site_id=1, zone_code="G02", name="Ground 2",
        vehicle_type="BUS", total_capacity=50, current_occupancy=50,
        is_active=True, display_order=2, created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [z1, z2]
    db.execute.return_value = mock_result

    summary = await ParkingAllocationService.get_occupancy_summary(db, customer_site_id=1)
    assert summary.total_zones == 2
    assert summary.total_capacity == 150
    assert summary.total_occupied == 90
    assert summary.total_available == 60
    assert summary.overall_occupancy_pct == 60.0
    assert len(summary.zones) == 2


@pytest.mark.asyncio
async def test_create_zone_duplicate_code():
    db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = ParkingZone(id=1, zone_code="G01")
    db.execute.return_value = mock_res

    req = ParkingZoneCreate(zone_code="G01", name="Ground 1", total_capacity=100)
    with pytest.raises(HTTPException) as exc:
        await ParkingAllocationService.create_zone(db, req)
    assert exc.value.status_code == 409
    assert "already exists" in exc.value.detail


@pytest.mark.asyncio
async def test_update_zone_capacity_below_occupancy():
    db = AsyncMock()
    existing = ParkingZone(id=1, zone_code="G01", total_capacity=100, current_occupancy=75)
    db.get.return_value = existing

    req = ParkingZoneUpdate(total_capacity=50)
    with pytest.raises(HTTPException) as exc:
        await ParkingAllocationService.update_zone(db, 1, req)
    assert exc.value.status_code == 400
    assert "Total capacity cannot be less than current occupancy" in exc.value.detail


@pytest.mark.asyncio
async def test_allocate_and_enter_duplicate_active_vehicle():
    db = AsyncMock()
    mock_dup = MagicMock()
    mock_dup.scalar_one_or_none.return_value = ParkingSession(
        id=10, normalized_plate="KL01AB1234", status="ACTIVE", entry_slip_number="SLIP-123"
    )
    db.execute.return_value = mock_dup

    req = ParkingEntryRequest(vehicle_number="KL-01-AB-1234", vehicle_type="LMV")
    with pytest.raises(HTTPException) as exc:
        await ParkingAllocationService.allocate_and_enter(db, req)
    assert exc.value.status_code == 409
    assert "already has an ACTIVE parking session" in exc.value.detail


@pytest.mark.asyncio
async def test_allocate_and_enter_preferred_zone_full():
    db = AsyncMock()
    # 1st execute for duplicate check returns None
    # 2nd execute for preferred zone returns a full zone
    mock_dup = MagicMock()
    mock_dup.scalar_one_or_none.return_value = None

    mock_zone = MagicMock()
    full_zone = ParkingZone(id=5, zone_code="G05", total_capacity=20, current_occupancy=20, is_active=True)
    mock_zone.scalar_one_or_none.return_value = full_zone

    db.execute.side_effect = [mock_dup, mock_zone]

    req = ParkingEntryRequest(vehicle_number="KL07BH1234", preferred_zone_id=5)
    with pytest.raises(HTTPException) as exc:
        await ParkingAllocationService.allocate_and_enter(db, req)
    assert exc.value.status_code == 409
    assert "currently full" in exc.value.detail


@pytest.mark.asyncio
async def test_allocate_and_enter_success():
    db = AsyncMock()
    db.add = MagicMock()
    mock_dup = MagicMock()
    mock_dup.scalar_one_or_none.return_value = None

    available_zone = ParkingZone(
        id=1, customer_site_id=1, zone_code="G01", name="Ground 1",
        vehicle_type="LMV", total_capacity=50, current_occupancy=10, is_active=True
    )
    mock_zones = MagicMock()
    mock_zones.scalars.return_value.all.return_value = [available_zone]

    db.execute.side_effect = [mock_dup, mock_zones]

    req = ParkingEntryRequest(vehicle_number="kl-01-ab-9999", customer_site_id=1, vehicle_type="LMV")
    session = await ParkingAllocationService.allocate_and_enter(db, req)

    assert session.status == "ACTIVE"
    assert session.normalized_plate == "KL01AB9999"
    assert session.parking_zone_id == 1
    assert available_zone.current_occupancy == 11
    assert session.entry_slip_number.startswith("SLIP-")
    assert db.commit.called


@pytest.mark.asyncio
async def test_process_exit_success():
    db = AsyncMock()
    entry_t = datetime.now(timezone.utc) - timedelta(hours=2, minutes=15)
    zone = ParkingZone(id=1, zone_code="G01", total_capacity=50, current_occupancy=15)
    session = ParkingSession(
        id=101, entry_slip_number="SLIP-TEST-001", vehicle_number="KL01AB9999",
        normalized_plate="KL01AB9999", vehicle_type="LMV", entry_time=entry_t,
        parking_zone_id=1, status="ACTIVE", zone=zone
    )

    mock_sess_res = MagicMock()
    mock_sess_res.scalar_one_or_none.return_value = session

    mock_zone_res = MagicMock()
    mock_zone_res.scalar_one_or_none.return_value = zone

    db.execute.side_effect = [mock_sess_res, mock_zone_res]

    req = ParkingExitRequest(entry_slip_number="SLIP-TEST-001")
    completed = await ParkingAllocationService.process_exit(db, req)

    assert completed.status == "COMPLETED"
    assert completed.exit_time is not None
    assert zone.current_occupancy == 14
    # 2h 15m = 3 billing hours -> LMV base 50 + (3-1)*25 = 100.0
    assert completed.fee_amount == 100.0


@pytest.mark.asyncio
async def test_process_exit_not_found():
    db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_res

    req = ParkingExitRequest(entry_slip_number="SLIP-NONEXISTENT")
    with pytest.raises(HTTPException) as exc:
        await ParkingAllocationService.process_exit(db, req)
    assert exc.value.status_code == 404
    assert "Active parking session not found" in exc.value.detail
