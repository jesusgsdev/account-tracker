"""Auth-free app (accounts/audit/dashboard/property routers only) on the temp DB.

conftest.py sets DB_PATH to a temp file before anything imports database.py.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import database
from database import Base
import models  # noqa: F401  (register tables)
from routers import accounts, audit, dashboard
from routers import property as property_router

_app = FastAPI()
for _r in (accounts.router, audit.router, dashboard.router, property_router.router):
    _app.include_router(_r)


def wipe_db():
    assert "foliotrack-tests-" in database.DB_PATH, "refusing to wipe a non-test DB"
    Base.metadata.create_all(bind=database.engine)
    with database.engine.begin() as conn:
        for t in reversed(Base.metadata.sorted_tables):
            conn.execute(t.delete())


@pytest.fixture()
def api():
    wipe_db()
    with TestClient(_app) as c:
        yield c
