"""GBP money arithmetic.

Columns stay REAL/float (no schema or API change); these helpers do the
arithmetic in Decimal and round to pence (ROUND_HALF_UP) so sums and deltas
reconcile. Only use for money amounts, never share quantities or prices.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Optional, Tuple

_PENNY = Decimal("0.01")


def _d(x) -> Decimal:
    # repr-based conversion avoids binary-float noise (0.1 + 0.2 style)
    return x if isinstance(x, Decimal) else Decimal(repr(float(x)))


def round_money(x) -> float:
    """Round to 2dp, half-up, returning a float."""
    return float(_d(x).quantize(_PENNY, rounding=ROUND_HALF_UP))


def money_sum(values: Iterable) -> float:
    """Exact (Decimal) sum of money values, rounded to pence."""
    return round_money(sum((_d(v) for v in values), Decimal(0)))


def money_delta(previous, new) -> Tuple[float, Optional[float]]:
    """(change_amount, change_percent) for a value change.

    Amount is the penny-rounded difference; percent is computed from the exact
    Decimal difference (None when previous is 0).
    """
    p, n = _d(previous), _d(new)
    diff = n - p
    pct = float(diff / p * 100) if p != 0 else None
    return round_money(diff), pct
