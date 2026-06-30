import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import cameras, streams, recordings, motion, health

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
    version="1.0.0",
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

app.include_router(health.router,     prefix="/api/v1")
app.include_router(cameras.router,    prefix="/api/v1")
app.include_router(streams.router,    prefix="/api/v1")
app.include_router(recordings.router, prefix="/api/v1")
app.include_router(motion.router,     prefix="/api/v1")


@app.get("/health", tags=["health"])
async def root_health():
    return {"status": "ok", "service": "sarvanetra-api"}