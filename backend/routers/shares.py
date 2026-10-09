"""
Share Holdings router — CRUD + live prices + account sync.

Scraping, Yahoo fetching, caching and FX live in backend/services/*.
  • ALL tickers are fetched in ONE yf.download() call per request.
  • Last successful price is persisted to the DB so stale data survives restarts.
  • Results cached in-process for 15 minutes.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Account, AuditLog, ShareHolding
from schemas import (
    ShareHoldingCreate, ShareHoldingUpdate,
    ShareHoldingResponse, LiveHoldingResponse,
    PortfolioLiveResponse,
)
from services import utcnow_naive
from services.prices import infer_currency as _infer_currency, fetch_batch_prices as _fetch_batch_prices
from services.fx import FxSnapshot
from services.snapshot import value_holdings, build_note, fx_for_holdings

router = APIRouter(prefix="/api/shares", tags=["shares"])


def _fx_for(tickers_or_currencies: List[str], holdings: List[ShareHolding]) -> FxSnapshot:
    return fx_for_holdings(holdings)


# ── Portfolio builder (shared by /live and /all-live) ─────────────────────────
def _build_portfolio(
    account_id: int,
    holdings: List[ShareHolding],
    prices: Dict[str, Dict[str, Any]],
    fx: FxSnapshot,
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
            h.last_price_at       = utcnow_naive()
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
        live_value_gbp    = fx.to_gbp(live_value_native, currency) if live_value_native is not None else None

        cost_basis     = (h.quantity * h.avg_cost) if h.avg_cost is not None else None
        cost_basis_gbp = fx.to_gbp(cost_basis, currency) if cost_basis is not None else None

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
    last_refreshed_time = last_update if (live_fetches == 0 and last_update is not None) else utcnow_naive()

    # ── Automatically sync the account current_value with the computed total_value_gbp ──
    # Only perform the sync if we successfully fetched at least one live price
    # and every holding could be valued (otherwise the total would record a false drop)
    if live_fetches > 0 and all(lh.live_value_gbp is not None for lh in live_holdings):
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
                    recorded_at=utcnow_naive(),
                )
                db.add(log)
                account.current_value = total_value_gbp
                account.updated_at    = utcnow_naive()

    return PortfolioLiveResponse(
        account_id=account_id,
        holdings=live_holdings,
        total_cost_basis_gbp=total_cost_gbp or None,
        total_live_value_gbp=total_value_gbp or None,
        total_pnl_gbp=total_pnl,
        total_pnl_percent=total_pnl_pct,
        gbpusd_rate=fx.gbpusd,
        gbpusd_rate_is_fallback=fx.flags()["gbpusd_rate_is_fallback"],
        gbpusd_rate_stale=fx.flags()["gbpusd_rate_is_stale"],
        unpriced_tickers=[h.ticker for h in live_holdings if h.live_value_gbp is None],
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
    fx = _fx_for(all_tickers, holdings_all)

    # Group holdings by account_id
    by_account: Dict[int, List[ShareHolding]] = {}
    for h in holdings_all:
        by_account.setdefault(h.account_id, []).append(h)

    portfolios = [
        _build_portfolio(acc_id, acc_holdings, prices, fx, db)
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
    holding.updated_at = utcnow_naive()
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
            gbpusd_rate=None, last_refreshed=utcnow_naive(),
        )

    all_tickers = list({h.ticker.upper() for h in holdings})
    prices = _fetch_batch_prices(all_tickers)
    fx = _fx_for(all_tickers, holdings)

    result = _build_portfolio(account_id, holdings, prices, fx, db)
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
    prices = _fetch_batch_prices(all_tickers)
    fx     = _fx_for(all_tickers, holdings)

    live_fetches = sum(1 for h in holdings if prices.get(h.ticker.upper(), {}).get("price") is not None)
    if live_fetches == 0:
        raise HTTPException(status_code=503, detail="Empty response from Yahoo Finance. Sync skipped.")

    v = value_holdings(holdings, prices, fx)
    total_gbp = v["total_gbp"]
    tickers_synced, stale_tickers, unpriced = v["tickers_synced"], v["stale_tickers"], v["unpriced"]

    if unpriced:
        raise HTTPException(
            status_code=502,
            detail=f"Sync aborted: no usable price/FX rate for {', '.join(unpriced)}. "
                   "Account value not changed.",
        )

    previous = account.current_value
    change   = total_gbp - previous
    pct      = ((change / previous) * 100) if previous != 0 else None

    flags = fx.flags()
    note = build_note(v, fx)

    log = AuditLog(
        account_id=account.id,
        previous_value=previous,
        new_value=total_gbp,
        change_amount=change,
        change_percent=pct,
        note=note,
        recorded_at=utcnow_naive(),
    )
    db.add(log)
    account.current_value = total_gbp
    account.updated_at    = utcnow_naive()
    db.commit()

    return {
        "previous_value": previous,
        "new_value": total_gbp,
        "change_amount": change,
        "tickers_synced": tickers_synced,
        "stale_tickers": stale_tickers,
        "gbpusd_rate": fx.gbpusd,
        "gbpusd_rate_is_fallback": flags["gbpusd_rate_is_fallback"],
        "gbpusd_rate_is_stale": flags["gbpusd_rate_is_stale"],
        "gbpusd_rate_fetched_at": flags["gbpusd_rate_fetched_at"],
    }
