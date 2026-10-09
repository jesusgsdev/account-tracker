"""In-process price cache (15 min TTL)."""
from datetime import timedelta
from typing import Any, Dict, Optional

from .timeutil import utcnow_naive

CACHE_TTL = 900   # seconds — generous to avoid rate limits
_price_cache: Dict[str, Dict[str, Any]] = {}


def cache_get(key: str) -> Optional[Dict[str, Any]]:
    entry = _price_cache.get(key.upper())
    if entry and utcnow_naive() - entry["fetched_at"] < timedelta(seconds=CACHE_TTL):
        return entry
    return None


def cache_set(key: str, data: Dict[str, Any]) -> None:
    _price_cache[key.upper()] = {**data, "fetched_at": utcnow_naive()}
