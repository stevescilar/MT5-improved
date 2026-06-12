from strategy.swing_detector import SwingPoint


def classify_structure(swings: list[SwingPoint]) -> str | None:
    """
    Classify market structure using the last 4 swing points.
    Requires at least 6 swings to avoid misclassifying shallow consolidation.
    Returns 'BULLISH', 'BEARISH', or 'RANGING'.
    """
    if len(swings) < 6:
        return None

    s1, s2, s3, s4 = swings[-4], swings[-3], swings[-2], swings[-1]

    if (
        s1.type == "LOW"
        and s2.type == "HIGH"
        and s3.type == "LOW"
        and s4.type == "HIGH"
        and s3.price > s1.price
        and s4.price > s2.price
    ):
        return "BULLISH"

    if (
        s1.type == "HIGH"
        and s2.type == "LOW"
        and s3.type == "HIGH"
        and s4.type == "LOW"
        and s3.price < s1.price
        and s4.price < s2.price
    ):
        return "BEARISH"

    return "RANGING"
