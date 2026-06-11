def detect_fvg(candles):

    gaps = []

    for i in range(2, len(candles)):

        c1 = candles.iloc[i - 2]
        c2 = candles.iloc[i - 1]
        c3 = candles.iloc[i]

        # Bullish FVG
        if c1["high"] < c3["low"]:

            gaps.append(
                {"type": "BULLISH", "top": c3["low"], "bottom": c1["high"], "index": i}
            )

        # Bearish FVG
        elif c1["low"] > c3["high"]:

            gaps.append(
                {"type": "BEARISH", "top": c1["low"], "bottom": c3["high"], "index": i}
            )

    return gaps
