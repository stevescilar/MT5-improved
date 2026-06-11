def detect_liquidity_sweep(candles, swings):

    if len(swings) < 2:
        return None

    current = candles.iloc[-1]

    last_high = None
    last_low = None

    for swing in reversed(swings):

        if swing.type == "HIGH" and last_high is None:
            last_high = swing

        if swing.type == "LOW" and last_low is None:
            last_low = swing

        if last_high and last_low:
            break

    # Buy-side liquidity sweep
    if (
        last_high
        and current["high"] > last_high.price
        and current["close"] < last_high.price
    ):
        return "BUY_SIDE_SWEEP"

    # Sell-side liquidity sweep
    if (
        last_low
        and current["low"] < last_low.price
        and current["close"] > last_low.price
    ):
        return "SELL_SIDE_SWEEP"

    return None
