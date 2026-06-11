from strategy.swing_detector import SwingPoint, detect_swings


def test_detects_swing_high_and_low(candles_from):
    candles = candles_from(
        [
            [1.0, 1.0, 0.7, 0.9],
            [1.0, 2.0, 0.9, 1.8],
            [1.8, 1.9, 1.1, 1.2],
            [1.2, 1.4, 0.5, 0.7],
            [0.7, 1.1, 0.8, 1.0],
        ]
    )

    assert detect_swings(candles, lookback=1) == [
        SwingPoint(index=1, price=2.0, type="HIGH"),
        SwingPoint(index=3, price=0.5, type="LOW"),
    ]


def test_filters_consecutive_highs_to_stronger_high(candles_from):
    candles = candles_from(
        [
            [1.0, 1.0, 0.8, 0.9],
            [0.9, 2.0, 0.9, 1.9],
            [1.9, 1.8, 1.0, 1.2],
            [1.2, 2.5, 1.1, 2.2],
            [2.2, 1.9, 1.2, 1.4],
        ]
    )

    assert detect_swings(candles, lookback=1) == [
        SwingPoint(index=3, price=2.5, type="HIGH")
    ]
