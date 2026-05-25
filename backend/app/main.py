from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import engine
from app.core.cache import cache
from app.api.v1.router import router as v1_router
from app.services.notification.scheduler import start_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await cache.connect()
    start_scheduler()
    yield
    shutdown_scheduler()
    await cache.disconnect()
    await engine.dispose()


app = FastAPI(
    title="FCM AI Butler",
    description="足球主队AI管家 - Backend API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(v1_router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}
