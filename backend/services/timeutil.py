"""Re-export of the single UTC helper implementation in backend/timeutil.py."""
from timeutil import utcnow, utcnow_naive

__all__ = ["utcnow", "utcnow_naive"]
