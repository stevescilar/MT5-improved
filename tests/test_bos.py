from strategy.bos import detect_bos
from strategy.market_structure import detect_bos as detect_bos_from_market_structure
from strategy.swing_detector import SwingPoint


def test_detects_bullish_bos(candles_from):
    candles = candles_from([[1.0, 1.2, 0.8, 2.1]])
    swings = [
        SwingPoint(index=1, price=1.0, type="LOW"),
        SwingPoint(index=2, price=2.0, type="HIGH"),
    ]

    assert detect_bos(candles, swings) == "BULLISH_BOS"


def test_detects_bearish_bos(candles_from):
    candles = candles_from([[1.0, 1.2, 0.4, 0.5]])
    swings = [
        SwingPoint(index=1, price=1.0, type="HIGH"),
        SwingPoint(index=2, price=0.6, type="LOW"),
    ]

    assert detect_bos(candles, swings) == "BEARISH_BOS"


def test_returns_none_when_no_bos(candles_from):
    candles = candles_from([[1.0, 1.2, 0.8, 1.1]])
    swings = [
        SwingPoint(index=1, price=1.0, type="LOW"),
        SwingPoint(index=2, price=2.0, type="HIGH"),
    ]

    assert detect_bos(candles, swings) is None


def test_market_structure_exports_same_bos_function():
    assert detect_bos_from_market_structure is detect_bos
