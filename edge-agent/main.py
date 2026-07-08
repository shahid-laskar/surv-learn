import asyncio
import logging
import os
from heartbeat import heartbeat_loop
from config_sync import config_sync_loop
from motion_loop import motion_loop
from status_loop import status_loop
from backup_uploader import backup_loop
from local_retention import retention_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
log = logging.getLogger("edge-agent")

async def main():
    log.info("Starting edge-agent...")
    site_code = os.environ.get("SITE_CODE", "UNKNOWN_SITE")
    hub_url = os.environ.get("HUB_API_URL", "http://100.64.0.1:8000/api/v1")
    
    log.info(f"Site Code: {site_code}")
    log.info(f"Hub API URL: {hub_url}")
    
    # Run all loops concurrently
    await asyncio.gather(
        heartbeat_loop(site_code, hub_url),
        config_sync_loop(site_code, hub_url),
        motion_loop(),
        status_loop(),
        backup_loop(site_code, hub_url),
        retention_loop(),
    )

if __name__ == "__main__":
    asyncio.run(main())
