from services.money import round_money, money_sum, money_delta
from timeutil import utcnow, utcnow_naive
from support import api  # noqa: F401


def test_round_money_half_up():
    assert round_money(1.005) == 1.01      # float repr 1.005 -> half-up
    assert round_money(2.675) == 2.68
    assert round_money(0.1 + 0.2) == 0.3
    assert round_money(-1.005) == -1.01


def test_money_sum_no_drift():
    assert money_sum([0.1] * 10) == 1.0
    assert money_sum([0.1, 0.2]) == 0.3


def test_money_delta():
    change, pct = money_delta(100.10, 100.30)
    assert change == 0.2
    assert abs(pct - 0.19980) < 1e-4
    assert money_delta(0, 5) == (5.0, None)


def test_single_utc_impl():
    assert utcnow_naive is utcnow
    assert utcnow().tzinfo is None


def test_summary_equity_reconciles(api):
    pid = api.post("/api/properties", json={
        "name": "H", "property_value": 300000.10, "ownership_percent": 50}).json()["id"]
    for bal in (100000.10, 50000.20):
        r = api.post(f"/api/properties/{pid}/parts", json={"name": "p", "outstanding_balance": bal})
        assert r.status_code == 201, r.text
    for v in (0.1, 0.2):
        api.post("/api/accounts", json={"name": "a", "account_type": "ISA", "category": "SAVINGS", "current_value": v})
    s = api.get("/api/dashboard/summary").json()
    assert s["accounts_total"] == 0.3
    assert s["mortgage_equity"] == 74999.9   # (300000.10-150000.30)*0.5 = 74999.90
    m = s["mortgage_summary"]
    assert m["total_outstanding_raw"] == 150000.3
    assert m["total_property_value_raw"] == 300000.1
    assert s["total_value"] == round(s["accounts_total"] + s["mortgage_equity"], 2)
