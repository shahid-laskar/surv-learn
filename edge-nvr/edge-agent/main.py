import asyncio
import logging
import os

from backup_uploader import backup_loop
from config_sync import config_sync_loop
from edge_db import init_db
from heartbeat import heartbeat_loop
from local_retention import retention_loop
from motion_loop import motion_loop
from motion_sync import motion_sync_loop
from status_loop import status_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("edge-agent")


async def main() -> None:
    init_db()
    site_code = os.environ.get("SITE_CODE", "UNKNOWN_SITE")
    hub_url = os.environ.get("HUB_API_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")

    if not os.environ.get("SITE_TOKEN"):
        log.warning("SITE_TOKEN not set — hub fleet API calls will fail until configured")

    log.info("Starting edge-agent site=%s hub=%s", site_code, hub_url)

    await asyncio.gather(
        heartbeat_loop(site_code, hub_url),
        config_sync_loop(site_code, hub_url),
        motion_loop(),
        motion_sync_loop(site_code, hub_url),
        status_loop(),
        backup_loop(site_code, hub_url),
        retention_loop(),
    )


if __name__ == "__main__":
    asyncio.run(main())
