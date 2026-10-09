"""History reconstruction. Rows are inserted directly so timestamps are controlled."""
from datetime import timedelta

import pytest

import database
from database import Base
from models import (
    Account, AuditLog, Property, MortgagePart, PropertyValueAuditLog, MortgagePartAuditLog,
)
from timeutil import utcnow


from support import api, wipe_db  # noqa: F401


@pytest.fixture()
def client(api):
    return api


@pytest.fixture()
def db(api):
    s = database.SessionLocal()
    yield s
    s.close()


def ago(days):
    return utcnow() - timedelta(days=days)


def acct(db, name, current, active=True, updated=None, cat="SAVINGS"):
    a = Account(name=name, account_type="SAVINGS", category=cat, current_value=current,
                is_active=active, created_at=ago(400), updated_at=updated or utcnow())
    db.add(a)
    db.flush()
    return a


def alog(db, a, prev, new, when):
    db.add(AuditLog(account_id=a.id, previous_value=prev, new_value=new,
                    change_amount=new - prev, recorded_at=when))


def hist(client, **params):
    r = client.get("/api/dashboard/history", params=params)
    assert r.status_code == 200, r.text
    return r.json()["points"]


def values(points):
    return [round(p["total_value"], 2) for p in points]


def test_dates_are_utc_z(client, db):
    a = acct(db, "A", 10)
    alog(db, a, 0, 10, ago(1))
    db.commit()
    assert all(p["date"].endswith("Z") for p in hist(client))


def test_seed_from_pre_window_log(client, db):
    a = acct(db, "A", 300)
    alog(db, a, 0, 100, ago(100))   # before 30d window
    alog(db, a, 100, 300, ago(5))
    db.commit()
    assert values(hist(client, days=30)) == [300.0]
    # window start value was 100; only one event so single point at 300


def test_missing_pre_window_logs_seed_from_previous_value(client, db):
    a = acct(db, "A", 300)
    b = acct(db, "B", 50)
    alog(db, a, 100, 200, ago(10))  # no earlier log: seed must be 100 (not current 300)
    alog(db, a, 200, 300, ago(5))
    alog(db, b, 0, 50, ago(7))
    db.commit()
    # events: A->200 (b=0): 200 ; B->50: 250 ; A->300: 350
    assert values(hist(client, days=30)) == [200.0, 250.0, 350.0]


def test_account_without_logs_uses_current(client, db):
    acct(db, "A", 40)
    b = acct(db, "B", 10)
    alog(db, b, 0, 10, ago(2))
    db.commit()
    assert values(hist(client, days=30)) == [50.0]


def test_deleted_account_counts_until_deletion(client, db):
    keep = acct(db, "keep", 100)
    alog(db, keep, 0, 100, ago(20))
    gone = acct(db, "gone", 500, active=False, updated=ago(5))
    alog(db, gone, 0, 500, ago(15))
    db.commit()
    pts = hist(client, days=30)
    assert values(pts) == [100.0, 600.0, 100.0]


def test_account_deleted_before_window_skipped(client, db):
    keep = acct(db, "keep", 100)
    alog(db, keep, 0, 100, ago(2))
    gone = acct(db, "gone", 500, active=False, updated=ago(60))
    alog(db, gone, 0, 500, ago(70))
    db.commit()
    assert values(hist(client, days=30)) == [100.0]


def test_category_filter(client, db):
    a = acct(db, "A", 10, cat="SAVINGS")
    b = acct(db, "B", 20, cat="INVESTMENTS")
    alog(db, a, 0, 10, ago(3))
    alog(db, b, 0, 20, ago(2))
    db.commit()
    assert values(hist(client, days=30, category="savings")) == [10.0]


def prop(db, value, own=100.0, active=True, updated=None):
    p = Property(name="Home", property_value=value, ownership_percent=own,
                 is_active=active, created_at=ago(400), updated_at=updated or utcnow())
    db.add(p)
    db.flush()
    return p


def part(db, p, bal, active=True, updated=None):
    m = MortgagePart(property_id=p.id, name="Part", outstanding_balance=bal, mortgage_type="REPAYMENT",
                     is_active=active, created_at=ago(400), updated_at=updated or utcnow())
    db.add(m)
    db.flush()
    return m


def test_property_and_part_seed_from_first_in_window_previous_value(client, db):
    p = prop(db, 300000)       # current value
    m = part(db, p, 80000)     # current balance
    db.add(PropertyValueAuditLog(property_id=p.id, previous_value=200000, new_value=300000,
                                 change_amount=100000, recorded_at=ago(10)))
    db.add(MortgagePartAuditLog(part_id=m.id, previous_value=120000, new_value=80000,
                                change_amount=-40000, recorded_at=ago(5)))
    db.commit()
    # After prop log: 300000 - 120000 (seed from previous_value, NOT current 80000)
    assert values(hist(client, days=30)) == [180000.0, 220000.0]


def test_deleted_part_and_property(client, db):
    p = prop(db, 300000)
    m1 = part(db, p, 100000)
    m2 = part(db, p, 50000, active=False, updated=ago(5))
    db.add(PropertyValueAuditLog(property_id=p.id, previous_value=0, new_value=300000,
                                 change_amount=300000, recorded_at=ago(20)))
    db.add(MortgagePartAuditLog(part_id=m1.id, previous_value=0, new_value=100000,
                                change_amount=100000, recorded_at=ago(19)))
    db.add(MortgagePartAuditLog(part_id=m2.id, previous_value=0, new_value=50000,
                                change_amount=50000, recorded_at=ago(18)))
    db.commit()
    # 300000 ; 200000 ; 150000 ; part2 deleted -> 200000
    assert values(hist(client, days=30)) == [300000.0, 200000.0, 150000.0, 200000.0]

    # delete whole property 2 days ago -> equity 0 afterwards
    p.is_active = False
    p.updated_at = ago(2)
    m1.is_active = False
    m1.updated_at = ago(2)
    db.commit()
    assert values(hist(client, days=30))[-1] == 0.0


def test_no_events_single_point(client, db):
    acct(db, "A", 25)
    db.commit()
    pts = hist(client, days=30)
    assert values(pts) == [25.0]
