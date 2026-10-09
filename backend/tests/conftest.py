import os
import tempfile

import pytest

# DB_PATH must be set BEFORE the app (and database.py) is imported.
_TMP_DIR = tempfile.mkdtemp(prefix="foliotrack-tests-")
os.environ["DB_PATH"] = os.path.join(_TMP_DIR, "test.db")
os.environ["BACKUP_DIR"] = os.path.join(_TMP_DIR, "backups")
os.environ["SNAPSHOT_ENABLED"] = "0"
os.environ["BACKUP_ENABLED"] = "0"


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as c:
        yield c
