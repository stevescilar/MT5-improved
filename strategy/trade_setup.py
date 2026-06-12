from bisect import bisect_left
from typing import Optional

from strategy.fvg import detect_fvg, is_fvg_filled
from strategy.models import DisplacementRef, FVGRef, OrderBlockRef, SwingRef, TradeSetup
from strategy.swing_detector import SwingPoint, detect_swings


def latest_high_low(
    swings: list[SwingPoint],
) -> tuple[Optional[SwingPoint], Optional[SwingPoint]]:
    last_high = None
    last_low = None
    for swing in reversed(swings):
        if swing.type == "HIGH" and last_high is None:
            last_high = swing
        if swing.type == "LOW" and last_low is None:
            last_low = swing
        if last_high and last_low:
            break
    return last_high, last_low


def detect_choch(
    candles, swings: list[SwingPoint], direction: str, index: Optional[int] = None
) -> Optional[SwingRef]:
    """Detect a Change of Character at a given candle index (defaults to last candle)."""
    if index is None:
        index = len(candles) - 1
    current_close = candles.iloc[index]["close"]
    last_high, last_low = latest_high_low(swings)

    if direction == "BUY" and last_high and current_close > last_high.price:
        return SwingRef(type="BULLISH_CHOCH", level=last_high.price, index=index)
    if direction == "SELL" and last_low and current_close < last_low.price:
        return SwingRef(type="BEARISH_CHOCH", level=last_low.price, index=index)
    return None


def detect_liquidity_sweep_at(
    candles, index: int, swings: list[SwingPoint]
) -> Optional[str]:
    if len(swings) < 2:
        return None
    current = candles.iloc[index]
    last_high, last_low = latest_high_low(swings)

    if (
        last_high
        and current["high"] > last_high.price
        and current["close"] < last_high.price
    ):
        return "BUY_SIDE_SWEEP"
    if (
        last_low
        and current["low"] < last_low.price
        and current["close"] > last_low.price
    ):
        return "SELL_SIDE_SWEEP"
    return None


def detect_displacement(
    candles, index: int, direction: str, lookback: int = 10, multiplier: float = 1.5
) -> Optional[DisplacementRef]:
    if index <= 0:
        return None
    start = max(0, index - lookback)
    previous = candles.iloc[start:index]
    if previous.empty:
        return None

    candle = candles.iloc[index]
    body = abs(candle["close"] - candle["open"])
    average_body = (previous["close"] - previous["open"]).abs().mean()
    if average_body == 0:
        return None

    bullish = candle["close"] > candle["open"]
    bearish = candle["close"] < candle["open"]

    if direction == "BUY" and bullish and body >= average_body * multiplier:
        return DisplacementRef(type="BULLISH_DISPLACEMENT", index=index, body=body)
    if direction == "SELL" and bearish and body >= average_body * multiplier:
        return DisplacementRef(type="BEARISH_DISPLACEMENT", index=index, body=body)
    return None


def find_order_block(
    candles, before_index: int, direction: str, max_lookback: int = 20
) -> Optional[OrderBlockRef]:
    limit = max(0, before_index - max_lookback)
    for i in range(before_index - 1, limit - 1, -1):
        candle = candles.iloc[i]
        if direction == "BUY" and candle["close"] < candle["open"]:
            return OrderBlockRef(
                type="BULLISH_ORDER_BLOCK",
                index=i,
                top=candle["open"],
                bottom=candle["low"],
            )
        if direction == "SELL" and candle["close"] > candle["open"]:
            return OrderBlockRef(
                type="BEARISH_ORDER_BLOCK",
                index=i,
                top=candle["high"],
                bottom=candle["open"],
            )
    return None


def calculate_risk_reward(
    entry: float, stop: float, target: float, direction: str
) -> Optional[float]:
    if direction == "BUY":
        risk = entry - stop
        reward = target - entry
    else:
        risk = stop - entry
        reward = entry - target
    if risk <= 0 or reward <= 0:
        return None
    return reward / risk


def find_target(swings: list[SwingPoint], direction: str) -> Optional[float]:
    target_type = "HIGH" if direction == "BUY" else "LOW"
    for swing in reversed(swings):
        if swing.type == target_type:
            return swing.price
    return None


def detect_trade_setup(
    candles, lookback: int = 3, min_rr: float = 3.0, max_scan: int = 80
) -> Optional[TradeSetup]:
    all_swings = detect_swings(candles, lookback=lookback)
    all_fvgs = detect_fvg(candles)
    # Pre-filter: only unfilled FVGs
    open_fvgs = [fvg for fvg in all_fvgs if not is_fvg_filled(fvg, candles)]

    # Build index → swing mapping for O(log n) slicing
    swing_indices = [s.index for s in all_swings]

    def swings_before(idx: int) -> list[SwingPoint]:
        pos = bisect_left(swing_indices, idx)
        return all_swings[:pos]

    start_index = max(lookback + 1, len(candles) - max_scan)
    latest_setup: Optional[TradeSetup] = None

    for sweep_index in range(start_index, len(candles)):
        sweep_swings = swings_before(sweep_index)
        sweep = detect_liquidity_sweep_at(candles, sweep_index, sweep_swings)

        if sweep == "SELL_SIDE_SWEEP":
            direction = "BUY"
        elif sweep == "BUY_SIDE_SWEEP":
            direction = "SELL"
        else:
            continue

        setup = TradeSetup(
            direction=direction,
            sweep={"type": sweep, "index": sweep_index},
        )

        for index in range(sweep_index + 1, len(candles)):
            current_swings = swings_before(index)

            if setup.choch is None:
                setup.choch = detect_choch(candles, current_swings, direction, index)

            if setup.choch is None:
                continue

            if setup.displacement is None:
                setup.displacement = detect_displacement(candles, index, direction)

            if setup.displacement is None:
                continue

            fvg_type = "BULLISH" if direction == "BUY" else "BEARISH"
            relevant_fvgs = [
                fvg
                for fvg in open_fvgs
                if fvg["type"] == fvg_type
                and setup.displacement.index <= fvg["index"] <= index
            ]

            if not relevant_fvgs:
                continue

            raw_fvg = relevant_fvgs[-1]
            setup.fvg = FVGRef(
                type=raw_fvg["type"],
                top=raw_fvg["top"],
                bottom=raw_fvg["bottom"],
                index=raw_fvg["index"],
            )

            setup.order_block = find_order_block(
                candles, setup.displacement.index, direction
            )
            if setup.order_block is None:
                continue

            if direction == "BUY":
                setup.entry = (setup.fvg.top + setup.fvg.bottom) / 2
                setup.stop = min(
                    setup.order_block.bottom, candles.iloc[sweep_index]["low"]
                )
            else:
                setup.entry = (setup.fvg.top + setup.fvg.bottom) / 2
                setup.stop = max(
                    setup.order_block.top, candles.iloc[sweep_index]["high"]
                )

            setup.target = find_target(current_swings, direction)
            if setup.target is None:
                continue

            setup.risk_reward = calculate_risk_reward(
                setup.entry, setup.stop, setup.target, direction
            )
            setup.valid = setup.risk_reward is not None and setup.risk_reward >= min_rr

            latest_setup = setup
            break

    return latest_setup
