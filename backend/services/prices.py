"""Currency inference and batched price fetching (Yahoo Finance + L&G)."""
from typing import Any, Dict, List, Optional

from .cache import cache_get, cache_set
from .landg import fetch_landg_price

_SUFFIX_CURRENCY: Dict[str, str] = {
    ".L":  "GBX",   # London Stock Exchange (pence)
    ".IL": "ILA",   # Tel Aviv (agorot)
    ".AS": "EUR", ".PA": "EUR", ".DE": "EUR", ".MI": "EUR", ".MC": "EUR",
    ".SW": "CHF",
    ".HK": "HKD",
    ".T":  "JPY",
    ".AX": "AUD",
    ".TO": "CAD", ".V": "CAD",
    ".NZ": "NZD",
}


def infer_currency(ticker: str) -> str:
    t = ticker.upper()
    if t.startswith("LG:"):
        return "GBP"
    if t.startswith("0P") and t.endswith(".L"):
        return "GBP"
    for suffix, ccy in _SUFFIX_CURRENCY.items():
        if t.endswith(suffix.upper()):
            return ccy
    return "USD"


def close_series_for(raw: Any, ticker: str) -> Any:
    """Extract the cleaned Close series for one ticker from a yf.download() frame."""
    close = raw["Close"]
    if hasattr(close, "columns"):
        if ticker in close.columns:
            close = close[ticker]
        else:
            close = close.iloc[:, 0]
    return close.dropna()


def _empty(ticker: str, error: str) -> Dict[str, Any]:
    return {
        "price": None, "currency": infer_currency(ticker), "short_name": ticker,
        "day_change_pct": None, "market_state": None, "error": error,
    }


def fetch_batch_prices(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetch prices for all tickers in a single yf.download() call ("LG:" tickers are
    scraped). Returns dict keyed by UPPERCASE ticker. Cached tickers are skipped.
    """
    results: Dict[str, Dict[str, Any]] = {}
    uncached: List[str] = []
    for t in tickers:
        hit = cache_get(t)
        if hit:
            results[t.upper()] = hit
        else:
            uncached.append(t.upper())
    if not uncached:
        return results

    yf_tickers: List[str] = []
    for ticker in uncached:
        if ticker.startswith("LG:"):
            data = fetch_landg_price(ticker[3:])
            if data.get("price") is not None:
                cache_set(ticker, data)
            results[ticker] = data
        else:
            yf_tickers.append(ticker)
    if not yf_tickers:
        return results

    try:
        import yfinance as yf
        raw = yf.download(tickers=" ".join(yf_tickers), period="5d",
                          progress=False, auto_adjust=True)
        if raw.empty:
            raise ValueError("Empty response from Yahoo Finance")

        for ticker in yf_tickers:
            try:
                close = close_series_for(raw, ticker)
                if close.empty:
                    result = _empty(ticker, f"No price data for '{ticker}' — is the ticker symbol correct?")
                else:
                    price = float(close.iloc[-1])
                    prev = float(close.iloc[-2]) if len(close) >= 2 else None
                    result = {
                        "price": price, "currency": infer_currency(ticker),
                        "short_name": ticker,
                        "day_change_pct": ((price - prev) / prev * 100) if prev else None,
                        "market_state": None, "error": None,
                    }
            except Exception as exc:
                result = _empty(ticker, str(exc))

            if result.get("price") is not None or (
                result.get("error") and "is the ticker symbol correct" in result["error"]
            ):
                cache_set(ticker, result)
            results[ticker] = result
    except Exception as exc:
        for ticker in yf_tickers:
            results[ticker] = _empty(ticker, str(exc))

    return results
