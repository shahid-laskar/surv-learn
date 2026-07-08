import asyncio
import logging

log = logging.getLogger("status_loop")

async def status_loop():
    while True:
        # In a real implementation, this would ping cameras locally
        # log.debug("Status loop running...")
        await asyncio.sleep(15)
