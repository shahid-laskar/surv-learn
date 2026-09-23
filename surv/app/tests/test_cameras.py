"""Unit tests for camera schemas, protocol normalization, and MediaMTX client integration."""

import pytest
from pydantic import ValidationError
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.camera import CameraCreate, CameraUpdate
from app.services.mediamtx_client import MediaMTXClient


def test_camera_create_valid():
    data = {
        "cam_id": "CAM001",
        "cam_name": "Front Gate",
        "cam_ip": "192.168.1.100",
        "cam_port": 554,
        "stream_protocol": "rtsp",
        "onvif_username": "admin",
        "onvif_password": "pass@123#special!",
        "recording_mode": "motion_only",
        "retention_days": 15,
    }
    camera = CameraCreate(**data)
    assert camera.cam_id == "CAM001"
    assert camera.stream_protocol == "rtsp"
    assert camera.recording_mode == "motion_only"
    assert camera.retention_days == 15


def test_camera_create_invalid_protocol():
    data = {
        "cam_id": "CAM002",
        "cam_ip": "192.168.1.101",
        "stream_protocol": "invalid_proto",
    }
    with pytest.raises(ValidationError):
        CameraCreate(**data)


def test_mediamtx_protocol_normalization():
    client = MediaMTXClient()
    
    c1 = SimpleNamespace(cam_id="C1", stream_protocol="rtsp")
    assert client._normalize_protocol(c1) == "rtsp"

    c2 = SimpleNamespace(cam_id="C2", stream_protocol="RTSPS")
    assert client._normalize_protocol(c2) == "rtsps"

    c3 = SimpleNamespace(cam_id="C3", stream_protocol="rtmp")
    assert client._normalize_protocol(c3) == "rtmp"

    c4 = SimpleNamespace(cam_id="C4", stream_protocol="unknown_proto")
    assert client._normalize_protocol(c4) == "rtsp"

    c5 = SimpleNamespace(cam_id="C5", stream_protocol=None)
    assert client._normalize_protocol(c5) == "rtsp"


def test_mediamtx_get_pull_source_url_encoding():
    client = MediaMTXClient()
    cam = SimpleNamespace(
        cam_id="CAM_TEST",
        cam_ip="10.0.0.50",
        cam_port=554,
        onvif_username="user@domain",
        onvif_password="p@ss#word!with:special",
        rtsp_url=None,
    )
    url = client._get_pull_source_url(cam, "rtsp")
    # Credentials should be percent-encoded:
    # @ -> %40, # -> %23, : -> %3A
    assert "user%40domain" in url
    assert "p%40ss%23word%21with%3Aspecial" in url
    assert "@10.0.0.50:554/stream1" in url
    assert url.startswith("rtsp://")


def test_mediamtx_get_pull_source_url_custom_rtsp_url():
    client = MediaMTXClient()
    cam = SimpleNamespace(
        cam_id="CAM_CUSTOM",
        cam_ip="10.0.0.50",
        cam_port=554,
        onvif_username="admin",
        onvif_password="password",
        rtsp_url="rtsps://10.0.0.60:322/live/sub",
    )
    url = client._get_pull_source_url(cam, "rtsps")
    assert url == "rtsps://admin:password@10.0.0.60:322/live/sub"


def test_mediamtx_path_payload_rtmp_publisher():
    client = MediaMTXClient()
    cam = SimpleNamespace(
        cam_id="CAM_RTMP",
        stream_protocol="rtmp",
        cam_ip="10.0.0.50",
        cam_port=1935,
        onvif_username="admin",
        onvif_password="password",
        rtsp_url=None,
    )
    payload = client._path_payload(cam)
    assert payload == {"source": "publisher"}


def test_mediamtx_path_payload_rtsp_pull():
    client = MediaMTXClient()
    cam = SimpleNamespace(
        cam_id="CAM_RTSP",
        stream_protocol="rtsp",
        cam_ip="10.0.0.50",
        cam_port=554,
        onvif_username="admin",
        onvif_password="password",
        rtsp_url=None,
    )
    payload = client._path_payload(cam)
    assert payload["sourceProtocol"] == "tcp"
    assert "source" in payload
    assert payload["source"].startswith("rtsp://admin:password@10.0.0.50:554")


@pytest.mark.asyncio
async def test_mediamtx_add_and_remove_camera():
    client = MediaMTXClient()
    cam = SimpleNamespace(
        cam_id="CAM_TEST_API",
        stream_protocol="rtsp",
        cam_ip="192.168.1.20",
        cam_port=554,
        onvif_username="admin",
        onvif_password="password",
        rtsp_url=None,
    )

    mock_resp_success = SimpleNamespace(status_code=200, text="OK")
    
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_resp_success)) as mock_post:
        await client.add_camera(cam)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert f"/v3/config/paths/replace/{cam.cam_id}" in args[0]
        assert kwargs["json"]["sourceProtocol"] == "tcp"

    with patch("httpx.AsyncClient.delete", new=AsyncMock(return_value=mock_resp_success)) as mock_del:
        await client.remove_camera("CAM_TEST_API")
        mock_del.assert_called_once()
        args, _ = mock_del.call_args
        assert "/v3/config/paths/delete/CAM_TEST_API" in args[0]


@pytest.mark.asyncio
async def test_create_camera_router_duplicate():
    from fastapi import HTTPException
    from app.routers.cameras import create_camera

    db = AsyncMock()
    user = SimpleNamespace(username="admin_user")
    payload = CameraCreate(
        cam_id="CAM_DUP",
        cam_ip="192.168.1.50",
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = SimpleNamespace(id=1, cam_id="CAM_DUP")
    db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc:
        await create_camera(payload=payload, db=db, user=user)
    assert exc.value.status_code == 409
    assert "already exists" in exc.value.detail


@pytest.mark.asyncio
async def test_deactivate_camera_router():
    from app.routers.cameras import deactivate_camera

    db = AsyncMock()
    user = SimpleNamespace(username="admin_user", roles=["SUPER_ADMIN"], permissions=[])
    cam = SimpleNamespace(id=10, cam_id="CAM_DEACT", is_active=True)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = cam
    db.execute.return_value = mock_result
    db.commit = AsyncMock()

    with patch("app.routers.cameras.mediamtx_client.remove_camera", new=AsyncMock()) as mock_remove:
        with patch("app.routers.cameras.ensure_camera_accessible", new=AsyncMock()):
            await deactivate_camera(cam_id="CAM_DEACT", db=db, user=user)
            assert cam.is_active is False
            db.commit.assert_called_once()
            mock_remove.assert_called_once_with("CAM_DEACT")
