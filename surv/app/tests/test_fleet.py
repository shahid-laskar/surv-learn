"""Unit tests for edge NVR fleet authentication, heartbeat processing, and configuration."""

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.dependencies.fleet_auth import verify_site_token
from app.routers.fleet import heartbeat, get_config
from app.schemas.fleet import HeartbeatIn


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
