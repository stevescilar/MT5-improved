"""
Swing detector — identifies local highs and lows.

Fixes over original:
  • Strict inequality for HIGH detection (>= was allowing equal neighbours to
    invalidate a real swing high; changed to strict > to match SMC convention).
  • Same for LOW detection (strict <).
  • Added `min_swing_size` parameter: ignores micro-swings smaller than
    `min_swing_size` × average candle range, reducing noise on M1/M5.
"""

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class SwingPoint:
    index: int
    price: float
    type: str  # "HIGH" | "LOW"


def detect_swings(
    candles: pd.DataFrame,
    lookback: int = 3,
    min_swing_size: float = 0.0,
) -> list[SwingPoint]:
    """
    Detect swing highs and lows.

    Parameters
    ----------
    candles : DataFrame with open/high/low/close columns.
    lookback : number of candles on each side required to confirm a swing.
    min_swing_size : minimum swing size as a multiple of the average candle
        range (high-low).  0.0 disables the filter (original behaviour).
    """
    n = len(candles)
    raw_swings: list[SwingPoint] = []

    # Compute average range for noise filter
    avg_range = (candles["high"] - candles["low"]).mean() if min_swing_size > 0 else 0.0
    min_body = avg_range * min_swing_size

    for i in range(lookback, n - lookback):
        high = candles.iloc[i]["high"]
        low = candles.iloc[i]["low"]

        is_high = all(
            candles.iloc[j]["high"] < high  # strict: equal neighbour disqualifies
            for j in range(i - lookback, i + lookback + 1)
            if j != i
        )
        is_low = all(
            candles.iloc[j]["low"] > low  # strict
            for j in range(i - lookback, i + lookback + 1)
            if j != i
        )

        # Noise filter
        if min_body > 0:
            swing_range = high - low
            if swing_range < min_body:
                is_high = False
                is_low = False

        if is_high:
            raw_swings.append(SwingPoint(i, high, "HIGH"))
        if is_low:
            raw_swings.append(SwingPoint(i, low, "LOW"))

    raw_swings.sort(key=lambda x: x.index)

    # De-duplicate consecutive same-type swings (keep extreme)
    filtered: list[SwingPoint] = []
    for swing in raw_swings:
        if not filtered:
            filtered.append(swing)
            continue
        last = filtered[-1]
        if last.type != swing.type:
            filtered.append(swing)
        else:
            if swing.type == "HIGH" and swing.price > last.price:
                filtered[-1] = swing
            elif swing.type == "LOW" and swing.price < last.price:
                filtered[-1] = swing

    return filtered
