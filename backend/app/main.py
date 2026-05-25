from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import engine, Base, async_session
from app.core.cache import cache
from app.api.v1.router import router as v1_router
from app.services.notification.scheduler import start_scheduler, shutdown_scheduler
from app.data.seed import seed_teams


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables in dev mode
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed dev data
    async with async_session() as db:
        await seed_teams(db)
        await db.commit()

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
