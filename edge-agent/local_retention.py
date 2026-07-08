import asyncio
import logging

log = logging.getLogger("local_retention")

async def retention_loop():
    while True:
        # In a real implementation, this cleans up old recordings from local SQLite/FS
        # log.debug("Retention loop running...")
        await asyncio.sleep(3600)
