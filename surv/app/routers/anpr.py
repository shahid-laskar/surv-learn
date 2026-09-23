"""
app/routers/anpr.py
FastAPI router for ANPR Management Plane, Ingest API, Fuzzy Search,
Vehicle Watchlists, and Real-Time Interception Alerts.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, CurrentUser
from app.models.anpr import AnprTransaction
from app.schemas.anpr import (
    AlertAcknowledgeIn,
    AnprEventIn,
    AnprTransactionOut,
    PlateCorrectionIn,
    WatchlistAlertOut,
    WatchlistCreate,
    WatchlistOut,
    WatchlistUpdate,
)
from app.services.anpr_service import AnprService

router = APIRouter(prefix="/anpr", tags=["anpr"])


@router.post("/events", response_model=AnprTransactionOut, status_code=status.HTTP_201_CREATED)
async def ingest_anpr_event(
    payload: AnprEventIn,
    db: AsyncSession = Depends(get_db),
):
    """
    Standardized ingest endpoint for ANPR reads from Edge LPUs or Hub AI pipelines.
    Decoupled from inference hardware: validates payload, persists transaction,
    checks against active watchlists, and publishes to Kafka topics.
    """
    tx, _alerts = await AnprService.record_anpr_event(db, payload)
    return AnprTransactionOut.model_validate(tx)


@router.get("/transactions", response_model=List[AnprTransactionOut])
async def list_transactions(
    camera_id: Optional[int] = Query(None, description="Filter by camera ID"),
    site_id: Optional[int] = Query(None, description="Filter by customer site ID"),
    plate: Optional[str] = Query(None, description="Filter by exact plate number"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """List historical ANPR vehicle reads with pagination and filtering."""
    stmt = select(AnprTransaction).order_by(AnprTransaction.captured_at.desc())
    if camera_id is not None:
        stmt = stmt.where(AnprTransaction.camera_id == camera_id)
    if site_id is not None:
        stmt = stmt.where(AnprTransaction.customer_site_id == site_id)
    if plate:
        from app.services.anpr_service import normalize_plate
        stmt = stmt.where(AnprTransaction.normalized_plate == normalize_plate(plate))

    stmt = stmt.offset(offset).limit(limit)
    res = await db.execute(stmt)
    items = res.scalars().all()
    return [AnprTransactionOut.model_validate(item) for item in items]


@router.get("/transactions/{transaction_id}", response_model=AnprTransactionOut)
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Get single ANPR transaction details including evidence links and correction history."""
    tx = await AnprService.get_transaction_by_id(db, transaction_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ANPR transaction not found")
    return AnprTransactionOut.model_validate(tx)


@router.get("/search", response_model=List[AnprTransactionOut])
async def search_plates_fuzzy(
    q: str = Query(..., min_length=2, description="License plate query or partial plate"),
    threshold: float = Query(0.3, ge=0.0, le=1.0, description="Similarity threshold (0.0 - 1.0)"),
    site_id: Optional[int] = Query(None, description="Optional customer site ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Fuzzy plate search using PostgreSQL pg_trgm similarity.
    Tolerates typical OCR substitution errors (e.g. 0 vs O, 1 vs I, 8 vs B).
    """
    results = await AnprService.search_plates(
        db, query=q, threshold=threshold, site_id=site_id, limit=limit, offset=offset
    )
    return [AnprTransactionOut.model_validate(item) for item in results]


@router.post("/transactions/{transaction_id}/correct", response_model=AnprTransactionOut)
async def correct_anpr_plate(
    transaction_id: int,
    payload: PlateCorrectionIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Operator human-in-the-loop correction of an OCR misread.
    Preserves original OCR read in audit trail and triggers watchlist evaluation for corrected plate.
    """
    tx = await AnprService.correct_plate(
        db, transaction_id=transaction_id, correction=payload, user_id=user.user_id
    )
    return AnprTransactionOut.model_validate(tx)


# ── Watchlist & Hotlist Management ───────────────────────────────────────────

@router.get("/watchlists", response_model=List[WatchlistOut])
async def list_watchlists(
    category: Optional[str] = Query(None, description="WANTED | STOLEN | SUSPICIOUS | CUSTOM | VIP"),
    is_active: Optional[bool] = Query(None, description="Filter active entries"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """List registered watchlist and hotlist vehicles."""
    items = await AnprService.list_watchlists(
        db, category=category, is_active=is_active, limit=limit, offset=offset
    )
    return [WatchlistOut.model_validate(item) for item in items]


@router.post("/watchlists", response_model=WatchlistOut, status_code=status.HTTP_201_CREATED)
async def create_watchlist_entry(
    payload: WatchlistCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Enroll a vehicle into the police hotlist / watchlist."""
    item = await AnprService.create_watchlist(db, payload, user_id=user.user_id)
    return WatchlistOut.model_validate(item)


@router.patch("/watchlists/{watchlist_id}", response_model=WatchlistOut)
async def update_watchlist_entry(
    watchlist_id: int,
    payload: WatchlistUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Update vehicle watchlist status or metadata."""
    item = await AnprService.update_watchlist(db, watchlist_id, payload)
    return WatchlistOut.model_validate(item)


# ── Watchlist Alerts ─────────────────────────────────────────────────────────

@router.get("/alerts", response_model=List[WatchlistAlertOut])
async def list_alerts(
    status_filter: Optional[str] = Query(None, description="ACTIVE | ACKNOWLEDGED | DISMISSED"),
    severity: Optional[str] = Query(None, description="CRITICAL | HIGH | MEDIUM | LOW"),
    site_id: Optional[int] = Query(None, description="Customer site ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Query real-time hotlist alerts triggered by incoming ANPR detections."""
    alerts = await AnprService.list_alerts(
        db, status_filter=status_filter, severity_filter=severity,
        customer_site_id=site_id, limit=limit, offset=offset
    )
    return [WatchlistAlertOut.model_validate(a) for a in alerts]


@router.post("/alerts/{alert_id}/acknowledge", response_model=WatchlistAlertOut)
async def acknowledge_alert(
    alert_id: int,
    payload: AlertAcknowledgeIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Operator acknowledgement and disposition notes for an interception alert."""
    alert = await AnprService.acknowledge_alert(
        db, alert_id=alert_id, user_id=user.user_id, notes=payload.notes
    )
    return WatchlistAlertOut.model_validate(alert)
