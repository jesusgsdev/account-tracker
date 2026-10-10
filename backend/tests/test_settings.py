from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

import database
from routers import settings as settings_router
from support import wipe_db

_app = FastAPI()
_app.include_router(settings_router.router)

GOOD = {
    "end_year": 2055, "include_other": False, "return_rate_investments": 6.5,
    "contrib_investments": 400, "return_rate_retirement": 5.5, "contrib_retirement": 250, "contrib_retirement_growth": 1.5,
    "inflation_rate": 2.0, "adjust_inflation": True, "birth_year": 1989, "withdrawal_rate": 3.5,
}


@pytest.fixture()
def client():
    wipe_db()
    return TestClient(_app)


def test_forecast_settings_roundtrip(client):
    assert client.get("/api/settings/forecast").json() is None
    assert client.put("/api/settings/forecast", json=GOOD).status_code == 200
    assert client.get("/api/settings/forecast").json() == GOOD
    client.put("/api/settings/forecast", json={**GOOD, "end_year": 2060})
    assert client.get("/api/settings/forecast").json()["end_year"] == 2060


def test_forecast_settings_validation(client):
    assert client.put("/api/settings/forecast", json={**GOOD, "birth_year": 1500}).status_code == 422
    assert client.put("/api/settings/forecast", json={**GOOD, "inflation_rate": -1}).status_code == 422
    bad = dict(GOOD); del bad["end_year"]
    assert client.put("/api/settings/forecast", json=bad).status_code == 422


def test_restore_of_old_backup_keeps_saved_settings(client, tmp_path):
    """Backups made before app_settings existed must not wipe the saved forecast."""
    import json
    import backup
    client.put("/api/settings/forecast", json=GOOD)
    old = tmp_path / "old.json"
    old.write_text(json.dumps({"accounts": []}))   # no app_settings key
    assert backup.run_restore(str(old)) == 0
    assert client.get("/api/settings/forecast").json() == GOOD


def test_old_saved_settings_without_growth_still_load(client):
    """Settings saved before contrib_retirement_growth existed get the default."""
    import json
    from models import AppSetting
    old = {k: v for k, v in GOOD.items() if k != "contrib_retirement_growth"}
    db = database.SessionLocal()
    db.add(AppSetting(key="forecast", value=json.dumps(old)))
    db.commit(); db.close()
    assert client.get("/api/settings/forecast").json()["contrib_retirement_growth"] == 1.0
