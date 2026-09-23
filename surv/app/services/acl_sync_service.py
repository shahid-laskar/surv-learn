"""
acl_sync_service.py
Synchronizes BSNL organizational hierarchy with Headscale WireGuard namespaces and ACL rules.
"""

import json
import logging
import os
import re
from typing import List, Optional
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization

log = logging.getLogger("acl_sync")


def sanitize_headscale_username(name: str) -> str:
    """Headscale user names must be alphanumeric with dashes/underscores."""
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "-", name.strip().lower())
    sanitized = re.sub(r"-+", "-", sanitized).strip("-")
    return sanitized or "default-user"


class HeadscaleClient:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    async def _request(self, method: str, endpoint: str, **kwargs):
        if not self.api_key:
            log.debug("HEADSCALE_API_KEY not configured — skipping API request")
            return {}
        url = f"{self.api_url}/api/v1{endpoint}"
        async with httpx.AsyncClient() as client:
            resp = await client.request(method, url, headers=self.headers, timeout=10.0, **kwargs)
            resp.raise_for_status()
            return resp.json()

    async def list_users(self) -> list[str]:
        data = await self._request("GET", "/user")
        return [u.get("name", "") for u in data.get("users", []) if u.get("name")]

    async def sync_organization(self, org_name: str) -> bool:
        """Ensure a Headscale user (namespace) exists for this organization."""
        username = sanitize_headscale_username(org_name)
        existing = await self.list_users()
        if username not in existing:
            await self._request("POST", "/user", json={"name": username})
            log.info(f"Created Headscale user for organization: {username}")
            return True
        return False


class ACLSyncService:
    def __init__(self):
        self.domain = os.environ.get("HEADSCALE_DOMAIN", "vpn.sarvanetra.bsnl.co.in")
        self.api_key = os.environ.get("HEADSCALE_API_KEY", "")
        self.acl_path = os.environ.get("HEADSCALE_ACL_PATH", "/etc/headscale/acl.hcl")
        protocol = "http" if "localhost" in self.domain or "127.0.0.1" in self.domain else "https"
        self.client = HeadscaleClient(f"{protocol}://{self.domain}", self.api_key)

    async def sync_orgs(self, db_session: AsyncSession) -> list[str]:
        """Query active organizations from DB and ensure corresponding users exist in Headscale."""
        result = await db_session.execute(select(Organization).where(Organization.is_active == True))
        orgs = result.scalars().all()
        synced: list[str] = []

        # Ensure base namespaces exist
        base_users = ["hub", "nvr"]
        for base in base_users:
            try:
                await self.client.sync_organization(base)
                synced.append(base)
            except Exception as e:
                log.warning(f"Could not sync base Headscale user '{base}': {e}")

        for org in orgs:
            username = sanitize_headscale_username(org.code or org.name)
            try:
                await self.client.sync_organization(username)
                synced.append(username)
            except Exception as e:
                log.warning(f"Could not sync Headscale user for org '{org.code}': {e}")

        return synced

    def build_acl_policy(self, org_users: Optional[list[str]] = None) -> dict:
        """Construct the ACL policy dict for Headscale."""
        org_users = org_users or []
        groups = {
            "group:hub": ["hub"],
            "group:nvr": ["nvr"],
            "group:mobile": list(set(org_users)),
        }
        acls = [
            # Hub can reach all NVRs and clients
            {"action": "accept", "src": ["group:hub"], "dst": ["*:*"]},
            # NVRs can reach hub
            {"action": "accept", "src": ["group:nvr"], "dst": ["group:hub:*"]},
            # Scoped users can reach hub
            {"action": "accept", "src": ["group:mobile"], "dst": ["group:hub:*"]},
        ]
        return {"groups": groups, "acls": acls}

    async def update_acls(self, db_session: Optional[AsyncSession] = None) -> dict:
        """Generate ACL rules and write to the Headscale ACL file if accessible."""
        org_users = []
        if db_session:
            result = await db_session.execute(select(Organization).where(Organization.is_active == True))
            orgs = result.scalars().all()
            org_users = [sanitize_headscale_username(o.code or o.name) for o in orgs]

        policy = self.build_acl_policy(org_users)
        try:
            if os.path.exists(os.path.dirname(self.acl_path)):
                with open(self.acl_path, "w") as f:
                    json.dump(policy, f, indent=2)
                log.info(f"Updated Headscale ACL policy at {self.acl_path}")
        except Exception as e:
            log.warning(f"Could not write ACL file at {self.acl_path}: {e}")

        return policy


acl_sync_service = ACLSyncService()
