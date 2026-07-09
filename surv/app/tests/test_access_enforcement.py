"""Phase A — camera access enforcement unit tests."""

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from app.services.access_service import ensure_camera_accessible


def _user(roles: list[str] | None = None):
    return SimpleNamespace(
        user_id=1,
        username="tester",
        roles=roles or ["VIEWER"],
    )


@pytest.mark.asyncio
async def test_ensure_camera_accessible_unrestricted():
    db = AsyncMock()
    with patch(
        "app.services.access_service.get_accessible_camera_ids",
        new=AsyncMock(return_value=None),
    ):
        await ensure_camera_accessible(_user(["SUPER_ADMIN"]), db, 42)


@pytest.mark.asyncio
async def test_ensure_camera_accessible_allowed():
    db = AsyncMock()
    with patch(
        "app.services.access_service.get_accessible_camera_ids",
        new=AsyncMock(return_value=[1, 2, 42]),
    ):
        await ensure_camera_accessible(_user(), db, 42)


@pytest.mark.asyncio
async def test_ensure_camera_accessible_denied():
    db = AsyncMock()
    with patch(
        "app.services.access_service.get_accessible_camera_ids",
        new=AsyncMock(return_value=[1, 2]),
    ):
        with pytest.raises(HTTPException) as exc:
            await ensure_camera_accessible(_user(), db, 99)
        assert exc.value.status_code == 403
