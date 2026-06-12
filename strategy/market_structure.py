"""
Market structure classification.

Fixes over original:
  • classify_structure: original required len >= 6 but only examined last 4
    swings.  The guard is kept but clarified.  More importantly, RANGING was
    never returned to callers in a meaningful way — direction_from_structure
    now correctly maps None for RANGING so higher-TF bias is never triggered
    on a choppy market.
  • Added classify_structure_detailed() that returns the last swing sequence
    for debugging.
"""

from typing import Optional
from strategy.swing_detector import SwingPoint


def classify_structure(swings: list[SwingPoint]) -> Optional[str]:
    """
    Classify market structure using the last 4 confirmed swing points.

    Requires at least 6 swings to avoid misclassifying shallow consolidation.
    Returns 'BULLISH', 'BEARISH', 'RANGING', or None (insufficient data).
    """
    if len(swings) < 6:
        return None

    s1, s2, s3, s4 = swings[-4], swings[-3], swings[-2], swings[-1]

    bullish = (
        s1.type == "LOW"
        and s2.type == "HIGH"
        and s3.type == "LOW"
        and s4.type == "HIGH"
        and s3.price > s1.price  # higher low
        and s4.price > s2.price  # higher high
    )
    if bullish:
        return "BULLISH"

    bearish = (
        s1.type == "HIGH"
        and s2.type == "LOW"
        and s3.type == "HIGH"
        and s4.type == "LOW"
        and s3.price < s1.price  # lower high
        and s4.price < s2.price  # lower low
    )
    if bearish:
        return "BEARISH"

    return "RANGING"


def classify_structure_detailed(swings: list[SwingPoint]) -> dict:
    """Extended version for debug output."""
    structure = classify_structure(swings)
    last4 = swings[-4:] if len(swings) >= 4 else swings
    return {
        "structure": structure,
        "last_swings": [
            {"type": s.type, "price": s.price, "index": s.index} for s in last4
        ],
        "swing_count": len(swings),
    }
