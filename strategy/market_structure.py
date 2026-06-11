from strategy.bos import detect_bos


def classify_structure(swings):

    if len(swings) < 4:
        return None

    s1 = swings[-4]
    s2 = swings[-3]
    s3 = swings[-2]
    s4 = swings[-1]

    if (
        s1.type == "LOW"
        and s2.type == "HIGH"
        and s3.type == "LOW"
        and s4.type == "HIGH"
    ):

        if s3.price > s1.price and s4.price > s2.price:
            return "BULLISH"

    if (
        s1.type == "HIGH"
        and s2.type == "LOW"
        and s3.type == "HIGH"
        and s4.type == "LOW"
    ):

        if s3.price < s1.price and s4.price < s2.price:
            return "BEARISH"

    return "RANGING"
