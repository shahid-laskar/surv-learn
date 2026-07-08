import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    cameras, streams, recordings, motion, health,
    auth, stream_auth,
    organizations, customers, roles, audit, camera_groups,
    bsnl, fleet, mobile as mobile_router
)
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger(__name__)


from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.camera import Camera
from app.services.mediamtx_client import mediamtx_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Sarvanetra API starting up")
    
    try:
        # Sync all active cameras with MediaMTX on startup
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Camera).where(Camera.is_active == True))
            cameras = result.scalars().all()
            await mediamtx_client.sync_cameras(cameras)
    except Exception as e:
        log.error(f"Failed to sync cameras with MediaMTX on startup: {e}")

    yield
    log.info("Sarvanetra API shutting down")


app = FastAPI(
    title="Sarvanetra Surveillance API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins.split(","),
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)

# ── Core surveillance endpoints ────────────────────────────────────────────────
app.include_router(health.router,       prefix="/api/v1")
app.include_router(auth.router,         prefix="/api/v1")
app.include_router(stream_auth.router,  prefix="/api/v1")  # MediaMTX webhook — not Kong
app.include_router(cameras.router,      prefix="/api/v1")
app.include_router(streams.router,      prefix="/api/v1")
app.include_router(recordings.router,   prefix="/api/v1")
app.include_router(motion.router,       prefix="/api/v1")

# ── Company hierarchy / multi-tenant endpoints ─────────────────────────────────
app.include_router(organizations.router,  prefix="/api/v1")
app.include_router(customers.router,      prefix="/api/v1")
app.include_router(roles.router,          prefix="/api/v1")
app.include_router(audit.router,          prefix="/api/v1")
app.include_router(camera_groups.router,  prefix="/api/v1")
app.include_router(fleet.router,          prefix="/api/v1")
app.include_router(bsnl.router,           prefix="") # Note: /api/v1/bsnl prefix is in the router itself
app.include_router(mobile_router.router)

@app.get("/health", tags=["health"])
async def root_health():
    return {"status": "ok", "service": "sarvanetra-api", "version": "2.0.0"}
