import asyncio
import logging
import httpx

log = logging.getLogger("backup_uploader")

async def backup_loop(site_code: str, hub_url: str):
    while True:
        # In a real implementation, this checks for pending backups and uploads to MinIO at hub
        # log.debug("Backup loop running...")
        await asyncio.sleep(60)
