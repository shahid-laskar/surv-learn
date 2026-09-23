"""Unit tests for edge NVR fleet authentication, heartbeat processing, and configuration."""

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.dependencies.fleet_auth import verify_site_token
from app.routers.fleet import heartbeat, get_config, upload_backup_clip
from app.schemas.fleet import HeartbeatIn, BackupClipIn
from app.routers.motion import ingest_edge_motion
from app.schemas.motion import EdgeMotionIn


@pytest.mark.asyncio
async def test_verify_site_token_missing_header():
    db = AsyncMock()
    with pytest.raises(HTTPException) as exc:
        await verify_site_token("SITE01", db=db, x_site_token=None)
    assert exc.value.status_code == 401
    assert "Missing X-Site-Token header" in exc.value.detail


@pytest.mark.asyncio
async def test_verify_site_token_invalid_site_or_secret():
    db = AsyncMock()
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc:
        await verify_site_token("UNKNOWN_SITE", db=db, x_site_token="some_token")
    assert exc.value.status_code == 401
    assert "Invalid site credentials" in exc.value.detail


@pytest.mark.asyncio
async def test_verify_site_token_mismatch():
    db = AsyncMock()
    node = SimpleNamespace(site_code="SITE01", site_enrollment_secret="correct_secret_token_123")
    db.scalar.return_value = node

    with pytest.raises(HTTPException) as exc:
        await verify_site_token("SITE01", db=db, x_site_token="wrong_secret_token")
    assert exc.value.status_code == 401
    assert "Invalid site credentials" in exc.value.detail


@pytest.mark.asyncio
async def test_verify_site_token_valid():
    db = AsyncMock()
    node = SimpleNamespace(site_code="SITE01", site_enrollment_secret="correct_secret_token_123")
    db.scalar.return_value = node

    result = await verify_site_token("SITE01", db=db, x_site_token="correct_secret_token_123")
    assert result == node


@pytest.mark.asyncio
async def test_heartbeat_unprovisioned_nvr():
    db = AsyncMock()
    db.scalar.return_value = None

    hb_payload = HeartbeatIn(
        site_code="SITE_UNREGISTERED",
        agent_version="1.0.0",
        disk_used_pct=45.0,
        online_cameras=[],
    )

    with pytest.raises(HTTPException) as exc:
        await heartbeat(hb_payload, db=db, x_site_token="any_token")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_heartbeat_success():
    db = AsyncMock()
    node = SimpleNamespace(
        id=5,
        site_code="SITE01",
        site_enrollment_secret="site_secret_abc",
        agent_version=None,
        disk_used_pct=None,
        last_heartbeat=None,
        is_provisioned=False,
        overlay_ip=None,
    )
    db.scalar.return_value = node
    db.commit = AsyncMock()
    db.execute = AsyncMock()

    hb_payload = HeartbeatIn(
        site_code="SITE01",
        agent_version="1.2.0",
        disk_used_pct=62.5,
        online_cameras=["CAM01"],
        overlay_ip="100.64.0.5",
    )

    res = await heartbeat(hb_payload, db=db, x_site_token="site_secret_abc")
    assert res == {"status": "ok"}
    assert node.agent_version == "1.2.0"
    assert node.disk_used_pct == 62.5
    assert node.is_provisioned is True
    assert node.overlay_ip == "100.64.0.5"
    assert node.last_heartbeat is not None
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_config_success():
    db = AsyncMock()
    node = SimpleNamespace(id=1, site_code="SITE01")
    cam = SimpleNamespace(
        cam_id="CAM01",
        cam_ip="192.168.1.10",
        cam_port=554,
        onvif_port=80,
        rtsp_url=None,
        onvif_username="admin",
        onvif_password="pwd",
        motion_active=True,
        retention_days=15,
    )
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [cam]
    scalars_mock.__iter__.return_value = [cam]
    db.scalars.return_value = [cam]

    res = await get_config(site_code="SITE01", db=db, node=node)
    assert res.site_code == "SITE01"
    assert len(res.cameras) == 1
    assert res.cameras[0].cam_id == "CAM01"


@pytest.mark.asyncio
async def test_get_config_mismatch():
    db = AsyncMock()
    node = SimpleNamespace(id=1, site_code="SITE01")
    with pytest.raises(HTTPException) as exc:
        await get_config(site_code="SITE02", db=db, node=node)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_upload_backup_clip_success():
    from datetime import datetime, timezone
    db = AsyncMock()
    node = SimpleNamespace(id=2, site_code="SITE01")
    cam = SimpleNamespace(id=10, cam_id="CAM01")
    db.scalar.return_value = cam
    db.add = MagicMock()
    db.commit = AsyncMock()

    payload = BackupClipIn(
        cam_id="CAM01",
        object_key="backup_clips/SITE01/CAM01/clip.mp4",
        reason="motion_trigger",
        captured_at=datetime.now(timezone.utc),
    )
    res = await upload_backup_clip(site_code="SITE01", clip=payload, db=db, node=node)
    assert res == {"status": "ok"}
    db.add.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_upload_backup_clip_mismatch():
    from datetime import datetime, timezone
    db = AsyncMock()
    node = SimpleNamespace(id=2, site_code="SITE01")
    payload = BackupClipIn(
        cam_id="CAM01",
        object_key="clip.mp4",
        reason="motion",
        captured_at=datetime.now(timezone.utc),
    )
    with pytest.raises(HTTPException) as exc:
        await upload_backup_clip(site_code="SITE02", clip=payload, db=db, node=node)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_ingest_edge_motion_success():
    from datetime import datetime, timezone
    db = AsyncMock()
    node = SimpleNamespace(id=5, site_code="SITE01")
    cam = SimpleNamespace(id=20, cam_id="CAM01")
    db.scalar.return_value = cam
    db.add = MagicMock()

    payload = EdgeMotionIn(
        site_code="SITE01",
        cam_id="CAM01",
        motion_start=datetime.now(timezone.utc),
        motion_end=None,
        is_active=True,
    )
    res = await ingest_edge_motion(payload=payload, db=db, node=node)
    assert res == {"status": "ok"}
    db.add.assert_called_once()


@pytest.mark.asyncio
async def test_ingest_edge_motion_mismatch():
    db = AsyncMock()
    node = SimpleNamespace(id=5, site_code="SITE01")
    payload = EdgeMotionIn(
        site_code="SITE_WRONG",
        cam_id="CAM01",
        motion_start="2026-09-23T07:00:00Z",
        motion_end=None,
        is_active=True,
    )
    with pytest.raises(HTTPException) as exc:
        await ingest_edge_motion(payload=payload, db=db, node=node)
    assert exc.value.status_code == 403
