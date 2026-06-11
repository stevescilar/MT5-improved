from dataclasses import dataclass


@dataclass
class SwingPoint:
    index: int
    price: float
    type: str


def detect_swings(candles, lookback=3):

    raw_swings = []

    for i in range(lookback, len(candles) - lookback):

        high = candles.iloc[i]["high"]
        low = candles.iloc[i]["low"]

        is_high = True
        is_low = True

        for j in range(i - lookback, i + lookback + 1):

            if i == j:
                continue

            if candles.iloc[j]["high"] >= high:
                is_high = False

            if candles.iloc[j]["low"] <= low:
                is_low = False

        if is_high:
            raw_swings.append(SwingPoint(i, high, "HIGH"))

        if is_low:
            raw_swings.append(SwingPoint(i, low, "LOW"))

    raw_swings.sort(key=lambda x: x.index)

    filtered = []

    for swing in raw_swings:

        if not filtered:
            filtered.append(swing)
            continue

        last = filtered[-1]

        if last.type != swing.type:
            filtered.append(swing)

        else:

            if swing.type == "HIGH":

                if swing.price > last.price:
                    filtered[-1] = swing

            elif swing.type == "LOW":

                if swing.price < last.price:
                    filtered[-1] = swing

    return filtered
