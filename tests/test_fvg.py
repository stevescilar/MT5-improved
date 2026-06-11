from strategy.fvg import detect_fvg


def test_detects_bullish_fvg(candles_from):
    candles = candles_from(
        [
            [1.0, 1.5, 0.8, 1.2],
            [1.2, 1.7, 1.0, 1.4],
            [1.8, 2.2, 1.7, 2.0],
        ]
    )

    assert detect_fvg(candles) == [
        {"type": "BULLISH", "top": 1.7, "bottom": 1.5, "index": 2}
    ]


def test_detects_bearish_fvg(candles_from):
    candles = candles_from(
        [
            [2.0, 2.5, 2.0, 2.2],
            [2.1, 2.3, 1.8, 2.0],
            [1.4, 1.7, 1.1, 1.3],
        ]
    )

    assert detect_fvg(candles) == [
        {"type": "BEARISH", "top": 2.0, "bottom": 1.7, "index": 2}
    ]


def test_returns_empty_list_when_no_fvg(candles_from):
    candles = candles_from(
        [
            [1.0, 1.5, 0.8, 1.2],
            [1.2, 1.6, 0.9, 1.4],
            [1.3, 1.7, 1.0, 1.5],
        ]
    )

    assert detect_fvg(candles) == []
