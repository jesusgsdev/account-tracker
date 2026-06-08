from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from models import Account, AuditLog, Property, MortgagePart, PropertyValueAuditLog, MortgagePartAuditLog
from schemas import (
    DashboardSummary, CategorySummary, MortgageSummary,
    HistoryPoint, DashboardHistory,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

CATEGORIES = ["INVESTMENTS", "RETIREMENT", "SAVINGS"]


def _compute_mortgage_equity(properties: list) -> float:
    """Sum of (property_value - total_outstanding_balance) * ownership_percent/100."""
    total_equity = 0.0
    for p in properties:
        total_out = sum(pt.outstanding_balance for pt in p.mortgage_parts if pt.is_active)
        equity = (p.property_value - total_out) * (p.ownership_percent / 100.0)
        total_equity += equity
    return total_equity


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db)):
    accounts = db.query(Account).filter(Account.is_active == True).all()
    properties = db.query(Property).filter(Property.is_active == True).all()

    accounts_total = sum(a.current_value for a in accounts)
    mortgage_equity = _compute_mortgage_equity(properties)
    total_value = accounts_total + mortgage_equity

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
        cat_total = sum(a.current_value for a in cat_accounts)

        last_change = None
        if cat_accounts:
            recent_logs = (
                db.query(AuditLog)
                .filter(AuditLog.account_id.in_([a.id for a in cat_accounts]))
                .order_by(desc(AuditLog.recorded_at))
                .limit(5)
                .all()
            )
            if recent_logs:
                total_change = sum(l.change_amount for l in recent_logs)
                prev_total = cat_total - total_change
                last_change = ((total_change / prev_total) * 100) if prev_total != 0 else None

        categories.append(CategorySummary(
            category=cat,
            total_value=cat_total,
            account_count=len(cat_accounts),
            last_change_percent=last_change,
        ))

    # Mortgage summary
    mort_summary = None
    if properties:
        pv_share = sum(p.property_value * (p.ownership_percent / 100.0) for p in properties)
        # Sum outstanding share for all active parts of all active properties
        ob_share = sum(
            sum(pt.outstanding_balance for pt in p.mortgage_parts if pt.is_active) * (p.ownership_percent / 100.0)
            for p in properties
        )
        mort_summary = MortgageSummary(
            total_property_value_share=pv_share,
            total_outstanding_share=ob_share,
            total_equity=mortgage_equity,
            mortgage_count=len(properties),
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


@router.get("/history", response_model=DashboardHistory)
def get_history(
    days: int = Query(default=365, description="Number of days of history"),
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Time-series of total portfolio value (accounts + mortgage equity) from the audit logs.
    Mortgage equity is included unless a category filter is specified.
    """
    since = datetime.utcnow() - timedelta(days=days)
    include_mortgages = category is None

    # ── Account history ────────────────────────────────────────────────────
    accounts = db.query(Account).filter(Account.is_active == True).all()
    if category:
        accounts = [a for a in accounts if a.category == category.upper()]

    if not accounts and not include_mortgages:
        return DashboardHistory(points=[])

    account_ids = [a.id for a in accounts]

    account_logs = (
        db.query(AuditLog)
        .filter(AuditLog.account_id.in_(account_ids), AuditLog.recorded_at >= since)
        .order_by(AuditLog.recorded_at)
        .all()
    ) if account_ids else []

    # Seed account values at start of window
    account_values: dict[int, float] = {}
    for account in accounts:
        pre = (
            db.query(AuditLog)
            .filter(AuditLog.account_id == account.id, AuditLog.recorded_at < since)
            .order_by(desc(AuditLog.recorded_at))
            .first()
        )
        account_values[account.id] = pre.new_value if pre else 0.0

    # ── Mortgage / Property history ────────────────────────────────────────
    property_values: dict[int, float] = {}
    property_ownership: dict[int, float] = {}
    part_balances: dict[int, float] = {}
    part_to_property: dict[int, int] = {}
    
    prop_logs: list = []
    part_logs: list = []

    if include_mortgages:
        properties = db.query(Property).filter(Property.is_active == True).all()
        for p in properties:
            # Seed property value
            pre_val_log = (
                db.query(PropertyValueAuditLog)
                .filter(PropertyValueAuditLog.property_id == p.id, PropertyValueAuditLog.recorded_at < since)
                .order_by(desc(PropertyValueAuditLog.recorded_at))
                .first()
            )
            property_values[p.id] = pre_val_log.new_value if pre_val_log else p.property_value
            property_ownership[p.id] = p.ownership_percent
            
            # Seed mortgage parts
            for pt in p.mortgage_parts:
                if pt.is_active:
                    pre_bal_log = (
                        db.query(MortgagePartAuditLog)
                        .filter(MortgagePartAuditLog.part_id == pt.id, MortgagePartAuditLog.recorded_at < since)
                        .order_by(desc(MortgagePartAuditLog.recorded_at))
                        .first()
                    )
                    part_balances[pt.id] = pre_bal_log.new_value if pre_bal_log else pt.outstanding_balance
                    part_to_property[pt.id] = p.id

        prop_ids = [p.id for p in properties]
        if prop_ids:
            prop_logs = (
                db.query(PropertyValueAuditLog)
                .filter(PropertyValueAuditLog.property_id.in_(prop_ids), PropertyValueAuditLog.recorded_at >= since)
                .order_by(PropertyValueAuditLog.recorded_at)
                .all()
            )
            
            part_ids = list(part_balances.keys())
            if part_ids:
                part_logs = (
                    db.query(MortgagePartAuditLog)
                    .filter(MortgagePartAuditLog.part_id.in_(part_ids), MortgagePartAuditLog.recorded_at >= since)
                    .order_by(MortgagePartAuditLog.recorded_at)
                    .all()
                )

    def current_mortgage_equity() -> float:
        total_eq = 0.0
        for pid, pval in property_values.items():
            own_pct = property_ownership.get(pid, 100.0) / 100.0
            prop_parts_bal = sum(bal for ptid, bal in part_balances.items() if part_to_property.get(ptid) == pid)
            total_eq += (pval - prop_parts_bal) * own_pct
        return total_eq

    # ── Merge and build time series ────────────────────────────────────────
    events: list[tuple[datetime, str, object]] = []
    for l in account_logs:
        events.append((l.recorded_at, "account", l))
    for l in prop_logs:
        events.append((l.recorded_at, "property_val", l))
    for l in part_logs:
        events.append((l.recorded_at, "part_bal", l))
        
    events.sort(key=lambda e: e[0])

    if not events:
        total = sum(account_values.values()) + current_mortgage_equity()
        return DashboardHistory(points=[HistoryPoint(date=datetime.utcnow(), total_value=total)])

    points: List[HistoryPoint] = []
    for recorded_at, kind, log in events:
        if kind == "account":
            account_values[log.account_id] = log.new_value
        elif kind == "property_val":
            property_values[log.property_id] = log.new_value
        elif kind == "part_bal":
            part_balances[log.part_id] = log.new_value

        total = sum(account_values.values()) + current_mortgage_equity()
        points.append(HistoryPoint(date=recorded_at, total_value=total, category=category))

    return DashboardHistory(points=points)
