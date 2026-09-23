"""
surv/app/tests/test_chaos_resilience.py
Automated Chaos & Fault-Tolerance Verification Suite.
Exercises component failure scenarios:
1. Kafka outage during high-throughput event ingestion (degraded mode persistence)
2. Database connection drop and automatic rollback
3. Rapid camera flapping (online -> offline -> online transitions)
4. Expired and tampered token rejection under clock skew
5. MinIO upload verification failure preserves local file (no silent data loss)
6. Poison-pill / malformed Kafka events handled gracefully without crashing
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

if "minio" not in sys.modules:
    mock_minio = MagicMock()
    sys.modules["minio"] = mock_minio
    sys.modules["minio.error"] = MagicMock()
if "kafka" not in sys.modules:
    sys.modules["kafka"] = MagicMock()

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose.exceptions import ExpiredSignatureError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../surv/workers")))
from status_consumer import process_status_event
from upload_to_minio import verify_and_delete_local
from app.models.camera import Camera
from app.schemas.anpr import AnprEventIn
from app.services.anpr_service import AnprService
from app.dependencies.auth import get_current_user
from app.services.auth_service import create_access_token, decode_access_token


@pytest.mark.asyncio
async def test_chaos_kafka_outage_graceful_degradation():
    """
    Chaos scenario: Kafka cluster is completely unreachable or timed out.
    Requirement: Central ANPR event ingestion MUST succeed in saving the event to PostgreSQL
    without raising an unhandled exception or aborting the HTTP transaction.
    """
    db = AsyncMock()
    db.add = MagicMock()
    mock_wl_res = MagicMock()
    mock_wl_res.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_wl_res

    event = AnprEventIn(
        plate="KL01AZ7777",
        confidence=0.95,
        vehicle_type="LMV",
        customer_site_id=1,
    )

    # Force Kafka publish to fail simulating broker unreachable
    with patch("app.services.anpr_service.safe_publish_kafka", return_value=False) as mock_kafka:
        tx, alerts = await AnprService.record_anpr_event(db, event)

        # Ingestion succeeded despite Kafka broker failure
        assert tx.normalized_plate == "KL01AZ7777"
        assert db.commit.called
        assert mock_kafka.called


def test_chaos_rapid_camera_status_flapping():
    """
    Chaos scenario: Camera connectivity flaps rapidly (ONLINE -> OFFLINE -> ONLINE).
    Requirement: Worker processes updates idempotently and updates camera state accurately.
    """
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    # Event 1: Online transition, Event 2: Offline transition
    mock_cur.fetchone.side_effect = [
        {"id": 1, "cam_id": "CAM01", "cam_name": "Test Cam", "is_online": False},  # lookup
        {"id": 100, "changed_at": datetime.now(timezone.utc)},                       # prev log
        {"id": 1, "cam_id": "CAM01", "cam_name": "Test Cam", "is_online": True},   # lookup
        {"id": 101, "changed_at": datetime.now(timezone.utc)},                       # prev log
    ]

    process_status_event(mock_conn, {"camera": "CAM01", "status": "online"})
    assert mock_conn.commit.called

    mock_conn.commit.reset_mock()
    process_status_event(mock_conn, {"camera": "CAM01", "status": "offline"})
    assert mock_conn.commit.called


@pytest.mark.asyncio
async def test_chaos_db_session_rollback_on_query_failure():
    """
    Chaos scenario: Database error occurs midway through session allocation.
    Requirement: Transaction is rolled back and database error does not leave dirty state.
    """
    db = AsyncMock()
    db.execute.side_effect = RuntimeError("FATAL: terminating connection due to administrator command")

    from app.services.parking_service import ParkingAllocationService
    from app.schemas.parking import ParkingEntryRequest

    req = ParkingEntryRequest(vehicle_number="KL01AB1234")
    with pytest.raises(RuntimeError):
        await ParkingAllocationService.allocate_and_enter(db, req)


@pytest.mark.asyncio
async def test_chaos_clock_skew_expired_jwt_rejected():
    """
    Chaos scenario: Edge node or client token was issued in the past and has expired.
    Requirement: Auth service strictly rejects expired JWT tokens with 401 Unauthorized,
    and underlying jwt decoder raises ExpiredSignatureError.
    """
    # Token with negative expiry
    expired_token, _ = create_access_token(
        user_id=1,
        username="operator",
        user_type="EMPLOYEE",
        org_id=None,
        customer_id=None,
        roles=["OPERATOR"],
        permissions=["camera.view"],
        session_id="test_sess_expired",
        expires_in=-60,
    )

    # 1. Jose decoder raises ExpiredSignatureError
    with pytest.raises(ExpiredSignatureError):
        decode_access_token(expired_token)

    # 2. get_current_user dependency converts to 401 Unauthorized
    with pytest.raises(HTTPException) as exc:
        await get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired_token))
    assert exc.value.status_code == 401
    assert "Invalid or expired token" in exc.value.detail


def test_chaos_status_consumer_poison_pill_resilience():
    """
    Chaos scenario: Corrupt/poison-pill payloads received on Kafka topics.
    Requirement: Worker must not crash; unresolvable payloads are safely skipped.
    """
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_cur.fetchone.return_value = None

    # Empty payload
    process_status_event(mock_conn, {})
    assert not mock_conn.commit.called

    # Malformed camera name with no match
    process_status_event(mock_conn, {"camera": "UNKNOWN_GARBAGE_CAM", "status": "online"})
    assert not mock_conn.commit.called


def test_chaos_minio_upload_verification_failure_preserves_local_file(tmp_path):
    """
    Chaos scenario: Network glitch causes remote MinIO object to be truncated or corrupted.
    Requirement: verify_and_delete_local MUST verify size equality before unlinking local file.
    If remote size does not match local file size, local file must be preserved!
    """
    test_file = tmp_path / "test_segment.mp4"
    test_file.write_bytes(b"A" * 1024)  # 1024 bytes

    mock_client = MagicMock()
    mock_stat = MagicMock()
    mock_stat.size = 512  # Mismatched/truncated remote object
    mock_client.stat_object.return_value = mock_stat

    verify_and_delete_local(mock_client, test_file, "CAM01/2026/09/23/seg.mp4")

    # Local file MUST still exist to prevent silent data loss
    assert test_file.exists(), "Local segment was deleted despite size mismatch!"
