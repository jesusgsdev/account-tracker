"""
Share Holdings router — CRUD + live Yahoo Finance prices + account sync.

Key design principles:
  • ALL tickers are fetched in ONE yf.download() call per /live or /all-live
    request, avoiding per-ticker rate limits.
  • Last successfully fetched price is persisted to the DB so stale data
    survives backend restarts and failed refreshes.
  • Results cached in-process for 15 minutes.
"""
from datetime import datetime, timedelta
import os
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Account, AuditLog, ShareHolding
from schemas import (
    ShareHoldingCreate, ShareHoldingUpdate,
    ShareHoldingResponse, LiveHoldingResponse,
    PortfolioLiveResponse,
)

router = APIRouter(prefix="/api/shares", tags=["shares"])

# ── Cache ─────────────────────────────────────────────────────────────────────
CACHE_TTL = 900   # 15 min — generous to avoid rate limits
_price_cache: Dict[str, Dict[str, Any]] = {}


def _cache_get(ticker: str) -> Optional[Dict[str, Any]]:
    entry = _price_cache.get(ticker.upper())
    if entry and datetime.utcnow() - entry["fetched_at"] < timedelta(seconds=CACHE_TTL):
        return entry
    return None


def _cache_set(ticker: str, data: Dict[str, Any]) -> None:
    _price_cache[ticker.upper()] = {**data, "fetched_at": datetime.utcnow()}


# ── Currency inference from ticker suffix ─────────────────────────────────────
_SUFFIX_CURRENCY: Dict[str, str] = {
    ".L":  "GBX",   # London Stock Exchange (pence)
    ".IL": "ILA",   # Tel Aviv
    ".AS": "EUR",   # Amsterdam
    ".PA": "EUR",   # Paris
    ".DE": "EUR",   # Frankfurt / XETRA
    ".MI": "EUR",   # Milan
    ".MC": "EUR",   # Madrid
    ".SW": "CHF",   # Swiss Exchange
    ".HK": "HKD",   # Hong Kong
    ".T":  "JPY",   # Tokyo
    ".AX": "AUD",   # Australia
    ".TO": "CAD",   # Toronto
    ".V":  "CAD",   # TSX Venture
    ".NZ": "NZD",   # New Zealand
}

def _infer_currency(ticker: str) -> str:
    t = ticker.upper()
    if t.startswith("0P") and t.endswith(".L"):
        return "GBP"
    for suffix, ccy in _SUFFIX_CURRENCY.items():
        if t.endswith(suffix.upper()):
            return ccy
    return "USD"


# ── GBP/USD rate ──────────────────────────────────────────────────────────────
RATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gbpusd_rate.json")

def _fetch_gbpusd_rate() -> Optional[float]:
    """Return live GBP→USD rate via a single yf.download() call, with persistent fallback."""
    cached = _cache_get("GBPUSD=X")
    if cached:
        return cached.get("price")
    try:
        import yfinance as yf
        df = yf.download("GBPUSD=X", period="5d", progress=False, auto_adjust=True)
        if not df.empty:
            close_series = df["Close"]
            if hasattr(close_series, "columns"):
                close_series = close_series.iloc[:, 0]
            close_series = close_series.dropna()
            if not close_series.empty:
                rate = float(close_series.iloc[-1])
                _cache_set("GBPUSD=X", {"price": rate, "currency": "USD",
                                         "short_name": "GBP/USD", "day_change_pct": None,
                                         "market_state": None, "error": None})
            try:
                with open(RATE_FILE, "w") as f:
                    json.dump({"rate": rate, "fetched_at": datetime.utcnow().isoformat()}, f)
            except Exception:
                pass
            return rate
    except Exception:
        pass
    
    # Fallback to local file
    if os.path.exists(RATE_FILE):
        try:
            with open(RATE_FILE, "r") as f:
                data = json.load(f)
                rate = data.get("rate")
                if rate:
                    _cache_set("GBPUSD=X", {"price": rate, "currency": "USD",
                                             "short_name": "GBP/USD", "day_change_pct": None,
                                             "market_state": None, "error": "Using persisted rate fallback"})
                    return rate
        except Exception:
            pass
            
    return 1.30  # Hardcoded fallback as last resort


def _to_gbp(value_native: float, currency: str, gbpusd: Optional[float]) -> Optional[float]:
    if currency == "GBP":
        return value_native
    if currency == "GBX":
        return value_native / 100
    if currency == "USD" and gbpusd:
        return value_native / gbpusd
    return None


# ── Batch price fetch — ONE network call for N tickers ────────────────────────
def _fetch_batch_prices(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetch prices for all given tickers in a single yf.download() call.
    Returns dict keyed by UPPERCASE ticker.  Cached tickers are skipped.
    """
    results: Dict[str, Dict[str, Any]] = {}

    uncached: List[str] = []
    for t in tickers:
        hit = _cache_get(t)
        if hit:
            results[t.upper()] = hit
        else:
            uncached.append(t.upper())

    if not uncached:
        return results

    try:
        import yfinance as yf
        joined = " ".join(uncached)
        raw = yf.download(
            tickers=joined,
            period="5d",
            progress=False,
            auto_adjust=True,
        )

        if raw.empty:
            raise ValueError("Empty response from Yahoo Finance")

        for ticker in uncached:
            try:
                close_series = raw["Close"]
                if hasattr(close_series, "columns"):
                    if ticker in close_series.columns:
                        close_series = close_series[ticker]
                    else:
                        close_series = close_series.iloc[:, 0]
                close_series = close_series.dropna()

                if close_series.empty:
                    result: Dict[str, Any] = {
                        "price": None,
                        "currency": _infer_currency(ticker),
                        "short_name": ticker,
                        "day_change_pct": None,
                        "market_state": None,
                        "error": f"No price data for '{ticker}' — is the ticker symbol correct?",
                    }
                else:
                    price = float(close_series.iloc[-1])
                    prev  = float(close_series.iloc[-2]) if len(close_series) >= 2 else None
                    day_chg = ((price - prev) / prev * 100) if prev else None
                    result = {
                        "price": price,
                        "currency": _infer_currency(ticker),
                        "short_name": ticker,
                        "day_change_pct": day_chg,
                        "market_state": None,
                        "error": None,
                    }
            except Exception as exc:
                result = {
                    "price": None, "currency": _infer_currency(ticker),
                    "short_name": ticker, "day_change_pct": None,
                    "market_state": None, "error": str(exc),
                }

            if result.get("price") is not None or (result.get("error") and "is the ticker symbol correct" in result.get("error")):
                _cache_set(ticker, result)
            results[ticker] = result

    except Exception as exc:
        err = str(exc)
        for ticker in uncached:
            result = {
                "price": None, "currency": _infer_currency(ticker),
                "short_name": ticker, "day_change_pct": None,
                "market_state": None, "error": err,
            }
            results[ticker] = result

    return results


# ── Portfolio builder (shared by /live and /all-live) ─────────────────────────
def _build_portfolio(
    account_id: int,
    holdings: List[ShareHolding],
    prices: Dict[str, Dict[str, Any]],
    gbpusd: Optional[float],
    db: Session,
) -> PortfolioLiveResponse:
    """
    Combine a list of holdings with fetched prices.
    Persists successful prices to DB.
    Falls back to h.last_price when live fetch fails (is_stale=True).
    """
    live_holdings: List[LiveHoldingResponse] = []
    total_cost_gbp  = 0.0
    total_value_gbp = 0.0

    for h in holdings:
        info     = prices.get(h.ticker.upper(), {})
        live_p   = info.get("price")
        currency = info.get("currency") or h.currency or _infer_currency(h.ticker)
        error    = info.get("error")
        is_stale = False
        last_price_at = h.last_price_at

        if live_p is not None:
            # ── Successful fetch: persist to DB ───────────────────────────────
            price = live_p
            h.last_price          = price
            h.last_price_currency = currency
            h.last_price_at       = datetime.utcnow()
            last_price_at         = h.last_price_at
            db.add(h)
        elif h.last_price is not None:
            # ── Failed fetch: fall back to stored last-known price ─────────────
            price    = h.last_price
            currency = h.last_price_currency or currency
            is_stale = True
            # Keep error so UI can show it alongside the stale badge
        else:
            price = None

        live_value_native = (h.quantity * price) if price is not None else None
        live_value_gbp    = _to_gbp(live_value_native, currency, gbpusd) if live_value_native is not None else None

        cost_basis     = (h.quantity * h.avg_cost) if h.avg_cost is not None else None
        cost_basis_gbp = _to_gbp(cost_basis, currency, gbpusd) if cost_basis is not None else None

        pnl_native = (live_value_native - cost_basis) if (live_value_native is not None and cost_basis is not None) else None
        pnl_pct    = (pnl_native / cost_basis * 100) if (pnl_native is not None and cost_basis and cost_basis != 0) else None

        if live_value_gbp is not None:
            total_value_gbp += live_value_gbp
        if cost_basis_gbp is not None:
            total_cost_gbp += cost_basis_gbp

        # Persist inferred currency
        if currency and h.currency != currency:
            h.currency = currency
            db.add(h)

        live_holdings.append(LiveHoldingResponse(
            id=h.id,
            account_id=h.account_id,
            ticker=h.ticker,
            display_name=h.display_name,
            quantity=h.quantity,
            avg_cost=h.avg_cost,
            live_price=price,
            currency=currency,
            live_value_native=live_value_native,
            live_value_gbp=live_value_gbp,
            cost_basis=cost_basis,
            pnl_native=pnl_native,
            pnl_percent=pnl_pct,
            short_name=info.get("short_name"),
            day_change_pct=info.get("day_change_pct"),
            market_state=info.get("market_state"),
            price_error=error,
            is_stale=is_stale,
            last_price_at=last_price_at,
        ))

    total_pnl     = (total_value_gbp - total_cost_gbp) if (total_value_gbp and total_cost_gbp) else None
    total_pnl_pct = (total_pnl / total_cost_gbp * 100) if (total_pnl is not None and total_cost_gbp != 0) else None

    # Count how many live prices were successfully fetched in this request
    live_fetches = sum(1 for h in holdings if prices.get(h.ticker.upper(), {}).get("price") is not None)

    # Find the most recent successful update time among holdings
    successful_times = [h.last_price_at for h in holdings if h.last_price_at is not None]
    last_update = max(successful_times) if successful_times else None
    
    # If live_fetches == 0 (failed refresh / empty response), we do not update last update datetime
    last_refreshed_time = last_update if (live_fetches == 0 and last_update is not None) else datetime.utcnow()

    # ── Automatically sync the account current_value with the computed total_value_gbp ──
    # Only perform the sync if we successfully fetched at least one live price
    if live_fetches > 0:
        account = db.query(Account).filter(Account.id == account_id).first()
        if account and total_value_gbp > 0:
            previous = account.current_value
            change   = total_value_gbp - previous
            if abs(change) >= 0.01:
                pct = ((change / previous) * 100) if previous != 0 else None
                tickers_synced = [h.ticker for h in holdings]
                log = AuditLog(
                    account_id=account.id,
                    previous_value=previous,
                    new_value=total_value_gbp,
                    change_amount=change,
                    change_percent=pct,
                    note=f"Auto-synced on refresh from live share prices: {', '.join(tickers_synced)}",
                    recorded_at=datetime.utcnow(),
                )
                db.add(log)
                account.current_value = total_value_gbp
                account.updated_at    = datetime.utcnow()

    return PortfolioLiveResponse(
        account_id=account_id,
        holdings=live_holdings,
        total_cost_basis_gbp=total_cost_gbp or None,
        total_live_value_gbp=total_value_gbp or None,
        total_pnl_gbp=total_pnl,
        total_pnl_percent=total_pnl_pct,
        gbpusd_rate=gbpusd,
        last_refreshed=last_refreshed_time,
    )


# ── CRUD ──────────────────────────────────────────────────────────────────────

# ── Live Prices — ALL investment accounts in one call ─────────────────────────

@router.get("/all-live", response_model=List[PortfolioLiveResponse])
def get_all_live_portfolios(db: Session = Depends(get_db)):
    """
    Fetch live prices for every holding across ALL investment accounts.
    Deduplicates tickers and issues a SINGLE yf.download() call.
    Returns a list of PortfolioLiveResponse, one per account that has holdings.
    """
    # Load all holdings for all INVESTMENTS & RETIREMENT accounts
    holdings_all = (
        db.query(ShareHolding)
        .join(Account, Account.id == ShareHolding.account_id)
        .filter(Account.category.in_(["INVESTMENTS", "RETIREMENT"]), Account.is_active == True)
        .order_by(ShareHolding.account_id, ShareHolding.ticker)
        .all()
    )

    if not holdings_all:
        return []

    # Deduplicate tickers across all accounts → ONE batch download
    all_tickers = list({h.ticker.upper() for h in holdings_all})
    prices = _fetch_batch_prices(all_tickers)
    gbpusd = _fetch_gbpusd_rate()

    # Group holdings by account_id
    by_account: Dict[int, List[ShareHolding]] = {}
    for h in holdings_all:
        by_account.setdefault(h.account_id, []).append(h)

    portfolios = [
        _build_portfolio(acc_id, acc_holdings, prices, gbpusd, db)
        for acc_id, acc_holdings in by_account.items()
    ]

    db.commit()
    return portfolios


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.get("/{account_id}", response_model=List[ShareHoldingResponse])
def list_holdings(account_id: int, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return (
        db.query(ShareHolding)
        .filter(ShareHolding.account_id == account_id)
        .order_by(ShareHolding.ticker)
        .all()
    )


@router.post("/{account_id}", response_model=ShareHoldingResponse, status_code=201)
def add_holding(account_id: int, payload: ShareHoldingCreate, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    ticker   = payload.ticker.strip().upper()
    currency = _infer_currency(ticker)

    holding = ShareHolding(
        account_id=account_id, ticker=ticker,
        display_name=payload.display_name, quantity=payload.quantity,
        avg_cost=payload.avg_cost, currency=currency, notes=payload.notes,
    )
    db.add(holding)
    db.commit()
    db.refresh(holding)
    return holding


@router.put("/holding/{holding_id}", response_model=ShareHoldingResponse)
def update_holding(holding_id: int, payload: ShareHoldingUpdate, db: Session = Depends(get_db)):
    holding = db.query(ShareHolding).filter(ShareHolding.id == holding_id).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")

    data = payload.model_dump(exclude_unset=True)
    if "ticker" in data:
        data["ticker"]   = data["ticker"].strip().upper()
        data["currency"] = _infer_currency(data["ticker"])

    for field, value in data.items():
        setattr(holding, field, value)
    holding.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(holding)
    return holding


@router.delete("/holding/{holding_id}", status_code=204)
def delete_holding(holding_id: int, db: Session = Depends(get_db)):
    holding = db.query(ShareHolding).filter(ShareHolding.id == holding_id).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    db.delete(holding)
    db.commit()


# ── Live Prices — single account ──────────────────────────────────────────────

@router.get("/{account_id}/live", response_model=PortfolioLiveResponse)
def get_live_portfolio(account_id: int, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    holdings = (
        db.query(ShareHolding)
        .filter(ShareHolding.account_id == account_id)
        .order_by(ShareHolding.ticker)
        .all()
    )

    if not holdings:
        return PortfolioLiveResponse(
            account_id=account_id, holdings=[],
            total_cost_basis_gbp=None, total_live_value_gbp=None,
            total_pnl_gbp=None, total_pnl_percent=None,
            gbpusd_rate=None, last_refreshed=datetime.utcnow(),
        )

    all_tickers = list({h.ticker.upper() for h in holdings})
    prices = _fetch_batch_prices(all_tickers)
    gbpusd = _fetch_gbpusd_rate()

    result = _build_portfolio(account_id, holdings, prices, gbpusd, db)
    db.commit()
    return result


# ── Sync Account Value ────────────────────────────────────────────────────────

@router.post("/{account_id}/sync", response_model=dict)
def sync_account_value(account_id: int, db: Session = Depends(get_db)):
    """
    Recompute total GBP value of all holdings at current live prices and
    update account.current_value, writing an audit log entry.
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    holdings = db.query(ShareHolding).filter(ShareHolding.account_id == account_id).all()
    if not holdings:
        raise HTTPException(status_code=400, detail="No holdings to sync")

    all_tickers = list({h.ticker.upper() for h in holdings})
    prices  = _fetch_batch_prices(all_tickers)
    gbpusd  = _fetch_gbpusd_rate()

    # Count how many live prices were successfully fetched in this request
    live_fetches = sum(1 for h in holdings if prices.get(h.ticker.upper(), {}).get("price") is not None)
    if live_fetches == 0:
        raise HTTPException(status_code=503, detail="Empty response from Yahoo Finance. Sync skipped.")

    total_gbp: float  = 0.0
    tickers_synced: List[str] = []

    for h in holdings:
        info     = prices.get(h.ticker.upper(), {})
        price    = info.get("price") or h.last_price   # fall back to stored price
        currency = info.get("currency") or h.currency or "USD"
        if price is None:
            continue
        value_native = h.quantity * price
        value_gbp    = _to_gbp(value_native, currency, gbpusd)
        if value_gbp is not None:
            total_gbp += value_gbp
            tickers_synced.append(h.ticker)

    if total_gbp == 0:
        raise HTTPException(status_code=502, detail="Could not fetch live prices for any holding")

    previous = account.current_value
    change   = total_gbp - previous
    pct      = ((change / previous) * 100) if previous != 0 else None

    log = AuditLog(
        account_id=account.id,
        previous_value=previous,
        new_value=total_gbp,
        change_amount=change,
        change_percent=pct,
        note=f"Synced from live share prices: {', '.join(tickers_synced)}",
        recorded_at=datetime.utcnow(),
    )
    db.add(log)
    account.current_value = total_gbp
    account.updated_at    = datetime.utcnow()
    db.commit()

    return {
        "previous_value": previous,
        "new_value": total_gbp,
        "change_amount": change,
        "tickers_synced": tickers_synced,
        "gbpusd_rate": gbpusd,
    }
