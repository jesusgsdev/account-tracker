"""Shared time helpers.

The database stores NAIVE UTC datetimes (kept for compatibility with existing
rows). ``utcnow()`` replaces the deprecated ``datetime.utcnow()`` and returns the
same kind of value. API responses serialise these as ISO-8601 with a trailing
'Z' (see ``UTCDateTime`` in schemas.py) so clients parse them as UTC.
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Current UTC time as a naive datetime (storage format)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_utc_iso(dt: datetime) -> str:
    """ISO-8601 string with trailing 'Z'. Naive values are assumed to be UTC."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.isoformat() + "Z"
