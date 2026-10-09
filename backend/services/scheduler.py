"""Background daily jobs (snapshot, backup), started from the FastAPI lifespan."""
import asyncio
import logging
from datetime import timedelta
from typing import Callable, Optional

from .timeutil import utcnow_naive

log = logging.getLogger("scheduler")


def seconds_until(hour_utc: int, now=None) -> float:
    now = now or utcnow_naive()
    target = now.replace(hour=hour_utc, minute=0, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


async def daily_job(name: str, hour_utc: int, job: Callable, catch_up: Optional[Callable[[], bool]] = None,
                    startup_delay: float = 20.0):
    """Run ``job`` (blocking, in a thread) daily at hour_utc. Never raises."""
    try:
        if catch_up is not None:
            await asyncio.sleep(startup_delay)
            if await asyncio.to_thread(catch_up):
                log.info("%s: catch-up run on startup", name)
                await _safe(name, job)
        while True:
            await asyncio.sleep(seconds_until(hour_utc))
            await _safe(name, job)
    except asyncio.CancelledError:
        raise
    except Exception:
        log.exception("%s: scheduler loop crashed", name)


async def _safe(name: str, job: Callable):
    try:
        await asyncio.to_thread(job)
    except Exception:
        log.exception("%s: job failed", name)
