import asyncio
import logging
import httpx

log = logging.getLogger("config_sync")

async def config_sync_loop(site_code: str, hub_url: str):
    while True:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{hub_url}/fleet/{site_code}/config", timeout=10)
                resp.raise_for_status()
                data = resp.json()
                
            log.info(f"Config sync successful: {len(data.get('cameras', []))} cameras synced")
            
            jwt_secret = data.get("kong_jwt_secret")
            if jwt_secret:
                # In a full implementation, we would write this secret to a local auth server
                # or inject it into MediaMTX config so it can validate the JWTs locally.
                # MediaMTX doesn't validate JWTs natively without an authHTTPAddress.
                log.info("Received JWT secret for edge stream validation.")
                
            # In a full implementation, update local SQLite DB here and configure MediaMTX
        except Exception as e:
            log.error(f"Failed to sync config: {e}")
            
        await asyncio.sleep(300) # Sync every 5 minutes
