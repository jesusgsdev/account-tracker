"""Daily auto-snapshot status and manual trigger."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from database import get_db
from services import snapshot

router = APIRouter(prefix="/api/snapshots", tags=["snapshots"])


@router.get("/status")
def get_status(db: Session = Depends(get_db)):
    return snapshot.status(db)


@router.post("/run")
async def run_now():
    try:
        return await run_in_threadpool(snapshot.run_snapshot)
    except snapshot.AlreadyRunning:
        raise HTTPException(status_code=409, detail="A snapshot is already running")
