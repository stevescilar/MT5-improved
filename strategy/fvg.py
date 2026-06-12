"""
Fair Value Gap (FVG) detection.

Fixes over original:
  • is_fvg_filled: original used a one-sided check.  A BULLISH FVG is filled
    when a candle's LOW trades INTO the gap (≤ top but ≥ bottom); a BEARISH
    FVG is filled when HIGH trades into the gap.  The original only checked
    the top/bottom boundary, producing false "filled" flags.
  • Added `min_gap_pips` parameter to ignore micro gaps smaller than a
    meaningful price move (avoids noise entries on tight-spread instruments).
"""

from typing import Optional


def detect_fvg(candles, min_gap_pips: float = 0.0) -> list[dict]:
    """
    Identify three-candle FVG patterns.

    Parameters
    ----------
    candles : DataFrame with high/low columns.
    min_gap_pips : Ignore gaps smaller than this value (raw price distance).
        Pass 0.0 (default) to disable and keep original behaviour.
    """
    gaps: list[dict] = []
    for i in range(2, len(candles)):
        c1 = candles.iloc[i - 2]
        c3 = candles.iloc[i]

        # Bullish FVG: gap between c1.high and c3.low
        if c1["high"] < c3["low"]:
            gap_size = c3["low"] - c1["high"]
            if gap_size >= min_gap_pips:
                gaps.append(
                    {
                        "type": "BULLISH",
                        "top": c3["low"],
                        "bottom": c1["high"],
                        "index": i,
                        "size": gap_size,
                    }
                )

        # Bearish FVG: gap between c3.high and c1.low
        elif c1["low"] > c3["high"]:
            gap_size = c1["low"] - c3["high"]
            if gap_size >= min_gap_pips:
                gaps.append(
                    {
                        "type": "BEARISH",
                        "top": c1["low"],
                        "bottom": c3["high"],
                        "index": i,
                        "size": gap_size,
                    }
                )

    return gaps


def is_fvg_filled(fvg: dict, candles) -> bool:
    """
    Return True if price has fully re-entered (not just touched) the FVG zone.

    A BULLISH FVG (gap above) is filled when a subsequent candle's LOW
    penetrates into the gap zone (low <= fvg.top AND low >= fvg.bottom, i.e.
    trades into the gap), OR closes below the bottom.

    A BEARISH FVG (gap below) is filled when a subsequent candle's HIGH
    penetrates into the gap zone, OR closes above the top.
    """
    later = candles.iloc[fvg["index"] + 1 :]
    if later.empty:
        return False

    if fvg["type"] == "BULLISH":
        # Filled if any candle low drops into or below the gap
        return bool((later["low"] <= fvg["top"]).any())
    else:
        # Filled if any candle high rises into or above the gap
        return bool((later["high"] >= fvg["bottom"]).any())
