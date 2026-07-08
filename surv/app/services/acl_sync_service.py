import httpx
import logging
import os

log = logging.getLogger("acl_sync")

class HeadscaleClient:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def _request(self, method: str, endpoint: str, **kwargs):
        url = f"{self.api_url}/api/v1{endpoint}"
        async with httpx.AsyncClient() as client:
            resp = await client.request(method, url, headers=self.headers, **kwargs)
            resp.raise_for_status()
            return resp.json()

    async def list_users(self):
        return await self._request("GET", "/user")

    async def sync_organization(self, org_name: str):
        # We map organizations to Headscale "users" (namespaces)
        users = await self.list_users()
        existing = [u["name"] for u in users.get("users", [])]
        if org_name not in existing:
            await self._request("POST", "/user", json={"name": org_name})
            log.info(f"Created Headscale user for organization: {org_name}")


class ACLSyncService:
    def __init__(self):
        self.domain = os.environ.get("HEADSCALE_DOMAIN", "vpn.sarvanetra.internal")
        self.api_key = os.environ.get("HEADSCALE_API_KEY", "")
        self.client = HeadscaleClient(f"https://{self.domain}", self.api_key)

    async def sync_orgs(self, db_session):
        # In a full implementation, we'd query all organizations from the DB
        # and create corresponding users in Headscale.
        pass

    async def update_acls(self):
        # In a full implementation, we'd read the current acl.hcl, augment it
        # with organization-specific rules, and apply it via the API or filesystem.
        pass

acl_sync_service = ACLSyncService()
