"""HTTP client helpers for hub fleet API calls."""

from __future__ import annotations

import os
from typing import Any

import httpx

SITE_TOKEN = os.environ.get("SITE_TOKEN", "")


def fleet_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    if SITE_TOKEN:
        headers["X-Site-Token"] = SITE_TOKEN
    return headers


async def hub_get(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    resp = await client.get(url, headers=fleet_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


async def hub_post(client: httpx.AsyncClient, url: str, payload: dict) -> dict[str, Any]:
    resp = await client.post(url, json=payload, headers=fleet_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()
