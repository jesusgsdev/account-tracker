from datetime import datetime, timezone


def utcnow_naive() -> datetime:
    """Naive UTC 'now' (replacement for deprecated datetime.utcnow()).

    DB values are stored as naive UTC, so tzinfo is intentionally stripped.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
