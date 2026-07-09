import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
log = logging.getLogger("local_retention")

async def retention_loop():
    while True:
        # In a real implementation, this cleans up old recordings from local SQLite/FS
        log.debug("Retention loop running...")
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(retention_loop())
