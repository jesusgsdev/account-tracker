import pytest

import database
from database import Base


from support import api  # noqa: F401


def make_account(api, **kw):
    body = {"name": "ISA", "account_type": "ISA", "category": "INVESTMENTS", "current_value": 100.0}
    body.update(kw)
    r = api.post("/api/accounts", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_create_logs_initial_value_and_z_suffix(api):
    a = make_account(api)
    assert a["created_at"].endswith("Z")
    logs = api.get(f"/api/audit/{a['id']}/history").json()
    assert len(logs) == 1 and logs[0]["new_value"] == 100.0
    assert logs[0]["recorded_at"].endswith("Z")


def test_update_value_writes_audit(api):
    a = make_account(api)
    r = api.patch(f"/api/accounts/{a['id']}/value", json={"new_value": 150.0, "note": "up"})
    assert r.status_code == 200
    log = r.json()
    assert (log["previous_value"], log["new_value"], log["change_amount"]) == (100.0, 150.0, 50.0)
    assert log["change_percent"] == pytest.approx(50.0)
    assert api.get(f"/api/accounts/{a['id']}").json()["current_value"] == 150.0
    assert len(api.get(f"/api/audit/{a['id']}/history").json()) == 2


def test_put_cannot_bypass_audit(api):
    a = make_account(api)
    for field, val in [("current_value", 5), ("is_active", False), ("id", 99), ("created_at", "2000-01-01T00:00:00")]:
        r = api.put(f"/api/accounts/{a['id']}", json={field: val})
        assert r.status_code == 422, field
    got = api.get(f"/api/accounts/{a['id']}").json()
    assert got["current_value"] == 100.0 and got["is_active"] is True
    assert api.put(f"/api/accounts/{a['id']}", json={"name": "Renamed"}).json()["name"] == "Renamed"


def test_put_null_name_ignored(api):
    a = make_account(api)
    r = api.put(f"/api/accounts/{a['id']}", json={"name": None})
    assert r.status_code == 200 and r.json()["name"] == "ISA"


def test_deleted_account_value_update_rejected(api):
    a = make_account(api)
    assert api.delete(f"/api/accounts/{a['id']}").status_code == 204
    assert api.patch(f"/api/accounts/{a['id']}/value", json={"new_value": 1}).status_code == 409


@pytest.mark.parametrize("body", [
    {"name": ""},
    {"name": "   "},
    {"name": "x" * 256},
    {"current_value": -1},
    {"initial_investment": -5},
    {"provider": "p" * 256},
    {"account_type": "NOPE"},
])
def test_account_validation(api, body):
    base = {"name": "A", "account_type": "ISA", "category": "INVESTMENTS", "current_value": 1}
    base.update(body)
    assert api.post("/api/accounts", json=base).status_code == 422


def test_negative_value_update_rejected(api):
    a = make_account(api)
    assert api.patch(f"/api/accounts/{a['id']}/value", json={"new_value": -1}).status_code == 422


def make_property(api, value=300000, own=100.0):
    r = api.post("/api/properties", json={"name": "Home", "property_value": value, "ownership_percent": own})
    assert r.status_code == 201, r.text
    return r.json()


def add_part(api, pid, balance=100000):
    r = api.post(f"/api/properties/{pid}/parts", json={"name": "Fixed", "outstanding_balance": balance})
    assert r.status_code == 201, r.text
    return r.json()


def test_equity(api):
    p = make_property(api, 300000, 50.0)
    add_part(api, p["id"], 100000)
    add_part(api, p["id"], 50000)
    got = api.get(f"/api/properties/{p['id']}").json()
    assert got["total_outstanding"] == 150000
    assert got["equity"] == pytest.approx((300000 - 150000) * 0.5)
    s = api.get("/api/dashboard/summary").json()
    assert s["mortgage_equity"] == pytest.approx(75000)
    assert s["total_value"] == pytest.approx(75000)


def test_property_delete_soft_deletes_parts_and_equity(api):
    p = make_property(api)
    part = add_part(api, p["id"])
    assert api.delete(f"/api/properties/{p['id']}").status_code == 204
    assert api.get("/api/properties").json() == []
    assert api.get("/api/dashboard/summary").json()["mortgage_equity"] == 0
    assert api.patch(f"/api/properties/{p['id']}/value", json={"new_value": 5}).status_code == 409
    assert api.patch(f"/api/properties/parts/{part['id']}/balance", json={"new_balance": 5}).status_code == 409
    assert api.post(f"/api/properties/{p['id']}/parts", json={"name": "x", "outstanding_balance": 1}).status_code == 409


@pytest.mark.parametrize("path,body", [
    ("/api/properties", {"name": "H", "property_value": 10, "ownership_percent": 101}),
    ("/api/properties", {"name": "H", "property_value": 10, "ownership_percent": -1}),
    ("/api/properties", {"name": "", "property_value": 10}),
    ("/api/properties", {"name": "H", "property_value": 0}),
])
def test_property_validation(api, path, body):
    assert api.post(path, json=body).status_code == 422


@pytest.mark.parametrize("extra", [
    {"term_months": 12}, {"term_months": -1}, {"interest_rate": 101}, {"interest_rate": -0.1},
    {"outstanding_balance": -1}, {"monthly_payment": -1}, {"name": ""}, {"term_years": -1},
])
def test_part_validation(api, extra):
    p = make_property(api)
    body = {"name": "P", "outstanding_balance": 10}
    body.update(extra)
    assert api.post(f"/api/properties/{p['id']}/parts", json=body).status_code == 422


def test_part_update_validation(api):
    p = make_property(api)
    part = add_part(api, p["id"])
    assert api.put(f"/api/properties/parts/{part['id']}", json={"interest_rate": 500}).status_code == 422
    assert api.put(f"/api/properties/parts/{part['id']}", json={"mortgage_type": "X"}).status_code == 422
    assert api.put(f"/api/properties/parts/{part['id']}", json={"interest_rate": 4.5}).status_code == 200
