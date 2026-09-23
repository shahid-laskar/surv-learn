"""Unit tests for camera access control and organization subtree resolution."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.services.access_service import (
    get_accessible_camera_ids,
    ensure_camera_accessible,
    UNRESTRICTED_ROLES,
    ORG_SCOPED_ROLES,
)
from app.dependencies.auth import CurrentUser


def _make_user(
    user_id: int = 1,
    username: str = "testuser",
    roles: list[str] | None = None,
    org_id: int | None = None,
    customer_id: int | None = None,
) -> CurrentUser:
    return CurrentUser(
        user_id=user_id,
        username=username,
        user_type="EMPLOYEE",
        org_id=org_id,
        customer_id=customer_id,
        roles=roles if roles is not None else ["VIEWER"],
        permissions=["camera.view"],
        session_id="session-1234",
    )


@pytest.mark.asyncio
async def test_super_admin_unrestricted():
    db = AsyncMock()
    user = _make_user(roles=["SUPER_ADMIN"])
    accessible = await get_accessible_camera_ids(user, db)
    assert accessible is None
    # ensure_camera_accessible should not raise
    await ensure_camera_accessible(user, db, 999)


@pytest.mark.asyncio
async def test_national_noc_unrestricted():
    db = AsyncMock()
    user = _make_user(roles=["NATIONAL_NOC"])
    accessible = await get_accessible_camera_ids(user, db)
    assert accessible is None
    await ensure_camera_accessible(user, db, 123)


@pytest.mark.asyncio
async def test_user_without_roles_legacy_unrestricted():
    db = AsyncMock()
    # Mock empty returns for direct grants and group mappings
    mock_empty = MagicMock()
    mock_empty.all.return_value = []
    db.execute.return_value = mock_empty

    user = _make_user(roles=[])
    accessible = await get_accessible_camera_ids(user, db)
    assert accessible is None


@pytest.mark.asyncio
async def test_org_scoped_user_with_subtree_and_direct_grants():
    db = AsyncMock()

    # Query 1: subtree org IDs -> [10, 11]
    mock_subtree_res = MagicMock()
    mock_subtree_res.all.return_value = [(10,), (11,)]

    # Query 2: cameras in org subtree -> [101, 102]
    mock_cam_res = MagicMock()
    mock_cam_res.all.return_value = [(101,), (102,)]

    # Query 3: direct user-camera grants -> [201]
    mock_direct_res = MagicMock()
    mock_direct_res.all.return_value = [(201,)]

    # Query 4: camera group membership -> [301]
    mock_group_res = MagicMock()
    mock_group_res.all.return_value = [(301,)]

    db.execute.side_effect = [
        mock_subtree_res,
        mock_cam_res,
        mock_direct_res,
        mock_group_res,
    ]

    user = _make_user(roles=["CIRCLE_ADMIN"], org_id=10)
    accessible = await get_accessible_camera_ids(user, db)

    assert accessible is not None
    assert set(accessible) == {101, 102, 201, 301}

    # Verify access enforcement
    # Should succeed for accessible camera
    db.execute.side_effect = [
        mock_subtree_res,
        mock_cam_res,
        mock_direct_res,
        mock_group_res,
    ]
    await ensure_camera_accessible(user, db, 101)

    # Should raise 403 for unauthorized camera
    db.execute.side_effect = [
        mock_subtree_res,
        mock_cam_res,
        mock_direct_res,
        mock_group_res,
    ]
    with pytest.raises(HTTPException) as exc_info:
        await ensure_camera_accessible(user, db, 999)
    assert exc_info.value.status_code == 403
