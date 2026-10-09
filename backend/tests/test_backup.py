import json
import os
import subprocess
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SEED = """
from datetime import datetime
from database import SessionLocal, Base, engine
import models
Base.metadata.create_all(bind=engine)
db = SessionLocal()
db.add(models.Account(id=7, name='ISA', account_type='stocks_shares_isa', category='investments',
                      current_value=100.0, created_at=datetime(2024, 1, 2, 3, 4, 5), updated_at=datetime(2024, 1, 2)))
db.flush()
db.add(models.AuditLog(id=3, account_id=7, previous_value=0, new_value=100, change_amount=100,
                       recorded_at=datetime(2024, 1, 2, 3, 4, 5)))
db.add(models.ShareHolding(id=5, account_id=7, ticker='HSBA.L', quantity=10, currency='GBX'))
db.commit()
"""

COUNT = """
from database import SessionLocal
import models
db = SessionLocal()
print(db.query(models.Account).count(), db.query(models.AuditLog).count(),
      db.query(models.ShareHolding).count(), db.query(models.ShareHolding).one().account_id)
"""


def py(code, db):
    env = dict(os.environ, DB_PATH=str(db))
    return subprocess.run([sys.executable, "-c", code], cwd=BACKEND, env=env,
                          capture_output=True, text=True, check=True).stdout.strip()


def backup(*args):
    return subprocess.run([sys.executable, os.path.join(BACKEND, "backup.py"), *args],
                          capture_output=True, text=True)


def test_round_trip(tmp_path):
    src, dst, out = tmp_path / "src.db", tmp_path / "dst.db", tmp_path / "b.json"
    py(SEED, src)
    assert backup("--backup", str(out), "--db", str(src)).returncode == 0
    data = json.loads(out.read_text())
    assert len(data["share_holdings"]) == 1
    assert not [p for p in tmp_path.iterdir() if p.name.endswith(".tmp")]

    r = backup("--restore", str(out), "--db", str(dst))
    assert r.returncode == 0, r.stderr
    assert py(COUNT, dst) == "1 1 1 7"
    # restoring over existing data is idempotent
    assert backup("--restore", str(out), "--db", str(dst)).returncode == 0
    assert py(COUNT, dst) == "1 1 1 7"


def test_bad_restore_keeps_data(tmp_path):
    db, out = tmp_path / "a.db", tmp_path / "b.json"
    py(SEED, db)
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"accounts": [{"id": 1, "bogus": 1}]}))
    assert backup("--restore", str(bad), "--db", str(db)).returncode != 0
    assert backup("--restore", str(tmp_path / "nope.json"), "--db", str(db)).returncode != 0
    # FK failure at insert time must roll back
    bad.write_text(json.dumps({"accounts": [], "share_holdings": [
        {"id": 1, "account_id": 99, "ticker": "X", "quantity": 1,
         "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"}]}))
    assert backup("--restore", str(bad), "--db", str(db)).returncode != 0
    assert py(COUNT, db) == "1 1 1 7"
