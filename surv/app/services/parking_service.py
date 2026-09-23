"""
app/services/parking_service.py
Core Parking Allocation and Lifecycle Management Service.
Handles concurrent zone allocation with row-level database locking (SELECT ... FOR UPDATE),
duplicate vehicle prevention, slip generation, and exit fee calculation.
"""

import math
import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.parking import ParkingLane, ParkingSession, ParkingZone
from app.schemas.parking import (
    ParkingEntryRequest,
    ParkingExitRequest,
    ParkingOccupancySummary,
    ParkingSlipOut,
    ParkingZoneCreate,
    ParkingZoneOut,
    ParkingZoneUpdate,
)


def normalize_plate(plate: str) -> str:
    """
    Strips whitespace, hyphens, and symbols; converts to uppercase alphanumeric.
    Example: 'kl-07 bh-9999' -> 'KL07BH9999'
    """
    if not plate:
        return ""
    return re.sub(r"[^A-Z0-9]", "", plate.upper())


class ParkingAllocationService:
    @staticmethod
    async def get_zones(
        db: AsyncSession,
        customer_site_id: Optional[int] = None,
        active_only: bool = True,
    ) -> List[ParkingZone]:
        stmt = select(ParkingZone).order_by(ParkingZone.display_order, ParkingZone.zone_code)
        if customer_site_id is not None:
            stmt = stmt.where(ParkingZone.customer_site_id == customer_site_id)
        if active_only:
            stmt = stmt.where(ParkingZone.is_active == True)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_zone_by_id(db: AsyncSession, zone_id: int) -> Optional[ParkingZone]:
        return await db.get(ParkingZone, zone_id)

    @staticmethod
    async def get_occupancy_summary(
        db: AsyncSession,
        customer_site_id: Optional[int] = None,
    ) -> ParkingOccupancySummary:
        zones = await ParkingAllocationService.get_zones(
            db, customer_site_id=customer_site_id, active_only=True
        )
        total_capacity = sum(z.total_capacity for z in zones)
        total_occupied = sum(z.current_occupancy for z in zones)
        total_available = max(0, total_capacity - total_occupied)
        overall_pct = (
            round((total_occupied / total_capacity) * 100.0, 1) if total_capacity > 0 else 100.0
        )

        zone_outs = [ParkingZoneOut.model_validate(z) for z in zones]
        return ParkingOccupancySummary(
            total_zones=len(zones),
            total_capacity=total_capacity,
            total_occupied=total_occupied,
            total_available=total_available,
            overall_occupancy_pct=overall_pct,
            zones=zone_outs,
        )

    @staticmethod
    async def create_zone(db: AsyncSession, data: ParkingZoneCreate) -> ParkingZone:
        # Check duplicate zone code within site
        existing_stmt = select(ParkingZone).where(
            ParkingZone.zone_code == data.zone_code,
            ParkingZone.customer_site_id == data.customer_site_id,
        )
        res = await db.execute(existing_stmt)
        if res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Parking zone code '{data.zone_code}' already exists for this site",
            )

        zone = ParkingZone(
            zone_code=data.zone_code.strip().upper(),
            name=data.name.strip(),
            customer_site_id=data.customer_site_id,
            vehicle_type=data.vehicle_type.upper(),
            total_capacity=data.total_capacity,
            current_occupancy=0,
            display_order=data.display_order,
            is_active=True,
        )
        db.add(zone)
        await db.commit()
        await db.refresh(zone)
        return zone

    @staticmethod
    async def update_zone(
        db: AsyncSession,
        zone_id: int,
        data: ParkingZoneUpdate,
    ) -> ParkingZone:
        zone = await db.get(ParkingZone, zone_id)
        if not zone:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")

        if data.name is not None:
            zone.name = data.name.strip()
        if data.vehicle_type is not None:
            zone.vehicle_type = data.vehicle_type.upper()
        if data.total_capacity is not None:
            if data.total_capacity < zone.current_occupancy:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Total capacity cannot be less than current occupancy",
                )
            zone.total_capacity = data.total_capacity
        if data.current_occupancy is not None:
            if data.current_occupancy > zone.total_capacity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current occupancy cannot exceed total capacity",
                )
            zone.current_occupancy = data.current_occupancy
        if data.is_active is not None:
            zone.is_active = data.is_active
        if data.display_order is not None:
            zone.display_order = data.display_order

        await db.commit()
        await db.refresh(zone)
        return zone

    @staticmethod
    async def allocate_and_enter(
        db: AsyncSession,
        request: ParkingEntryRequest,
    ) -> ParkingSession:
        """
        Transactional vehicle entry allocation:
        1. Plate normalization
        2. Duplicate active session check
        3. Row-level locked zone selection (FOR UPDATE)
        4. Occupancy increment (never exceeding capacity)
        5. Unique slip generation
        """
        norm_plate = normalize_plate(request.vehicle_number)
        if not norm_plate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valid vehicle number is required",
            )

        # 1. Prevent duplicate active session
        dup_stmt = select(ParkingSession).where(
            ParkingSession.normalized_plate == norm_plate,
            ParkingSession.status == "ACTIVE",
        )
        if request.customer_site_id is not None:
            dup_stmt = dup_stmt.where(ParkingSession.customer_site_id == request.customer_site_id)
        
        dup_res = await db.execute(dup_stmt)
        existing_session = dup_res.scalar_one_or_none()
        if existing_session:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Vehicle '{norm_plate}' already has an ACTIVE parking session (Slip: {existing_session.entry_slip_number})",
            )

        # 2. Zone selection with FOR UPDATE row lock to prevent race conditions
        selected_zone: Optional[ParkingZone] = None

        if request.preferred_zone_id:
            zone_stmt = (
                select(ParkingZone)
                .where(
                    ParkingZone.id == request.preferred_zone_id,
                    ParkingZone.is_active == True,
                )
                .with_for_update()
            )
            res = await db.execute(zone_stmt)
            candidate = res.scalar_one_or_none()
            if not candidate:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Preferred zone ID {request.preferred_zone_id} not found or inactive",
                )
            if candidate.current_occupancy >= candidate.total_capacity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Preferred zone '{candidate.zone_code}' is currently full ({candidate.current_occupancy}/{candidate.total_capacity})",
                )
            selected_zone = candidate
        else:
            # Query eligible zones where vehicle_type matches or is 'ALL'
            req_vtype = (request.vehicle_type or "LMV").upper()
            zone_query = (
                select(ParkingZone)
                .where(
                    ParkingZone.is_active == True,
                    ParkingZone.vehicle_type.in_([req_vtype, "ALL"]),
                    ParkingZone.current_occupancy < ParkingZone.total_capacity,
                )
                .order_by(ParkingZone.display_order, ParkingZone.id)
                .with_for_update()
            )
            if request.customer_site_id is not None:
                zone_query = zone_query.where(ParkingZone.customer_site_id == request.customer_site_id)

            res = await db.execute(zone_query)
            candidates = list(res.scalars().all())

            if not candidates:
                # Also check if any generic zone is open regardless of strict type if needed
                fallback_query = (
                    select(ParkingZone)
                    .where(
                        ParkingZone.is_active == True,
                        ParkingZone.current_occupancy < ParkingZone.total_capacity,
                    )
                    .order_by(ParkingZone.display_order, ParkingZone.id)
                    .with_for_update()
                )
                if request.customer_site_id is not None:
                    fallback_query = fallback_query.where(ParkingZone.customer_site_id == request.customer_site_id)
                fb_res = await db.execute(fallback_query)
                candidates = list(fb_res.scalars().all())

            if not candidates:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="All parking zones are at maximum capacity",
                )
            selected_zone = candidates[0]

        # 3. Increment occupancy safely
        selected_zone.current_occupancy += 1

        # 4. Generate unique slip number
        now = datetime.now(timezone.utc)
        unique_token = uuid.uuid4().hex[:6].upper()
        slip_number = f"SLIP-{now.strftime('%Y%m%d%H%M%S')}-{unique_token}"

        # 5. Persist ParkingSession
        session = ParkingSession(
            customer_site_id=request.customer_site_id or selected_zone.customer_site_id,
            parking_zone_id=selected_zone.id,
            entry_lane_id=request.lane_id,
            vehicle_number=request.vehicle_number.strip().upper(),
            normalized_plate=norm_plate,
            vehicle_type=(request.vehicle_type or "LMV").upper(),
            entry_time=now,
            status="ACTIVE",
            entry_slip_number=slip_number,
            anpr_transaction_id=request.anpr_transaction_id,
            fee_amount=0.0,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        await db.refresh(selected_zone)
        session.zone = selected_zone
        return session

    @staticmethod
    async def process_exit(
        db: AsyncSession,
        request: ParkingExitRequest,
    ) -> ParkingSession:
        """
        Processes vehicle exit:
        - Locates active session by slip or normalized plate
        - Decrements zone occupancy under row lock
        - Calculates total duration & parking fee
        - Sets session status to COMPLETED
        """
        stmt = (
            select(ParkingSession)
            .options(selectinload(ParkingSession.zone))
            .where(ParkingSession.status == "ACTIVE")
        )
        if request.entry_slip_number:
            stmt = stmt.where(ParkingSession.entry_slip_number == request.entry_slip_number.strip())
        elif request.vehicle_number:
            norm_plate = normalize_plate(request.vehicle_number)
            stmt = stmt.where(ParkingSession.normalized_plate == norm_plate)
            if request.customer_site_id is not None:
                stmt = stmt.where(ParkingSession.customer_site_id == request.customer_site_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either entry_slip_number or vehicle_number must be provided",
            )

        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active parking session not found for specified identifier",
            )

        # Lock the zone to decrement occupancy safely
        zone_stmt = (
            select(ParkingZone)
            .where(ParkingZone.id == session.parking_zone_id)
            .with_for_update()
        )
        z_res = await db.execute(zone_stmt)
        zone = z_res.scalar_one_or_none()
        if zone:
            zone.current_occupancy = max(0, zone.current_occupancy - 1)

        now = datetime.now(timezone.utc)
        session.exit_time = now
        session.exit_lane_id = request.exit_lane_id
        session.status = "COMPLETED"

        # Fee computation based on vehicle class and duration
        duration_sec = (session.exit_time - session.entry_time).total_seconds()
        duration_hours = max(1, math.ceil(duration_sec / 3600))

        vtype = (session.vehicle_type or "LMV").upper()
        if "BUS" in vtype or "HMV" in vtype:
            base_fee = 100.0
            hourly_rate = 50.0
        elif "2W" in vtype:
            base_fee = 20.0
            hourly_rate = 10.0
        elif "3W" in vtype:
            base_fee = 30.0
            hourly_rate = 15.0
        else:  # CAR / LMV
            base_fee = 50.0
            hourly_rate = 25.0

        if duration_hours <= 1:
            total_fee = base_fee
        else:
            total_fee = base_fee + (duration_hours - 1) * hourly_rate

        session.fee_amount = round(total_fee, 2)

        await db.commit()
        await db.refresh(session)
        if zone:
            session.zone = zone
        return session

    @staticmethod
    def session_to_slip_out(session: ParkingSession) -> ParkingSlipOut:
        duration_mins = None
        if session.exit_time and session.entry_time:
            duration_mins = int((session.exit_time - session.entry_time).total_seconds() / 60)
        elif session.entry_time:
            duration_mins = int((datetime.now(timezone.utc) - session.entry_time).total_seconds() / 60)

        zone_code = session.zone.zone_code if session.zone else "UNKNOWN"
        zone_name = session.zone.name if session.zone else "General Parking"

        return ParkingSlipOut(
            session_id=session.id,
            slip_number=session.entry_slip_number,
            vehicle_number=session.vehicle_number,
            vehicle_type=session.vehicle_type,
            zone_code=zone_code,
            zone_name=zone_name,
            entry_time=session.entry_time,
            exit_time=session.exit_time,
            duration_minutes=duration_mins,
            status=session.status,
            fee_amount=float(session.fee_amount or 0.0),
        )
