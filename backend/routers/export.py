"""CSV exports and JSON backups. No endpoint accepts a filename."""
import csv
import io
import json
from typing import Iterable, Iterator, List, Optional, Sequence

from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

import backup as backup_mod
from database import get_db
from models import Account, AuditLog, Property
from services import backups
from services import utcnow_naive
from timeutil import to_utc_iso

router = APIRouter(prefix="/api/export", tags=["export"])

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def safe_text(value) -> str:
    """Text cell: neutralise spreadsheet formula injection with a leading quote."""
    if value is None:
        return ""
    s = str(value)
    return "'" + s if s.startswith(_FORMULA_PREFIXES) else s


def _iso(dt) -> str:
    return to_utc_iso(dt) if dt else ""


def _num(v):
    return "" if v is None else v


def _csv_response(filename_stem: str, header: Sequence[str], rows: List[Sequence]) -> StreamingResponse:
    def gen() -> Iterator[str]:
        buf = io.StringIO()
        w = csv.writer(buf, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
        w.writerow(header)
        yield buf.getvalue()
        for row in rows:
            buf.seek(0); buf.truncate()
            w.writerow(row)
            yield buf.getvalue()

    fname = f"{filename_stem}-{utcnow_naive().strftime('%Y-%m-%d')}.csv"
    return StreamingResponse(
        gen(), media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'})


@router.get("/accounts.csv")
def accounts_csv(db: Session = Depends(get_db)):
    rows = [
        [a.id, safe_text(a.name), safe_text(a.account_type), safe_text(a.category), safe_text(a.provider),
         _num(a.current_value), _num(a.initial_investment), 1 if a.is_active else 0, _iso(a.updated_at)]
        for a in db.query(Account).order_by(Account.id).all()
    ]
    return _csv_response("accounts", ["id", "name", "type", "category", "provider", "current_value",
                                      "initial_investment", "is_active", "updated_at"], rows)


@router.get("/audit.csv")
def audit_csv(account_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    q = db.query(AuditLog, Account.name).join(Account, Account.id == AuditLog.account_id)
    if account_id is not None:
        q = q.filter(AuditLog.account_id == account_id)
    rows = [
        [l.id, l.account_id, safe_text(name), l.previous_value, l.new_value, l.change_amount,
         _num(l.change_percent), safe_text(l.note), _iso(l.recorded_at)]
        for l, name in q.order_by(AuditLog.recorded_at, AuditLog.id).all()
    ]
    return _csv_response("audit", ["id", "account_id", "account_name", "previous_value", "new_value",
                                   "change_amount", "change_percent", "note", "recorded_at"], rows)


@router.get("/properties.csv")
def properties_csv(db: Session = Depends(get_db)):
    rows = []
    for p in db.query(Property).order_by(Property.id).all():
        base = [p.id, safe_text(p.name), safe_text(p.property_address), _num(p.original_price),
                p.property_value, p.ownership_percent, _iso(p.purchase_date), 1 if p.is_active else 0]
        parts = sorted(p.mortgage_parts, key=lambda m: m.id)
        if not parts:
            rows.append(base + [""] * 9)
        for m in parts:
            rows.append(base + [m.id, safe_text(m.name), safe_text(m.lender), m.outstanding_balance,
                                _num(m.interest_rate), safe_text(m.mortgage_type), _num(m.term_years),
                                _num(m.term_months), _num(m.monthly_payment)])
    return _csv_response("properties", [
        "property_id", "property_name", "address", "original_price", "property_value",
        "ownership_percent", "purchase_date", "is_active",
        "part_id", "part_name", "lender", "outstanding_balance", "interest_rate", "mortgage_type",
        "term_years", "term_months", "monthly_payment"], rows)


@router.get("/backup.json")
def backup_json(db: Session = Depends(get_db)):
    body = json.dumps(backup_mod.build_backup_data(db), default=backup_mod.serialize_datetime, indent=2)
    fname = f"backup-{utcnow_naive().strftime('%Y%m%d-%H%M%S')}.json"
    return Response(body, media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="{fname}"'})


@router.get("/backups")
def list_backups():
    return backups.list_backups()


@router.post("/backups/run")
async def run_backup_now():
    return await run_in_threadpool(backups.create_backup)
