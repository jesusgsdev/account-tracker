"""L&G Fund Centre scraper. Ticker format: "LG:<FUND_CODE>" e.g. "LG:BC03"."""
from typing import Any, Dict, Optional

LG_BASE_URL = "https://fundcentres.landg.com/en/uk/workplace-employee/fund-centre/"
LG_FUND_SLUGS: Dict[str, str] = {
    # fund-code -> URL slug (add more as needed)
    "BC03": "Global-Developed-Equity-Index-Fund",
    "BAW3": "Global-Developed-Equity-Index-Fund",
    "BAVY": "Global-Developed-Equity-Index-Fund",
}


def parse_landg_html(html: str, fund_code: str) -> Dict[str, Any]:
    """Pure parser. Returns {"price_pence", "as_at", "short_name"} (price_pence may be None)."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    price_pence: Optional[float] = None
    as_at: Optional[str] = None
    short_name = f"L&G {fund_code}"
    shareclass_id: Optional[str] = None

    # Strategy 1: resolve shareclass-id via the selector anchor carrying data-fund-code.
    selector_anchor = soup.find(
        "a", attrs={"data-fund-code": lambda v: v and v.strip().upper() == fund_code.upper()}
    )
    if selector_anchor:
        shareclass_id = selector_anchor.get("data-value")
        h1_tag = soup.find("h1", attrs={"data-shareclass-id": shareclass_id})
        if h1_tag:
            short_name = h1_tag.get("data-shareclass-name", short_name)

    if shareclass_id:
        row = soup.find(
            "div",
            attrs={"data-shareclass-id": shareclass_id,
                   "class": lambda c: c and "FundRibbonPrices-row" in c},
        )
        if row:
            strong_tags = row.find_all("strong")
            for tag in strong_tags:
                text = tag.get_text(strip=True).replace("p", "").replace(",", "")
                try:
                    price_pence = float(text)
                    break
                except ValueError:
                    pass
            if len(strong_tags) >= 2:
                as_at = strong_tags[1].get_text(strip=True)

    # Strategy 2: first visible "<digits>p" price on the page
    if price_pence is None:
        for strong in soup.find_all("strong"):
            text = strong.get_text(strip=True)
            if text.endswith("p") and text[:-1].replace(".", "").replace(",", "").isdigit():
                try:
                    price_pence = float(text[:-1].replace(",", ""))
                    break
                except ValueError:
                    pass

    return {"price_pence": price_pence, "as_at": as_at, "short_name": short_name}


def _err(fund_code: str, msg: str, short_name: Optional[str] = None) -> Dict[str, Any]:
    return {
        "price": None, "currency": "GBP",
        "short_name": short_name or f"L&G {fund_code}",
        "day_change_pct": None, "market_state": None, "error": msg,
    }


def fetch_landg_price(fund_code: str) -> Dict[str, Any]:
    """Scrape the fund page; prices are in pence, returned in GBP."""
    slug = LG_FUND_SLUGS.get(fund_code.upper())
    if not slug:
        return _err(fund_code, f"No URL slug configured for L&G fund code '{fund_code}'")

    url = f"{LG_BASE_URL}{slug}/?isin_code={fund_code}"
    try:
        import requests

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-GB,en;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        parsed = parse_landg_html(resp.text, fund_code)
        if parsed["price_pence"] is None:
            return _err(fund_code, f"Could not parse price from L&G fund page for '{fund_code}'",
                        parsed["short_name"])
        return {
            "price": parsed["price_pence"] / 100.0,
            "currency": "GBP",
            "short_name": parsed["short_name"],
            "day_change_pct": None,   # page doesn't publish daily change
            "market_state": None,
            "error": None,
            "price_note": f"as at {parsed['as_at']}" if parsed["as_at"] else "",
        }
    except Exception as exc:
        return _err(fund_code, f"L&G scrape failed: {exc}")
