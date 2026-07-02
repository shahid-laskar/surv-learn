import httpx
from app.config import settings


async def get_active_paths() -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.mediamtx_api_url}/v3/paths/list",
                                timeout=5)
        if resp.status_code == 200:
            return resp.json().get("items", [])
    return []


async def is_path_ready(cam_path: str) -> bool:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{settings.mediamtx_api_url}/v3/paths/get/{cam_path}",
                timeout=5,
            )
            return resp.status_code == 200 and resp.json().get("ready", False)
        except Exception:
            return False