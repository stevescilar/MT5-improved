from strategy.trade_setup import (
    calculate_risk_reward,
    detect_choch,
    detect_displacement,
    find_order_block,
)
from strategy.swing_detector import SwingPoint


def test_detects_bullish_choch(candles_from):
    candles = candles_from([[1.0, 1.5, 0.8, 2.1]])
    swings = [
        SwingPoint(index=1, price=1.0, type="LOW"),
        SwingPoint(index=2, price=2.0, type="HIGH"),
    ]

    assert detect_choch(candles, swings, "BUY") == {
        "type": "BULLISH_CHOCH",
        "level": 2.0,
        "index": 0,
    }


def test_detects_bearish_choch(candles_from):
    candles = candles_from([[1.0, 1.5, 0.8, 0.7]])
    swings = [
        SwingPoint(index=1, price=2.0, type="HIGH"),
        SwingPoint(index=2, price=0.8, type="LOW"),
    ]

    assert detect_choch(candles, swings, "SELL") == {
        "type": "BEARISH_CHOCH",
        "level": 0.8,
        "index": 0,
    }


def test_detects_bullish_displacement(candles_from):
    candles = candles_from(
        [
            [1.0, 1.2, 0.9, 1.1],
            [1.1, 1.3, 1.0, 1.2],
            [1.2, 1.8, 1.1, 1.7],
        ]
    )

    displacement = detect_displacement(candles, 2, "BUY", lookback=2, multiplier=1.5)

    assert displacement["type"] == "BULLISH_DISPLACEMENT"
    assert displacement["index"] == 2


def test_finds_bullish_order_block(candles_from):
    candles = candles_from(
        [
            [1.2, 1.3, 0.9, 1.0],
            [1.0, 1.8, 0.95, 1.7],
        ]
    )

    assert find_order_block(candles, before_index=1, direction="BUY") == {
        "type": "BULLISH_ORDER_BLOCK",
        "index": 0,
        "top": 1.2,
        "bottom": 0.9,
    }


def test_calculates_buy_risk_reward():
    assert calculate_risk_reward(entry=10, stop=9, target=13, direction="BUY") == 3


def test_rejects_invalid_risk_reward():
    assert calculate_risk_reward(entry=10, stop=11, target=13, direction="BUY") is None
