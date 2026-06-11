def detect_bos(candles, swings):

    if len(swings) < 2:
        return None

    current_close = candles.iloc[-1]["close"]

    last_high = None
    last_low = None

    for swing in reversed(swings):

        if swing.type == "HIGH" and last_high is None:
            last_high = swing

        if swing.type == "LOW" and last_low is None:
            last_low = swing

        if last_high and last_low:
            break

    if last_high and current_close > last_high.price:
        return "BULLISH_BOS"

    if last_low and current_close < last_low.price:
        return "BEARISH_BOS"

    return None
