"""Dated automatic backups: create, list and prune files in BACKUP_DIR."""
import logging
import os
import re
import threading
from datetime import datetime
from typing import Dict, List, Optional

from .timeutil import utcnow_naive

log = logging.getLogger("backups")

FILENAME_RE = re.compile(r"^backup-(\d{8})-(\d{6})\.json$")
_lock = threading.Lock()


def enabled() -> bool:
    return os.environ.get("BACKUP_ENABLED", "1") != "0"


def hour_utc() -> int:
    try:
        return min(23, max(0, int(os.environ.get("BACKUP_HOUR_UTC", "3"))))
    except ValueError:
        return 3


def keep_count() -> int:
    try:
        return max(1, int(os.environ.get("BACKUP_KEEP", "14")))
    except ValueError:
        return 14


def backup_dir() -> str:
    import database
    return os.environ.get("BACKUP_DIR") or os.path.join(
        os.path.dirname(os.path.abspath(database.DB_PATH)), "backups")


def _info(directory: str, filename: str) -> Optional[Dict]:
    m = FILENAME_RE.match(filename)
    if not m:
        return None
    path = os.path.join(directory, filename)
    try:
        st = os.stat(path)
        created = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
    except (OSError, ValueError):
        return None
    return {"filename": filename, "size_bytes": st.st_size,
            "created_at": created.isoformat() + "Z"}


def list_backups(directory: Optional[str] = None) -> List[Dict]:
    directory = directory or backup_dir()
    if not os.path.isdir(directory):
        return []
    items = [i for i in (_info(directory, f) for f in os.listdir(directory)) if i]
    return sorted(items, key=lambda i: i["filename"], reverse=True)


def prune(directory: Optional[str] = None, keep: Optional[int] = None) -> List[str]:
    """Delete oldest matching backups beyond ``keep``. Returns removed filenames."""
    directory = directory or backup_dir()
    keep = keep if keep is not None else keep_count()
    removed = []
    for item in list_backups(directory)[keep:]:
        try:
            os.unlink(os.path.join(directory, item["filename"]))
            removed.append(item["filename"])
        except OSError as e:
            log.warning("Could not prune %s: %s", item["filename"], e)
    return removed


def create_backup(directory: Optional[str] = None) -> Dict:
    """Write a dated backup, prune old ones, return its info dict."""
    import backup
    from database import SessionLocal
    directory = directory or backup_dir()
    with _lock:
        os.makedirs(directory, exist_ok=True)
        name = f"backup-{utcnow_naive().strftime('%Y%m%d-%H%M%S')}.json"
        db = SessionLocal()
        try:
            backup.write_backup(db, os.path.join(directory, name))
        finally:
            db.close()
        prune(directory)
        return _info(directory, name)


def last_backup_age_hours(directory: Optional[str] = None) -> Optional[float]:
    items = list_backups(directory)
    if not items:
        return None
    dt = datetime.strptime(items[0]["created_at"][:-1], "%Y-%m-%dT%H:%M:%S")
    return (utcnow_naive() - dt).total_seconds() / 3600
