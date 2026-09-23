"""Unit tests for recordings router logic, timeline filtering, and presigned URLs."""

import pytest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.routers.recordings import get_timeline, get_download_url
from app.dependencies.auth import CurrentUser


def _user():
    return CurrentUser(
        user_id=1,
        username="operator",
        user_type="EMPLOYEE",
        org_id=1,
        customer_id=None,
        roles=["OPERATOR"],
        permissions=["camera.playback", "camera.download"],
        session_id="session-1",
    )


@pytest.mark.asyncio
async def test_timeline_camera_not_found():
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc:
        await get_timeline(
            cam_id="NON_EXISTENT",
            date="2026-06-27",
            type=None,
            db=db,
            user=_user(),
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_timeline_invalid_date():
    db = AsyncMock()
    mock_cam = SimpleNamespace(id=1, cam_id="CAM01")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_cam
    db.execute.return_value = mock_result

    with patch("app.routers.recordings.ensure_camera_accessible", new=AsyncMock()):
        with pytest.raises(HTTPException) as exc:
            await get_timeline(
                cam_id="CAM01",
                date="invalid-date-format",
                type=None,
                db=db,
                user=_user(),
            )
        assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_timeline_success():
    db = AsyncMock()
    mock_cam = SimpleNamespace(id=10, cam_id="CAM01")

    mock_seg1 = SimpleNamespace(
        id=101,
        camera_id=10,
        segment_start=datetime(2026, 6, 27, 10, 0, 0, tzinfo=timezone.utc),
        segment_end=datetime(2026, 6, 27, 10, 1, 0, tzinfo=timezone.utc),
        duration_seconds=60,
        file_size_bytes=1024000,
        object_key="CAM01/2026/06/27/10-00-00.mp4",
        bucket="recordings",
        recording_type="motion",
        has_motion=True,
        deleted_at=None,
    )

    mock_cam_res = MagicMock()
    mock_cam_res.scalar_one_or_none.return_value = mock_cam

    mock_seg_res = MagicMock()
    mock_seg_res.scalars.return_value.all.return_value = [mock_seg1]

    db.execute.side_effect = [mock_cam_res, mock_seg_res]

    with patch("app.routers.recordings.ensure_camera_accessible", new=AsyncMock()):
        with patch("app.routers.recordings.get_presigned_url", return_value="http://minio/signed-url"):
            res = await get_timeline(
                cam_id="CAM01",
                date="2026-06-27",
                type="motion",
                db=db,
                user=_user(),
            )

    assert res.camera_id == "CAM01"
    assert res.date == "2026-06-27"
    assert len(res.segments) == 1
    seg = res.segments[0]
    assert seg.segment_id == 101
    assert seg.recording_type == "motion"
    assert seg.playback_url == "http://minio/signed-url"
    assert seg.has_motion is True
