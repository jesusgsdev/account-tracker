import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.landg import parse_landg_html  # noqa: E402
from services.fx import FxRate, FxSnapshot  # noqa: E402
from services.prices import infer_currency  # noqa: E402

FIXTURE = """
<html><body>
<h1 data-shareclass-id="77" data-shareclass-name="Global Dev Eq Index (BC03)"></h1>
<a data-fund-code="BC03" data-value="77">BC03</a>
<a data-fund-code="BAW3" data-value="88">BAW3</a>
<div class="FundRibbonPrices-row x" data-shareclass-id="88"><strong>111.00p</strong><strong>01 Jan 2026</strong></div>
<div class="FundRibbonPrices-row x" data-shareclass-id="77">
  <span class=" price">Price</span><strong>3,037.37p</strong><strong>19 Jun 2026</strong>
</div>
</body></html>
"""


def test_parse_landg_row():
    r = parse_landg_html(FIXTURE, "bc03")
    assert r["price_pence"] == 3037.37
    assert r["as_at"] == "19 Jun 2026"
    assert r["short_name"] == "Global Dev Eq Index (BC03)"


def test_parse_landg_fallback_first_strong():
    r = parse_landg_html("<html><strong>12.5p</strong></html>", "ZZZZ")
    assert r["price_pence"] == 12.5


def test_parse_landg_no_price():
    assert parse_landg_html("<html></html>", "BC03")["price_pence"] is None


def test_infer_currency():
    assert infer_currency("VOD.L") == "GBX"
    assert infer_currency("LG:BC03") == "GBP"
    assert infer_currency("SAP.DE") == "EUR"
    assert infer_currency("AAPL") == "USD"


def test_to_gbp_conversions():
    fx = FxSnapshot({
        "USD": FxRate(1.25, "live", None),
        "EUR": FxRate(1.20, "live", None),
        "ILS": FxRate(4.5, "live", None),
    })
    assert fx.to_gbp(100, "GBP") == 100
    assert fx.to_gbp(100, "GBX") == 1
    assert fx.to_gbp(125, "USD") == 100
    assert fx.to_gbp(120, "EUR") == 100
    assert abs(fx.to_gbp(450, "ILA") - 1.0) < 1e-9
    assert fx.to_gbp(1, "CHF") is None
