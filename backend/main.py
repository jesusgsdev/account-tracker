import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

import auth
from migrations import run_migrations
from routers import accounts, audit, dashboard, export as export_router, snapshots as snapshots_router
from services import backups as backup_svc, snapshot as snapshot_svc
from services.scheduler import daily_job
from routers import property as property_router
from routers import shares as shares_router

logging.basicConfig(level=logging.INFO)

# Creates tables (create_all) and applies idempotent migrations
run_migrations()
auth.warn_if_unconfigured()

def _snapshot_catch_up() -> bool:
    from database import SessionLocal
    from services.timeutil import utcnow_naive
    db = SessionLocal()
    try:
        last = snapshot_svc.last_snapshot_at(db)
    finally:
        db.close()
    return last is None or (utcnow_naive() - last).total_seconds() > 24 * 3600


def _backup_catch_up() -> bool:
    age = backup_svc.last_backup_age_hours()
    return age is None or age > 24


@asynccontextmanager
async def lifespan(_app: FastAPI):
    tasks = []
    if snapshot_svc.enabled():
        tasks.append(asyncio.create_task(daily_job(
            "snapshot", snapshot_svc.hour_utc(), snapshot_svc.run_snapshot, _snapshot_catch_up)))
    if backup_svc.enabled():
        tasks.append(asyncio.create_task(daily_job(
            "backup", backup_svc.hour_utc(), backup_svc.create_backup, _backup_catch_up, startup_delay=5.0)))
    try:
        yield
    finally:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(
    lifespan=lifespan,
    title="UK Account Tracker API",
    description="Local-first financial account tracking for UK residents",
    version="1.0.0",
)

_DEFAULT_CORS = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:4173,http://127.0.0.1:4173"
)
cors_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", _DEFAULT_CORS).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # explicit list (never "*") so credentials are safe
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

protected = [Depends(auth.require_auth)]
app.include_router(auth.router)
app.include_router(accounts.router, dependencies=protected)
app.include_router(audit.router, dependencies=protected)
app.include_router(dashboard.router, dependencies=protected)
app.include_router(property_router.router, dependencies=protected)
app.include_router(shares_router.router, dependencies=protected)
app.include_router(snapshots_router.router, dependencies=protected)
app.include_router(export_router.router, dependencies=protected)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "account-tracker"}
