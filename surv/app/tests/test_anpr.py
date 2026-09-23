"""
surv/app/tests/test_anpr.py
Unit tests for ANPR Management Plane:
Event ingestion, plate normalization, watchlist hit matching,
human-in-the-loop manual plate correction audit trail, and alert acknowledgement.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.anpr import AnprTransaction, VehicleWatchlist, WatchlistAlert
from app.schemas.anpr import (
    AnprEventIn,
    PlateCorrectionIn,
    WatchlistCreate,
    WatchlistUpdate,
)
from app.services.anpr_service import AnprService, normalize_plate


def test_normalize_plate_anpr():
    assert normalize_plate("kl-07 bh 9999") == "KL07BH9999"
    assert normalize_plate("mh.02.cz.1234") == "MH02CZ1234"
    assert normalize_plate("") == ""


@pytest.mark.asyncio
async def test_record_anpr_event_no_match():
    db = AsyncMock()
    db.add = MagicMock()
    # Mock watchlist query returning empty list
    mock_wl_res = MagicMock()
    mock_wl_res.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_wl_res

    event = AnprEventIn(
        plate="KL01AB1234",
        confidence=0.96,
        vehicle_type="CAR",
        customer_site_id=1,
        camera_id=10,
    )
    with patch("app.services.anpr_service.safe_publish_kafka") as mock_kafka:
        tx, alerts = await AnprService.record_anpr_event(db, event)

        assert tx.normalized_plate == "KL01AB1234"
        assert tx.plate_number == "KL01AB1234"
        assert tx.confidence == 0.96
        assert len(alerts) == 0
        assert db.add.called
        assert db.commit.called
        mock_kafka.assert_called_with("anpr.events", pytest.approx(mock_kafka.call_args_list[0][0][1]))


@pytest.mark.asyncio
async def test_record_anpr_event_with_watchlist_hit():
    db = AsyncMock()
    db.add = MagicMock()
    wl_entry = VehicleWatchlist(
        id=42,
        plate_number="KL07BH9999",
        normalized_plate="KL07BH9999",
        category="WANTED",
        severity="CRITICAL",
        reason="Stolen bank cash transfer van",
        is_active=True,
    )
    mock_wl_res = MagicMock()
    mock_wl_res.scalars.return_value.all.return_value = [wl_entry]
    db.execute.return_value = mock_wl_res

    event = AnprEventIn(
        plate="kl-07-bh-9999",
        confidence=0.98,
        vehicle_type="CAR",
        customer_site_id=1,
        camera_id=5,
    )
    with patch("app.services.anpr_service.safe_publish_kafka") as mock_kafka:
        tx, alerts = await AnprService.record_anpr_event(db, event)

        assert tx.normalized_plate == "KL07BH9999"
        assert len(alerts) == 1
        assert alerts[0].watchlist_id == 42
        assert alerts[0].severity == "CRITICAL"
        assert alerts[0].status == "ACTIVE"
        # Verified Kafka published to both anpr.events and anpr.alerts
        assert mock_kafka.call_count == 2


@pytest.mark.asyncio
async def test_correct_plate_audit_trail():
    db = AsyncMock()
    tx = AnprTransaction(
        id=100,
        plate_number="KL01AB123O",  # OCR read 'O' instead of '0'
        normalized_plate="KL01AB123O",
        confidence=0.72,
        is_corrected=False,
        original_plate=None,
    )
    db.get.return_value = tx

    # Watchlist check on corrected plate
    mock_wl_res = MagicMock()
    mock_wl_res.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_wl_res

    correction = PlateCorrectionIn(
        corrected_plate="KL01AB1230",
        correction_notes="Manual verification from hi-res snapshot: 0 not O",
    )
    corrected_tx = await AnprService.correct_plate(
        db, transaction_id=100, correction=correction, user_id=9
    )

    assert corrected_tx.is_corrected is True
    assert corrected_tx.original_plate == "KL01AB123O"
    assert corrected_tx.plate_number == "KL01AB1230"
    assert corrected_tx.normalized_plate == "KL01AB1230"
    assert corrected_tx.corrected_by_user_id == 9
    assert corrected_tx.correction_notes == "Manual verification from hi-res snapshot: 0 not O"
    assert db.commit.called


@pytest.mark.asyncio
async def test_create_watchlist_duplicate_conflict():
    db = AsyncMock()
    mock_dup = MagicMock()
    mock_dup.scalar_one_or_none.return_value = VehicleWatchlist(id=1, normalized_plate="KL07BH9999")
    db.execute.return_value = mock_dup

    data = WatchlistCreate(
        plate_number="KL-07-BH-9999",
        category="STOLEN",
        severity="HIGH",
        reason="Stolen car",
    )
    with pytest.raises(HTTPException) as exc:
        await AnprService.create_watchlist(db, data, user_id=1)
    assert exc.value.status_code == 409
    assert "already registered" in exc.value.detail


@pytest.mark.asyncio
async def test_acknowledge_alert():
    db = AsyncMock()
    alert = WatchlistAlert(
        id=7,
        watchlist_id=1,
        anpr_transaction_id=10,
        plate_number="KL07BH9999",
        severity="HIGH",
        status="ACTIVE",
    )
    db.get.return_value = alert

    ack = await AnprService.acknowledge_alert(
        db, alert_id=7, user_id=42, notes="Intercepted at Nilakkal Ground 2"
    )
    assert ack.status == "ACKNOWLEDGED"
    assert ack.acknowledged_by_user_id == 42
    assert ack.acknowledged_at is not None
    assert ack.notes == "Intercepted at Nilakkal Ground 2"
    assert db.commit.called
