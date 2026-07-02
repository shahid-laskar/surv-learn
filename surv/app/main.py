import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    cameras, streams, recordings, motion, health,
    auth, stream_auth,
    organizations, customers, roles, audit, camera_groups,
    bsnl,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Sarvanetra API starting up")
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
    allow_origins=["*"],   # tightened in Phase 11
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(bsnl.router,           prefix="") # Note: /api/v1/bsnl prefix is in the router itself


@app.get("/health", tags=["health"])
async def root_health():
    return {"status": "ok", "service": "sarvanetra-api", "version": "2.0.0"}
