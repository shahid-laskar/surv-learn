"""Unit tests for Headscale ACL synchronization service."""

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.acl_sync_service import (
    sanitize_headscale_username,
    HeadscaleClient,
    ACLSyncService,
)


def test_sanitize_headscale_username():
    assert sanitize_headscale_username("BSNL_Circle_Kerala") == "bsnl_circle_kerala"
    assert sanitize_headscale_username("Circle Kerala - 01!") == "circle-kerala-01"
    assert sanitize_headscale_username("---Test---") == "test"
    assert sanitize_headscale_username("") == "default-user"


@pytest.mark.asyncio
async def test_headscale_client_sync_org():
    client = HeadscaleClient(api_url="http://test-headscale:8080", api_key="secret-key")

    with patch.object(client, "list_users", new=AsyncMock(return_value=["hub", "nvr"])):
        with patch.object(client, "_request", new=AsyncMock(return_value={"user": {"name": "kerala"}})) as mock_req:
            created = await client.sync_organization("kerala")
            assert created is True
            mock_req.assert_called_once_with("POST", "/user", json={"name": "kerala"})

    # Test idempotent when already existing
    with patch.object(client, "list_users", new=AsyncMock(return_value=["hub", "nvr", "kerala"])):
        with patch.object(client, "_request", new=AsyncMock()) as mock_req:
            created = await client.sync_organization("kerala")
            assert created is False
            mock_req.assert_not_called()


@pytest.mark.asyncio
async def test_acl_sync_service_build_policy():
    service = ACLSyncService()
    policy = service.build_acl_policy(["circle-kerala", "ba-tvm"])

    assert "groups" in policy
    assert "group:hub" in policy["groups"]
    assert "group:mobile" in policy["groups"]
    assert "circle-kerala" in policy["groups"]["group:mobile"]
    assert "ba-tvm" in policy["groups"]["group:mobile"]

    assert "acls" in policy
    assert len(policy["acls"]) == 3
    assert any(rule["src"] == ["group:hub"] for rule in policy["acls"])


@pytest.mark.asyncio
async def test_acl_sync_service_sync_orgs():
    service = ACLSyncService()
    db = AsyncMock()

    org1 = SimpleNamespace(id=1, code="CIRCLE_KL", name="Kerala Circle", is_active=True)
    org2 = SimpleNamespace(id=2, code="BA_TVM", name="Trivandrum BA", is_active=True)
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = [org1, org2]
    db.execute.return_value = mock_res

    with patch.object(service.client, "sync_organization", new=AsyncMock(return_value=True)):
        synced = await service.sync_orgs(db)
        assert "hub" in synced
        assert "nvr" in synced
        assert "circle_kl" in synced
        assert "ba_tvm" in synced
