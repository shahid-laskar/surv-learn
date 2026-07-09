"""Authenticate edge-agent fleet API calls via per-site enrollment token."""

import secrets

from fastapi import Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.nvr import NvrNode


async def verify_site_token(
    site_code: str,
    db: AsyncSession,
    x_site_token: str | None = Header(None, alias="X-Site-Token"),
) -> NvrNode:
    if not x_site_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Site-Token header",
        )

    node = await db.scalar(select(NvrNode).where(NvrNode.site_code == site_code))
    if not node or not node.site_enrollment_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid site credentials",
        )

    if not secrets.compare_digest(x_site_token, node.site_enrollment_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid site credentials",
        )
    return node


async def verify_site_token_body(
    site_code: str,
    db: AsyncSession,
    x_site_token: str | None = Header(None, alias="X-Site-Token"),
) -> NvrNode:
    """Same as verify_site_token but site_code comes from request body field."""
    return await verify_site_token(site_code, db, x_site_token)
