import csv
import io
import json
import os
import sqlite3
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import database
import models
from routers import export as export_router, snapshots as snapshots_router
from services import backups, snapshot
from services.fx import FxRate, FxSnapshot
from support import wipe_db

_app = FastAPI()
_app.include_router(export_router.router)
_app.include_router(snapshots_router.router)


@pytest.fixture()
def c():
    wipe_db()
    snapshot._last_result = None
    snapshot._last_run_at = None
    with TestClient(_app) as cl:
        yield cl


def fx_gbp():
    return FxSnapshot({"GBP": FxRate(1.0, "live", None), "USD": FxRate(2.0, "live", None)})


def seed(value=100.0, ticker="AAA.L", price_cached=None):
    db = database.SessionLocal()
    a = models.Account(name="ISA", account_type="isa", category="INVESTMENTS", current_value=value)
    db.add(a); db.flush()
    db.add(models.ShareHolding(account_id=a.id, ticker=ticker, quantity=10, currency="GBP",
                               last_price=price_cached, last_price_currency="GBP" if price_cached else None))
    db.commit()
    aid = a.id
    db.close()
    return aid


def patch(monkeypatch, prices):
    monkeypatch.setattr(snapshot, "fetch_batch_prices", lambda t: prices)
    monkeypatch.setattr(snapshot, "fetch_fx_rates", lambda c: fx_gbp())


def logs():
    db = database.SessionLocal()
    try:
        return db.query(models.AuditLog).all()
    finally:
        db.close()


def test_snapshot_changed_writes_tagged_log(c, monkeypatch):
    aid = seed(100.0)
    patch(monkeypatch, {"AAA.L": {"price": 15.0, "currency": "GBP"}})
    r = c.post("/api/snapshots/run")
    assert r.status_code == 200
    body = r.json()
    assert body["accounts_updated"] == 1 and body["accounts_skipped"] == [] and body["ran_at"].endswith("Z")
    ls = logs()
    assert len(ls) == 1 and ls[0].note.startswith("[auto-snapshot] ") and ls[0].new_value == 150.0
    s = c.get("/api/snapshots/status").json()
    assert s["last_run_at"].endswith("Z") and s["last_result"]["accounts_updated"] == 1
    assert s["hour_utc"] == 21 and s["enabled"] is False


def test_snapshot_unchanged_no_log(c, monkeypatch):
    seed(150.0)
    patch(monkeypatch, {"AAA.L": {"price": 15.0, "currency": "GBP"}})
    assert c.post("/api/snapshots/run").json()["accounts_updated"] == 0
    assert logs() == []


def test_snapshot_unpriced_skipped(c, monkeypatch):
    aid = seed(100.0)
    patch(monkeypatch, {"AAA.L": {"price": None, "error": "x"}})
    r = c.post("/api/snapshots/run").json()
    assert r["accounts_updated"] == 0 and r["accounts_skipped"][0]["account_id"] == aid
    assert logs() == []


def test_snapshot_partial_unpriced_aborts_account(c, monkeypatch):
    aid = seed(100.0)
    db = database.SessionLocal()
    db.add(models.ShareHolding(account_id=aid, ticker="BBB.L", quantity=1, currency="GBP"))
    db.commit(); db.close()
    patch(monkeypatch, {"AAA.L": {"price": 20.0, "currency": "GBP"}, "BBB.L": {"price": None}})
    r = c.post("/api/snapshots/run").json()
    assert r["accounts_updated"] == 0 and "BBB.L" in r["accounts_skipped"][0]["reason"]
    db = database.SessionLocal()
    assert db.get(models.Account, aid).current_value == 100.0
    db.close()


def test_snapshot_409_when_running(c):
    assert snapshot._run_lock.acquire(blocking=False)
    try:
        assert c.post("/api/snapshots/run").status_code == 409
    finally:
        snapshot._run_lock.release()


def test_status_survives_restart_via_audit(c, monkeypatch):
    seed(100.0)
    patch(monkeypatch, {"AAA.L": {"price": 15.0, "currency": "GBP"}})
    c.post("/api/snapshots/run")
    snapshot._last_result = None; snapshot._last_run_at = None
    s = c.get("/api/snapshots/status").json()
    assert s["last_run_at"] is not None and s["last_result"] is None


def test_no_schema_change():
    con = sqlite3.connect(database.DB_PATH)
    tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    con.close()
    assert tables == {"accounts", "audit_log", "share_holdings", "properties", "mortgage_parts",
                      "property_value_audit_log", "mortgage_part_audit_log"}


def test_accounts_csv_and_injection(c):
    db = database.SessionLocal()
    db.add(models.Account(name='=HYPERLINK("x")', account_type="cash", category="CASH",
                          provider="a,b \"q\"", current_value=-5.5))
    db.commit(); db.close()
    r = c.get("/api/export/accounts.csv")
    assert r.headers["content-type"].startswith("text/csv")
    assert 'attachment; filename="accounts-' in r.headers["content-disposition"]
    rows = list(csv.reader(io.StringIO(r.text)))
    assert rows[0][:4] == ["id", "name", "type", "category"]
    assert rows[1][1] == "'=HYPERLINK(\"x\")"
    assert rows[1][4] == 'a,b "q"'
    assert rows[1][5] == "-5.5"          # numeric stays numeric
    assert rows[1][8].endswith("Z")


def test_audit_csv_filter(c):
    db = database.SessionLocal()
    a = models.Account(name="A", account_type="cash", category="CASH", current_value=1)
    b = models.Account(name="B", account_type="cash", category="CASH", current_value=1)
    db.add_all([a, b]); db.flush()
    for x in (a, b):
        db.add(models.AuditLog(account_id=x.id, previous_value=0, new_value=1, change_amount=1, note="+boom"))
    db.commit(); ida = a.id; db.close()
    allrows = list(csv.reader(io.StringIO(c.get("/api/export/audit.csv").text)))
    assert len(allrows) == 3 and allrows[1][7] == "'+boom" and allrows[1][2] == "A"
    one = list(csv.reader(io.StringIO(c.get(f"/api/export/audit.csv?account_id={ida}").text)))
    assert len(one) == 2


def test_properties_csv_flattened(c):
    db = database.SessionLocal()
    p = models.Property(name="Home", property_value=300000)
    db.add(p); db.flush()
    db.add_all([models.MortgagePart(property_id=p.id, name="Fixed", outstanding_balance=1000),
                models.MortgagePart(property_id=p.id, name="Var", outstanding_balance=2000)])
    db.add(models.Property(name="Empty", property_value=1))
    db.commit(); db.close()
    rows = list(csv.reader(io.StringIO(c.get("/api/export/properties.csv").text)))
    assert len(rows) == 4 and rows[1][9] == "Fixed" and rows[2][9] == "Var" and rows[3][8] == ""


def test_backup_json_restorable_format(c):
    db = database.SessionLocal()
    db.add(models.Account(name="A", account_type="cash", category="CASH", current_value=1))
    db.commit(); db.close()
    r = c.get("/api/export/backup.json")
    assert "attachment" in r.headers["content-disposition"]
    data = r.json()
    import backup
    assert set(data) == {n for n, _ in backup.TABLE_SPECS} and data["accounts"][0]["name"] == "A"


def test_backup_run_list_and_prune(c, monkeypatch, tmp_path):
    d = tmp_path / "b"
    d.mkdir()
    monkeypatch.setenv("BACKUP_DIR", str(d))
    monkeypatch.setenv("BACKUP_KEEP", "3")
    (d / "notes.txt").write_text("keep me")
    (d / "backup-bad.json").write_text("{}")
    for i in range(5):
        (d / f"backup-2024010{i + 1}-000000.json").write_text("{}")
    r = c.post("/api/export/backups/run")
    assert r.status_code == 200 and r.json()["created_at"].endswith("Z")
    lst = c.get("/api/export/backups").json()
    assert len(lst) == 3 and lst[0]["filename"] == r.json()["filename"]
    assert [x["filename"] for x in lst] == sorted((x["filename"] for x in lst), reverse=True)
    assert (d / "notes.txt").exists() and (d / "backup-bad.json").exists()
    json.loads((d / lst[0]["filename"]).read_text())
    assert not [f for f in os.listdir(d) if f.endswith(".tmp")]


def test_endpoints_require_auth(client):
    for method, path in [("get", "/api/export/accounts.csv"), ("get", "/api/export/audit.csv"),
                         ("get", "/api/export/properties.csv"), ("get", "/api/export/backup.json"),
                         ("get", "/api/export/backups"), ("post", "/api/export/backups/run"),
                         ("get", "/api/snapshots/status"), ("post", "/api/snapshots/run")]:
        assert getattr(client, method)(path).status_code in (401, 503), path


def test_seconds_until_next_hour():
    from services.scheduler import seconds_until
    now = datetime(2024, 1, 1, 20, 0, 0)
    assert seconds_until(21, now) == 3600
    assert seconds_until(19, now) == 23 * 3600
    assert seconds_until(20, now) == 24 * 3600
