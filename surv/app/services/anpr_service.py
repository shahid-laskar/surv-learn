"""
app/services/anpr_service.py
ANPR Management Plane Service.
Handles ingestion of vehicle plate reads from Edge LPUs or Hub AI pipelines,
normalization, fuzzy similarity search, hotlist/watchlist alert matching,
and human-in-the-loop manual plate correction audit trails.
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.anpr import AnprTransaction, VehicleWatchlist, WatchlistAlert
from app.schemas.anpr import (
    AnprEventIn,
    PlateCorrectionIn,
    WatchlistCreate,
    WatchlistUpdate,
)

logger = logging.getLogger(__name__)


def normalize_plate(plate: str) -> str:
    """
    Standardizes license plate strings by stripping whitespace and non-alphanumeric characters.
    Example: 'KL 07 BH 9999' -> 'KL07BH9999'
    """
    if not plate:
        return ""
    return re.sub(r"[^A-Z0-9]", "", plate.upper())


def safe_publish_kafka(topic: str, payload: dict) -> bool:
    """
    Asynchronously or non-blockingly attempt to publish Kafka messages.
    Fails gracefully so DB persistence is never disrupted if Kafka is offline.
    """
    try:
        from kafka import KafkaProducer
        # Short timeout to avoid hanging when Kafka is unreachable in test environments
        producer = KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            request_timeout_ms=1000,
            max_block_ms=1000,
        )
        producer.send(topic, payload)
        producer.flush(timeout=1.0)
        return True
    except Exception as exc:
        logger.debug("Kafka safe publish skipped (%s): %s", topic, exc)
        return False


class AnprService:
    @staticmethod
    async def record_anpr_event(
        db: AsyncSession,
        event: AnprEventIn,
    ) -> Tuple[AnprTransaction, List[WatchlistAlert]]:
        """
        Persists incoming ANPR read, evaluates watchlists, and produces alerts.
        """
        norm_plate = normalize_plate(event.plate)
        if not norm_plate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valid plate number is required",
            )

        captured_time = event.timestamp or datetime.now(timezone.utc)

        # 1. Persist transaction
        tx = AnprTransaction(
            customer_site_id=event.customer_site_id,
            camera_id=event.camera_id,
            lane_id=event.lane_id,
            plate_number=event.plate.strip().upper(),
            normalized_plate=norm_plate,
            confidence=event.confidence,
            vehicle_type=(event.vehicle_type or "CAR").upper(),
            vehicle_color=event.vehicle_color,
            speed_kmh=event.speed_kmh,
            direction=event.direction.upper() if event.direction else None,
            snapshot_key=event.snapshot_key,
            video_reference=event.video_reference,
            processing_source=event.processing_source or "edge_lpu",
            is_corrected=False,
            captured_at=captured_time,
        )
        db.add(tx)
        await db.flush()
        await db.refresh(tx)

        # 2. Watchlist evaluation
        wl_stmt = select(VehicleWatchlist).where(
            VehicleWatchlist.is_active == True,
            VehicleWatchlist.normalized_plate == norm_plate,
        )
        wl_res = await db.execute(wl_stmt)
        matched_watchlists = list(wl_res.scalars().all())

        alerts: List[WatchlistAlert] = []
        for wl in matched_watchlists:
            alert = WatchlistAlert(
                watchlist_id=wl.id,
                anpr_transaction_id=tx.id,
                plate_number=tx.plate_number,
                camera_id=tx.camera_id,
                customer_site_id=tx.customer_site_id,
                severity=wl.severity,
                status="ACTIVE",
                created_at=datetime.now(timezone.utc),
            )
            db.add(alert)
            alerts.append(alert)

        await db.commit()
        await db.refresh(tx)
        for a in alerts:
            await db.refresh(a)

        # 3. Publish to Kafka (best-effort)
        event_payload = {
            "transaction_id": tx.id,
            "plate_number": tx.plate_number,
            "normalized_plate": tx.normalized_plate,
            "camera_id": tx.camera_id,
            "site_id": tx.customer_site_id,
            "timestamp": tx.captured_at.isoformat(),
            "confidence": tx.confidence,
        }
        safe_publish_kafka("anpr.events", event_payload)

        if alerts:
            for a in alerts:
                alert_payload = {
                    "alert_id": a.id,
                    "plate_number": a.plate_number,
                    "severity": a.severity,
                    "status": a.status,
                    "camera_id": a.camera_id,
                    "site_id": a.customer_site_id,
                    "timestamp": a.created_at.isoformat(),
                }
                safe_publish_kafka("anpr.alerts", alert_payload)

        return tx, alerts

    @staticmethod
    async def get_transaction_by_id(db: AsyncSession, tx_id: int) -> Optional[AnprTransaction]:
        return await db.get(AnprTransaction, tx_id)

    @staticmethod
    async def search_plates(
        db: AsyncSession,
        query: str,
        threshold: float = 0.3,
        site_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AnprTransaction]:
        """
        Fuzzy search for plates. Uses pg_trgm similarity when on PostgreSQL;
        falls back to ILIKE substring query when pg_trgm is unavailable or running on SQLite.
        """
        norm_query = normalize_plate(query)
        if not norm_query:
            return []

        # Check if database is PostgreSQL
        is_postgres = False
        try:
            bind = db.bind
            if bind and bind.dialect.name == "postgresql":
                is_postgres = True
        except Exception:
            pass

        stmt = select(AnprTransaction)
        if site_id is not None:
            stmt = stmt.where(AnprTransaction.customer_site_id == site_id)

        if is_postgres:
            try:
                # Use pg_trgm similarity
                stmt = stmt.where(
                    or_(
                        AnprTransaction.normalized_plate == norm_query,
                        func.similarity(AnprTransaction.normalized_plate, norm_query) >= threshold,
                    )
                ).order_by(
                    func.similarity(AnprTransaction.normalized_plate, norm_query).desc(),
                    AnprTransaction.captured_at.desc(),
                )
            except Exception:
                stmt = stmt.where(
                    AnprTransaction.normalized_plate.ilike(f"%{norm_query}%")
                ).order_by(AnprTransaction.captured_at.desc())
        else:
            # Fallback for SQLite / mock DBs
            stmt = stmt.where(
                AnprTransaction.normalized_plate.ilike(f"%{norm_query}%")
            ).order_by(AnprTransaction.captured_at.desc())

        stmt = stmt.offset(offset).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def correct_plate(
        db: AsyncSession,
        transaction_id: int,
        correction: PlateCorrectionIn,
        user_id: Optional[int] = None,
    ) -> AnprTransaction:
        """
        Human-in-the-loop manual plate correction:
        - Stores audit trail of original plate
        - Re-evaluates vehicle watchlist for newly corrected plate
        """
        tx = await db.get(AnprTransaction, transaction_id)
        if not tx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ANPR transaction not found")

        norm_corrected = normalize_plate(correction.corrected_plate)
        if not norm_corrected:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Corrected plate cannot be empty")

        if not tx.is_corrected:
            tx.original_plate = tx.plate_number

        tx.plate_number = correction.corrected_plate.strip().upper()
        tx.normalized_plate = norm_corrected
        tx.is_corrected = True
        tx.corrected_by_user_id = user_id
        tx.correction_notes = correction.correction_notes

        # Re-check watchlist for the corrected plate
        wl_stmt = select(VehicleWatchlist).where(
            VehicleWatchlist.is_active == True,
            VehicleWatchlist.normalized_plate == norm_corrected,
        )
        wl_res = await db.execute(wl_stmt)
        matched_watchlists = list(wl_res.scalars().all())

        for wl in matched_watchlists:
            # Check if alert already exists
            existing_alert = await db.execute(
                select(WatchlistAlert).where(
                    WatchlistAlert.watchlist_id == wl.id,
                    WatchlistAlert.anpr_transaction_id == tx.id,
                )
            )
            if not existing_alert.scalar_one_or_none():
                alert = WatchlistAlert(
                    watchlist_id=wl.id,
                    anpr_transaction_id=tx.id,
                    plate_number=tx.plate_number,
                    camera_id=tx.camera_id,
                    customer_site_id=tx.customer_site_id,
                    severity=wl.severity,
                    status="ACTIVE",
                    notes=f"Generated via manual operator correction from '{tx.original_plate}'",
                    created_at=datetime.now(timezone.utc),
                )
                db.add(alert)

        await db.commit()
        await db.refresh(tx)
        return tx

    # ── Watchlist Management ───────────────────────────────────────────────────

    @staticmethod
    async def create_watchlist(
        db: AsyncSession,
        data: WatchlistCreate,
        user_id: Optional[int] = None,
    ) -> VehicleWatchlist:
        norm_plate = normalize_plate(data.plate_number)
        if not norm_plate:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plate number is required")

        existing = await db.execute(
            select(VehicleWatchlist).where(VehicleWatchlist.normalized_plate == norm_plate)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Plate '{norm_plate}' is already registered in the watchlist",
            )

        entry = VehicleWatchlist(
            plate_number=data.plate_number.strip().upper(),
            normalized_plate=norm_plate,
            category=data.category.upper(),
            severity=data.severity.upper(),
            reason=data.reason.strip(),
            case_number=data.case_number.strip() if data.case_number else None,
            reporting_authority=data.reporting_authority.strip() if data.reporting_authority else None,
            is_active=data.is_active,
            created_by_user_id=user_id,
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry

    @staticmethod
    async def update_watchlist(
        db: AsyncSession,
        watchlist_id: int,
        data: WatchlistUpdate,
    ) -> VehicleWatchlist:
        entry = await db.get(VehicleWatchlist, watchlist_id)
        if not entry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist entry not found")

        if data.category is not None:
            entry.category = data.category.upper()
        if data.severity is not None:
            entry.severity = data.severity.upper()
        if data.reason is not None:
            entry.reason = data.reason.strip()
        if data.case_number is not None:
            entry.case_number = data.case_number.strip()
        if data.reporting_authority is not None:
            entry.reporting_authority = data.reporting_authority.strip()
        if data.is_active is not None:
            entry.is_active = data.is_active

        await db.commit()
        await db.refresh(entry)
        return entry

    @staticmethod
    async def list_watchlists(
        db: AsyncSession,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[VehicleWatchlist]:
        stmt = select(VehicleWatchlist).order_by(VehicleWatchlist.created_at.desc())
        if category:
            stmt = stmt.where(VehicleWatchlist.category == category.upper())
        if is_active is not None:
            stmt = stmt.where(VehicleWatchlist.is_active == is_active)

        stmt = stmt.offset(offset).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def list_alerts(
        db: AsyncSession,
        status_filter: Optional[str] = None,
        severity_filter: Optional[str] = None,
        customer_site_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[WatchlistAlert]:
        stmt = select(WatchlistAlert).order_by(WatchlistAlert.created_at.desc())
        if status_filter:
            stmt = stmt.where(WatchlistAlert.status == status_filter.upper())
        if severity_filter:
            stmt = stmt.where(WatchlistAlert.severity == severity_filter.upper())
        if customer_site_id is not None:
            stmt = stmt.where(WatchlistAlert.customer_site_id == customer_site_id)

        stmt = stmt.offset(offset).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def acknowledge_alert(
        db: AsyncSession,
        alert_id: int,
        user_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> WatchlistAlert:
        alert = await db.get(WatchlistAlert, alert_id)
        if not alert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

        alert.status = "ACKNOWLEDGED"
        alert.acknowledged_by_user_id = user_id
        alert.acknowledged_at = datetime.now(timezone.utc)
        if notes:
            alert.notes = notes.strip()

        await db.commit()
        await db.refresh(alert)
        return alert
