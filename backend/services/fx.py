"""
FX helpers. Rates are expressed as units of CCY per 1 GBP (Yahoo ticker GBP<CCY>=X),
so value_gbp = value_ccy / rate.

Resolution order per currency: in-process cache -> live Yahoo (one batched call)
-> persisted file -> (USD only) hard-coded 1.30 flagged as fallback.
Special units: GBP (1), GBX (pence, /100), ILA (agorot, /100 then ILS).
"""
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, Optional

from .cache import cache_get, cache_set
from .prices import close_series_for
from .timeutil import utcnow_naive

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FX_FILE = os.path.join(_BASE, "services", "fx_rates.json")
LEGACY_USD_FILE = os.path.join(_BASE, "routers", "gbpusd_rate.json")  # read-only legacy seed
USD_HARD_FALLBACK = 1.30
STALE_AFTER = timedelta(days=3)

# pricing currency -> (settlement currency used for the FX lookup, divisor)
_SUBUNITS = {"GBX": ("GBP", 100.0), "ILA": ("ILS", 100.0)}


class FxRate:
    __slots__ = ("rate", "source", "fetched_at")

    def __init__(self, rate: float, source: str, fetched_at: Optional[datetime]):
        self.rate = rate
        self.source = source            # live | cache | persisted | fallback
        self.fetched_at = fetched_at

    @property
    def is_fallback(self) -> bool:
        return self.source == "fallback"

    @property
    def is_stale(self) -> bool:
        if self.source == "fallback":
            return True
        if self.source == "persisted":
            return self.fetched_at is None or utcnow_naive() - self.fetched_at > STALE_AFTER
        return False


class FxSnapshot:
    """Rates for a set of currencies fetched together."""

    def __init__(self, rates: Dict[str, FxRate]):
        self.rates = rates

    def to_gbp(self, value: Optional[float], currency: Optional[str]) -> Optional[float]:
        if value is None or not currency:
            return None
        ccy = currency.upper()
        divisor = 1.0
        if ccy in _SUBUNITS:
            ccy, divisor = _SUBUNITS[ccy]
        if ccy == "GBP":
            return value / divisor
        fx = self.rates.get(ccy)
        if fx is None or not fx.rate:
            return None
        return value / divisor / fx.rate

    @property
    def gbpusd(self) -> Optional[float]:
        fx = self.rates.get("USD")
        return fx.rate if fx else None

    def flags(self) -> Dict[str, Any]:
        """gbpusd_rate_is_fallback / _is_stale / _fetched_at plus per-currency detail."""
        usd = self.rates.get("USD")
        return {
            "gbpusd_rate_is_fallback": bool(usd and usd.is_fallback),
            "gbpusd_rate_is_stale": bool(usd and usd.is_stale),
            "gbpusd_rate_fetched_at": usd.fetched_at.isoformat() if usd and usd.fetched_at else None,
            "fx_rates": {
                c: {"rate": r.rate, "source": r.source, "is_stale": r.is_stale,
                    "fetched_at": r.fetched_at.isoformat() if r.fetched_at else None}
                for c, r in self.rates.items()
            },
        }


def _load_persisted() -> Dict[str, Dict[str, Any]]:
    data: Dict[str, Dict[str, Any]] = {}
    try:
        with open(LEGACY_USD_FILE, "r") as f:
            old = json.load(f)
        if old.get("rate"):
            data["USD"] = {"rate": old["rate"], "fetched_at": old.get("fetched_at")}
    except Exception:
        pass
    try:
        with open(FX_FILE, "r") as f:
            data.update(json.load(f))
    except Exception:
        pass
    return data


def _save_persisted(updates: Dict[str, FxRate]) -> None:
    data = _load_persisted()
    for c, r in updates.items():
        data[c] = {"rate": r.rate, "fetched_at": r.fetched_at.isoformat() if r.fetched_at else None}
    try:
        tmp = FX_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, FX_FILE)
    except Exception:
        pass


def _parse_dt(s: Any) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(s) if s else None
    except Exception:
        return None


def _fx_settlement_currencies(currencies: Iterable[str]) -> set:
    out = set()
    for c in currencies:
        c = (c or "").upper()
        if not c:
            continue
        c = _SUBUNITS.get(c, (c, 1))[0]
        if c != "GBP":
            out.add(c)
    return out


def fetch_fx_rates(currencies: Iterable[str]) -> FxSnapshot:
    """Resolve GBP->CCY rates for every currency (USD is always included)."""
    needed = _fx_settlement_currencies(currencies) | {"USD"}
    rates: Dict[str, FxRate] = {}

    missing = []
    for c in sorted(needed):
        hit = cache_get(f"GBP{c}=X")
        if hit and hit.get("price"):
            rates[c] = FxRate(hit["price"], hit.get("fx_source", "cache"), hit.get("fx_fetched_at"))
        else:
            missing.append(c)

    if missing:
        live: Dict[str, FxRate] = {}
        try:
            import yfinance as yf
            syms = [f"GBP{c}=X" for c in missing]
            raw = yf.download(" ".join(syms), period="5d", progress=False, auto_adjust=True)
            if not raw.empty:
                now = utcnow_naive()
                for c, sym in zip(missing, syms):
                    try:
                        close = close_series_for(raw, sym)
                        if not close.empty:
                            live[c] = FxRate(float(close.iloc[-1]), "live", now)
                    except Exception:
                        pass
        except Exception:
            pass

        if live:
            _save_persisted(live)   # only on success

        persisted = _load_persisted() if len(live) < len(missing) else {}
        for c in missing:
            if c in live:
                fx = live[c]
            elif persisted.get(c, {}).get("rate"):
                fx = FxRate(float(persisted[c]["rate"]), "persisted", _parse_dt(persisted[c].get("fetched_at")))
            elif c == "USD":
                fx = FxRate(USD_HARD_FALLBACK, "fallback", None)
            else:
                continue
            rates[c] = fx
            if fx.source in ("live", "persisted"):
                cache_set(f"GBP{c}=X", {"price": fx.rate, "fx_source": "cache" if fx.source == "live" else "persisted",
                                        "fx_fetched_at": fx.fetched_at})
    return FxSnapshot(rates)
