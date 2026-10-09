from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from timeutil import utcnow
from services.money import round_money, money_sum
from models import Account, AuditLog, Property, MortgagePart, PropertyValueAuditLog, MortgagePartAuditLog
from schemas import (
    DashboardSummary, CategorySummary, MortgageSummary,
    HistoryPoint, DashboardHistory,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

CATEGORIES = ["INVESTMENTS", "RETIREMENT", "SAVINGS"]


def _property_figures(p) -> dict:
    """Per-property money figures (penny-exact): value/outstanding raw and share, equity."""
    own = Decimal(repr(float(p.ownership_percent))) / 100
    value = Decimal(repr(float(p.property_value)))
    out = sum((Decimal(repr(float(pt.outstanding_balance))) for pt in p.mortgage_parts if pt.is_active), Decimal(0))
    return {
        "value_raw": value, "out_raw": out,
        "value_share": value * own, "out_share": out * own,
        "equity": (value - out) * own,
    }


def _compute_mortgage_equity(properties: list) -> float:
    """Sum of (property_value - total_outstanding_balance) * ownership_percent/100."""
    return round_money(sum((_property_figures(p)["equity"] for p in properties), Decimal(0)))


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db)):
    accounts = db.query(Account).filter(Account.is_active == True).all()
    properties = db.query(Property).filter(Property.is_active == True).all()

    figs = [_property_figures(p) for p in properties]  # single pass over properties/parts
    accounts_total = money_sum(a.current_value for a in accounts)
    mortgage_equity = round_money(sum((f["equity"] for f in figs), Decimal(0)))
    total_value = round_money(Decimal(repr(accounts_total)) + Decimal(repr(mortgage_equity)))

    last_updated = max(
        (a.updated_at for a in accounts),
        default=None
    ) if accounts else None
    
    # Check if properties have more recent updates
    if properties:
        prop_last_updated = max(p.updated_at for p in properties)
        if last_updated is None or prop_last_updated > last_updated:
            last_updated = prop_last_updated

    categories = []
    for cat in CATEGORIES:
        cat_accounts = [a for a in accounts if a.category == cat]
        cat_total = money_sum(a.current_value for a in cat_accounts)

        last_change = None
        if cat_accounts:
            total_invested = money_sum(
                a.initial_investment if a.initial_investment is not None else a.current_value
                for a in cat_accounts
            )
            if total_invested > 0:
                last_change = ((cat_total - total_invested) / total_invested) * 100

        categories.append(CategorySummary(
            category=cat,
            total_value=cat_total,
            account_count=len(cat_accounts),
            last_change_percent=last_change,
        ))

    # Mortgage summary
    mort_summary = None
    if properties:
        def tot(key):
            return round_money(sum((f[key] for f in figs), Decimal(0)))
        pv_share, ob_share = tot("value_share"), tot("out_share")
        pv_raw, ob_raw = tot("value_raw"), tot("out_raw")
        mort_summary = MortgageSummary(
            total_property_value_share=pv_share,
            total_outstanding_share=ob_share,
            total_equity=mortgage_equity,
            mortgage_count=len(properties),
            total_property_value_raw=pv_raw,
            total_outstanding_raw=ob_raw,
        )

    return DashboardSummary(
        total_value=total_value,
        accounts_total=accounts_total,
        mortgage_equity=mortgage_equity,
        categories=categories,
        account_count=len(accounts),
        mortgage_summary=mort_summary,
        last_updated=last_updated,
    )


def _seed(logs_by_id: dict, pre_by_id: dict, entity_id: int, fallback: float) -> float:
    """Value of an entity at the start of the history window.

    1. Last log before the window -> its new_value.
    2. Else the earliest in-window log's previous_value (the value that held
       just before the first recorded change; 0 for the "Initial value" log, so
       entities created inside the window correctly start at 0).
    3. Else (no logs at all) -> the current value; nothing ever changed.
    """
    if entity_id in pre_by_id:
        return pre_by_id[entity_id].new_value
    if entity_id in logs_by_id:
        return logs_by_id[entity_id][0].previous_value
    return fallback


def _group(logs: list, key: str) -> dict:
    out: dict = {}
    for l in logs:  # logs are already ordered by recorded_at
        out.setdefault(getattr(l, key), []).append(l)
    return out


def _last_before(db: Session, model, key_col, ids: list, since: datetime) -> dict:
    """Latest log strictly before ``since`` for each id."""
    if not ids:
        return {}
    rows = (
        db.query(model)
        .filter(key_col.in_(ids), model.recorded_at < since)
        .order_by(model.recorded_at, model.id)
        .all()
    )
    out: dict = {}
    for r in rows:  # ascending, so later rows overwrite earlier ones
        out[getattr(r, key_col.key)] = r
    return out


@router.get("/history", response_model=DashboardHistory)
def get_history(
    days: int = Query(default=365, description="Number of days of history"),
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Time-series of total portfolio value (accounts + mortgage equity) from the audit logs.
    Mortgage equity is included unless a category filter is specified.

    Soft-deleted items (is_active = False):
      History is NOT rewritten retroactively. An inactive account/property/part
      still contributes to the series until its deletion time, which we take to
      be its ``updated_at`` (delete sets it; value changes on deleted items are
      refused, so it is not touched afterwards). From that moment its value
      counts as 0. Items deleted before the window start are skipped entirely.
      A deleted property removes its whole equity (its parts included); a
      deleted part alone removes just its balance (equity rises).

    Seeding: see ``_seed`` - never falls back to the CURRENT value when a log
    exists, so history is not rewritten with today's numbers.
    """
    since = utcnow() - timedelta(days=days)
    include_mortgages = category is None

    # ── Accounts (active, plus those deleted inside/after the window start) ──
    accounts = db.query(Account).all()
    if category:
        accounts = [a for a in accounts if a.category == category.upper()]
    accounts = [a for a in accounts if a.is_active or a.updated_at >= since]

    if not accounts and not include_mortgages:
        return DashboardHistory(points=[])

    account_ids = [a.id for a in accounts]
    account_logs = (
        db.query(AuditLog)
        .filter(AuditLog.account_id.in_(account_ids), AuditLog.recorded_at >= since)
        .order_by(AuditLog.recorded_at, AuditLog.id)
        .all()
    ) if account_ids else []
    acc_by_id = _group(account_logs, "account_id")
    acc_pre = _last_before(db, AuditLog, AuditLog.account_id, account_ids, since)

    account_values: dict[int, float] = {
        a.id: _seed(acc_by_id, acc_pre, a.id, a.current_value) for a in accounts
    }

    # ── Properties / mortgage parts ────────────────────────────────────────
    property_values: dict[int, float] = {}
    property_ownership: dict[int, float] = {}
    part_balances: dict[int, float] = {}
    part_to_property: dict[int, int] = {}
    prop_logs: list = []
    part_logs: list = []
    # (time, kind, id) deletion events
    end_events: list[tuple[datetime, str, int]] = []

    if include_mortgages:
        properties = [
            p for p in db.query(Property).all() if p.is_active or p.updated_at >= since
        ]
        prop_ids = [p.id for p in properties]
        # Query parts directly: Property.mortgage_parts only returns ACTIVE parts.
        parts = (
            db.query(MortgagePart).filter(MortgagePart.property_id.in_(prop_ids)).all()
        ) if prop_ids else []
        parts = [pt for pt in parts if pt.is_active or pt.updated_at >= since]

        if prop_ids:
            prop_logs = (
                db.query(PropertyValueAuditLog)
                .filter(PropertyValueAuditLog.property_id.in_(prop_ids),
                        PropertyValueAuditLog.recorded_at >= since)
                .order_by(PropertyValueAuditLog.recorded_at, PropertyValueAuditLog.id)
                .all()
            )
        part_ids = [pt.id for pt in parts]
        if part_ids:
            part_logs = (
                db.query(MortgagePartAuditLog)
                .filter(MortgagePartAuditLog.part_id.in_(part_ids),
                        MortgagePartAuditLog.recorded_at >= since)
                .order_by(MortgagePartAuditLog.recorded_at, MortgagePartAuditLog.id)
                .all()
            )
        prop_by_id = _group(prop_logs, "property_id")
        part_by_id = _group(part_logs, "part_id")
        prop_pre = _last_before(db, PropertyValueAuditLog, PropertyValueAuditLog.property_id, prop_ids, since)
        part_pre = _last_before(db, MortgagePartAuditLog, MortgagePartAuditLog.part_id, part_ids, since)

        for p in properties:
            property_values[p.id] = _seed(prop_by_id, prop_pre, p.id, p.property_value)
            property_ownership[p.id] = p.ownership_percent
            if not p.is_active:
                end_events.append((p.updated_at, "property_end", p.id))
        for pt in parts:
            part_balances[pt.id] = _seed(part_by_id, part_pre, pt.id, pt.outstanding_balance)
            part_to_property[pt.id] = pt.property_id
            if not pt.is_active:
                end_events.append((pt.updated_at, "part_end", pt.id))

    for a in accounts:
        if not a.is_active:
            end_events.append((a.updated_at, "account_end", a.id))

    def current_mortgage_equity() -> float:
        total_eq = 0.0
        for pid, pval in property_values.items():
            own_pct = property_ownership.get(pid, 100.0) / 100.0
            prop_parts_bal = sum(bal for ptid, bal in part_balances.items() if part_to_property.get(ptid) == pid)
            total_eq += (pval - prop_parts_bal) * own_pct
        return total_eq

    # ── Merge and build time series ────────────────────────────────────────
    # Same-timestamp ties: value logs first, deletions last.
    events: list[tuple[datetime, int, str, object]] = []
    for l in account_logs:
        events.append((l.recorded_at, 0, "account", l))
    for l in prop_logs:
        events.append((l.recorded_at, 0, "property_val", l))
    for l in part_logs:
        events.append((l.recorded_at, 0, "part_bal", l))
    for t, kind, eid in end_events:
        if t >= since:
            events.append((t, 1, kind, eid))
    events.sort(key=lambda e: (e[0], e[1]))

    if not events:
        total = round_money(money_sum(account_values.values()) + current_mortgage_equity())
        return DashboardHistory(points=[HistoryPoint(date=utcnow(), total_value=total, category=category)])

    points: List[HistoryPoint] = []
    for recorded_at, _, kind, obj in events:
        if kind == "account":
            account_values[obj.account_id] = obj.new_value
        elif kind == "property_val":
            property_values[obj.property_id] = obj.new_value
        elif kind == "part_bal":
            part_balances[obj.part_id] = obj.new_value
        elif kind == "account_end":
            account_values[obj] = 0.0
        elif kind == "property_end":
            property_values.pop(obj, None)
            property_ownership.pop(obj, None)
        elif kind == "part_end":
            part_balances.pop(obj, None)

        total = round_money(money_sum(account_values.values()) + current_mortgage_equity())
        points.append(HistoryPoint(date=recorded_at, total_value=total, category=category))

    return DashboardHistory(points=points)
