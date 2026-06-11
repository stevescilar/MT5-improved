from strategy.liquidity import detect_liquidity_sweep
from strategy.swing_detector import SwingPoint


def test_detects_buy_side_liquidity_sweep(candles_from):
    candles = candles_from([[1.0, 2.2, 0.9, 1.8]])
    swings = [
        SwingPoint(index=1, price=1.0, type="LOW"),
        SwingPoint(index=2, price=2.0, type="HIGH"),
    ]

    assert detect_liquidity_sweep(candles, swings) == "BUY_SIDE_SWEEP"


def test_detects_sell_side_liquidity_sweep(candles_from):
    candles = candles_from([[1.0, 1.4, 0.7, 1.1]])
    swings = [
        SwingPoint(index=1, price=1.5, type="HIGH"),
        SwingPoint(index=2, price=0.8, type="LOW"),
    ]

    assert detect_liquidity_sweep(candles, swings) == "SELL_SIDE_SWEEP"


def test_returns_none_without_liquidity_sweep(candles_from):
    candles = candles_from([[1.0, 1.8, 1.1, 1.5]])
    swings = [
        SwingPoint(index=1, price=1.0, type="LOW"),
        SwingPoint(index=2, price=2.0, type="HIGH"),
    ]

    assert detect_liquidity_sweep(candles, swings) is None
