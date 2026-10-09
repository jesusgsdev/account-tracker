"""Share-holding valuation + the daily auto-snapshot job.

``value_holdings`` is the single valuation routine used by both
POST /api/shares/{id}/sync and the scheduled snapshot, so they share the same
safety rules: if any holding has no usable price or FX rate the account is
NOT valued (a partial total would record a false drop).
"""
import logging
import os
import threading
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from .fx import FxSnapshot, fetch_fx_rates
from .prices import fetch_batch_prices, infer_currency
from .timeutil import utcnow_naive
from .money import round_money, money_delta, money_sum

log = logging.getLogger("snapshot")

TAG = "[auto-snapshot] "
MIN_CHANGE_GBP = 0.005

_state_lock = threading.Lock()
_run_lock = threading.Lock()
_last_result: Optional[Dict[str, Any]] = None
_last_run_at = None  # naive UTC datetime


class AlreadyRunning(Exception):
    pass


def enabled() -> bool:
    return os.environ.get("SNAPSHOT_ENABLED", "1") != "0"


def hour_utc() -> int:
    try:
        return min(23, max(0, int(os.environ.get("SNAPSHOT_HOUR_UTC", "21"))))
    except ValueError:
        return 21


def iso_z(dt) -> Optional[str]:
    return dt.isoformat() + "Z" if dt else None


def fx_for_holdings(holdings) -> FxSnapshot:
    ccys = {(h.last_price_currency or h.currency or infer_currency(h.ticker)) for h in holdings}
    ccys |= {infer_currency(h.ticker) for h in holdings}
    return fetch_fx_rates(ccys)


def value_holdings(holdings, prices: Dict[str, Dict[str, Any]], fx: FxSnapshot) -> Dict[str, Any]:
    """Value holdings in GBP. Returns total_gbp, tickers_synced, stale_tickers, unpriced, live_fetches."""
    parts: List[float] = []
    synced: List[str] = []
    stale: List[str] = []
    unpriced: List[str] = []
    live_fetches = sum(1 for h in holdings if prices.get(h.ticker.upper(), {}).get("price") is not None)
    for h in holdings:
        info = prices.get(h.ticker.upper(), {})
        live_p = info.get("price")
        if live_p is not None:
            price, currency = live_p, info.get("currency") or h.currency or infer_currency(h.ticker)
        elif h.last_price is not None:
            price = h.last_price
            currency = h.last_price_currency or info.get("currency") or h.currency or infer_currency(h.ticker)
            stale.append(h.ticker)
        else:
            unpriced.append(h.ticker)
            continue
        value_gbp = fx.to_gbp(h.quantity * price, currency)
        if value_gbp is None:
            unpriced.append(f"{h.ticker} (no {currency}->GBP rate)")
            continue
        parts.append(value_gbp)
        synced.append(h.ticker)
    return {"total_gbp": money_sum(parts), "tickers_synced": synced, "stale_tickers": stale,
            "unpriced": unpriced, "live_fetches": live_fetches}


def build_note(valuation: Dict[str, Any], fx: FxSnapshot, prefix: str = "Synced from live share prices: ") -> str:
    note = f"{prefix}{', '.join(valuation['tickers_synced'])}"
    if valuation["stale_tickers"]:
        note += f" | stale (stored) prices used for: {', '.join(valuation['stale_tickers'])}"
    flags = fx.flags()
    if flags["gbpusd_rate_is_fallback"]:
        note += " | GBP/USD rate is hard-coded fallback"
    elif flags["gbpusd_rate_is_stale"]:
        note += " | GBP/USD rate is stale"
    return note


def snapshot_accounts(db: Session) -> Dict[str, Any]:
    """Value every active account that has holdings; log changes > 0.005 GBP."""
    from models import Account, AuditLog, ShareHolding

    skipped: List[Dict[str, Any]] = []
    updated = 0
    holdings = (
        db.query(ShareHolding).join(Account, Account.id == ShareHolding.account_id)
        .filter(Account.is_active == True).order_by(ShareHolding.account_id).all()  # noqa: E712
    )
    by_account: Dict[int, list] = {}
    for h in holdings:
        by_account.setdefault(h.account_id, []).append(h)

    if by_account:
        tickers = list({h.ticker.upper() for h in holdings})
        prices = fetch_batch_prices(tickers)
        fx = fx_for_holdings(holdings)
        for account_id, hs in by_account.items():
            account = db.get(Account, account_id)
            try:
                v = value_holdings(hs, prices, fx)
                if v["live_fetches"] == 0:
                    skipped.append({"account_id": account_id, "name": account.name,
                                    "reason": "no live prices available"})
                    continue
                if v["unpriced"]:
                    skipped.append({"account_id": account_id, "name": account.name,
                                    "reason": f"no usable price/FX rate for {', '.join(v['unpriced'])}"})
                    continue
                total = round_money(v["total_gbp"])
                previous = account.current_value
                change, pct = money_delta(previous, total)
                if abs(change) <= MIN_CHANGE_GBP:
                    continue
                now = utcnow_naive()
                db.add(AuditLog(
                    account_id=account.id, previous_value=previous, new_value=total,
                    change_amount=change, change_percent=pct,
                    note=build_note(v, fx, TAG + "Live share prices: "), recorded_at=now))
                account.current_value = total
                account.updated_at = now
                db.commit()
                updated += 1
            except Exception as e:  # one bad account must not stop the others
                db.rollback()
                log.exception("Snapshot failed for account %s", account_id)
                skipped.append({"account_id": account_id, "name": getattr(account, "name", str(account_id)),
                                "reason": f"error: {e}"})
    return {"accounts_updated": updated, "accounts_skipped": skipped}


def run_snapshot() -> Dict[str, Any]:
    """Blocking. Raises AlreadyRunning if a run is in progress."""
    global _last_result, _last_run_at
    from database import SessionLocal
    if not _run_lock.acquire(blocking=False):
        raise AlreadyRunning()
    try:
        db = SessionLocal()
        try:
            result = snapshot_accounts(db)
        finally:
            db.close()
        now = utcnow_naive()
        result["ran_at"] = iso_z(now)
        with _state_lock:
            _last_result, _last_run_at = result, now
        log.info("Snapshot done: %s updated, %s skipped",
                 result["accounts_updated"], len(result["accounts_skipped"]))
        return result
    finally:
        _run_lock.release()


def last_snapshot_at(db: Session):
    """Newest of in-memory last run and newest [auto-snapshot] audit row."""
    from models import AuditLog
    row = (db.query(AuditLog.recorded_at).filter(AuditLog.note.like(TAG + "%"))
           .order_by(AuditLog.recorded_at.desc()).first())
    candidates = [d for d in (row[0] if row else None, _last_run_at) if d]
    return max(candidates) if candidates else None


def status(db: Session) -> Dict[str, Any]:
    with _state_lock:
        result = _last_result
    return {"enabled": enabled(), "hour_utc": hour_utc(),
            "last_run_at": iso_z(last_snapshot_at(db)), "last_result": result}
