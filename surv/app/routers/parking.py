"""
app/routers/parking.py
FastAPI router for Parking Management System (PMS):
Zones, live occupancy, transactional vehicle allocation, entry slip issuance, and exit fee calculation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, CurrentUser
from app.schemas.parking import (
    ParkingEntryRequest,
    ParkingExitRequest,
    ParkingOccupancySummary,
    ParkingSlipOut,
    ParkingZoneCreate,
    ParkingZoneOut,
    ParkingZoneUpdate,
)
from app.services.parking_service import ParkingAllocationService

router = APIRouter(prefix="/parking", tags=["parking"])


@router.get("/zones", response_model=List[ParkingZoneOut])
async def list_parking_zones(
    site_id: Optional[int] = Query(None, description="Filter by customer site ID"),
    active_only: bool = Query(True, description="Filter active zones only"),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """List all configured parking zones with live capacity and occupancy metrics."""
    zones = await ParkingAllocationService.get_zones(
        db, customer_site_id=site_id, active_only=active_only
    )
    return [ParkingZoneOut.model_validate(z) for z in zones]


@router.post("/zones", response_model=ParkingZoneOut, status_code=status.HTTP_201_CREATED)
async def create_parking_zone(
    payload: ParkingZoneCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Create a new parking zone / ground."""
    zone = await ParkingAllocationService.create_zone(db, payload)
    return ParkingZoneOut.model_validate(zone)


@router.patch("/zones/{zone_id}", response_model=ParkingZoneOut)
async def update_parking_zone(
    zone_id: int,
    payload: ParkingZoneUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Update parking zone configuration, capacity, or display order."""
    zone = await ParkingAllocationService.update_zone(db, zone_id, payload)
    return ParkingZoneOut.model_validate(zone)


@router.get("/occupancy", response_model=ParkingOccupancySummary)
async def get_parking_occupancy(
    site_id: Optional[int] = Query(None, description="Customer site ID"),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Real-time parking occupancy roll-up across all grounds for the Common Operating Picture."""
    return await ParkingAllocationService.get_occupancy_summary(db, customer_site_id=site_id)


@router.post("/entry", response_model=ParkingSlipOut, status_code=status.HTTP_201_CREATED)
async def vehicle_entry(
    payload: ParkingEntryRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Allocates an open parking zone for an arriving vehicle, increments zone occupancy,
    and returns an official parking entry slip.
    Uses database row-level locking (SELECT ... FOR UPDATE) to prevent over-allocation.
    """
    session = await ParkingAllocationService.allocate_and_enter(db, payload)
    return ParkingAllocationService.session_to_slip_out(session)


@router.post("/entry-slip", response_model=ParkingSlipOut, status_code=status.HTTP_201_CREATED)
async def issue_entry_slip(
    payload: ParkingEntryRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Alias for /entry to issue an official thermal POS print slip payload."""
    session = await ParkingAllocationService.allocate_and_enter(db, payload)
    return ParkingAllocationService.session_to_slip_out(session)


@router.post("/exit", response_model=ParkingSlipOut)
async def vehicle_exit(
    payload: ParkingExitRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Processes vehicle exit by entry slip or plate number.
    Calculates duration, determines parking fee, decrements zone occupancy, and closes session.
    """
    session = await ParkingAllocationService.process_exit(db, payload)
    return ParkingAllocationService.session_to_slip_out(session)
