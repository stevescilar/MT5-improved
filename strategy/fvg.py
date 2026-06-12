def detect_fvg(candles) -> list[dict]:
    gaps = []
    for i in range(2, len(candles)):
        c1 = candles.iloc[i - 2]
        c3 = candles.iloc[i]

        if c1["high"] < c3["low"]:
            gaps.append(
                {"type": "BULLISH", "top": c3["low"], "bottom": c1["high"], "index": i}
            )
        elif c1["low"] > c3["high"]:
            gaps.append(
                {"type": "BEARISH", "top": c1["low"], "bottom": c3["high"], "index": i}
            )

    return gaps


def is_fvg_filled(fvg: dict, candles) -> bool:
    """Return True if price has re-entered the FVG zone after it formed."""
    later = candles.iloc[fvg["index"] + 1 :]
    if later.empty:
        return False
    if fvg["type"] == "BULLISH":
        return bool((later["low"] <= fvg["top"]).any())
    else:
        return bool((later["high"] >= fvg["bottom"]).any())
