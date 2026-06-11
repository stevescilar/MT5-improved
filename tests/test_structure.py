from strategy.market_structure import classify_structure
from strategy.swing_detector import SwingPoint


def test_classifies_bullish_structure():
    swings = [
        SwingPoint(index=1, price=1.0, type="LOW"),
        SwingPoint(index=2, price=2.0, type="HIGH"),
        SwingPoint(index=3, price=1.2, type="LOW"),
        SwingPoint(index=4, price=2.4, type="HIGH"),
    ]

    assert classify_structure(swings) == "BULLISH"


def test_classifies_bearish_structure():
    swings = [
        SwingPoint(index=1, price=2.4, type="HIGH"),
        SwingPoint(index=2, price=1.2, type="LOW"),
        SwingPoint(index=3, price=2.0, type="HIGH"),
        SwingPoint(index=4, price=1.0, type="LOW"),
    ]

    assert classify_structure(swings) == "BEARISH"


def test_classifies_ranging_structure():
    swings = [
        SwingPoint(index=1, price=1.0, type="LOW"),
        SwingPoint(index=2, price=2.0, type="HIGH"),
        SwingPoint(index=3, price=0.9, type="LOW"),
        SwingPoint(index=4, price=2.1, type="HIGH"),
    ]

    assert classify_structure(swings) == "RANGING"


def test_returns_none_when_not_enough_swings():
    assert classify_structure([]) is None
