from typing import Optional

from strategy.market_structure import classify_structure
from strategy.models import TradeSetup
from strategy.swing_detector import detect_swings
from strategy.trade_setup import calculate_risk_reward, detect_trade_setup


def direction_from_structure(structure: Optional[str]) -> Optional[str]:
    if structure == "BULLISH":
        return "BUY"
    if structure == "BEARISH":
        return "SELL"
    return None


def analyze_market_bias(candles, lookback: int = 3, timeframe: str = "H4") -> dict:
    swings = detect_swings(candles, lookback=lookback)
    structure = classify_structure(swings)
    return {
        "timeframe": timeframe,
        "structure": structure,
        "bias": direction_from_structure(structure),
        "swings": swings,
    }


def analyze_structure(candles, lookback: int = 3, timeframe: str = "H1") -> dict:
    swings = detect_swings(candles, lookback=lookback)
    structure = classify_structure(swings)
    return {
        "timeframe": timeframe,
        "structure": structure,
        "direction": direction_from_structure(structure),
        "swings": swings,
    }


def choose_execution_levels(
    m15_setup: Optional[TradeSetup],
    m5_entry: Optional[TradeSetup],
    m1_refinement: Optional[TradeSetup],
) -> dict:
    execution = m1_refinement or m5_entry or m15_setup
    target_source = m15_setup or m5_entry or m1_refinement

    if execution is None or target_source is None:
        return {"entry": None, "stop": None, "target": None}

    return {
        "entry": execution.entry,
        "stop": execution.stop,
        "target": target_source.target,
    }


def analyze_multi_timeframe(
    h4_candles,
    h1_candles,
    m15_candles,
    m5_candles,
    m1_candles,
    lookback: int = 3,
    min_rr: float = 3.0,
) -> dict:
    h4 = analyze_market_bias(h4_candles, lookback=lookback, timeframe="H4")
    h1 = analyze_structure(h1_candles, lookback=lookback, timeframe="H1")

    direction = h4["bias"] if h4["bias"] == h1["direction"] else None

    m15_setup = detect_trade_setup(m15_candles, lookback=lookback, min_rr=0)
    m5_entry = detect_trade_setup(m5_candles, lookback=lookback, min_rr=0)
    m1_refine = detect_trade_setup(m1_candles, lookback=lookback, min_rr=0)

    levels = choose_execution_levels(m15_setup, m5_entry, m1_refine)
    risk_reward = None

    if direction and all(v is not None for v in levels.values()):
        risk_reward = calculate_risk_reward(
            levels["entry"], levels["stop"], levels["target"], direction
        )

    checks = {
        "h4_bias": h4["bias"] is not None,
        "h1_structure": h1["direction"] is not None,
        "bias_matches_structure": direction is not None,
        "m15_setup": m15_setup is not None
        and m15_setup.has_full_model()
        and m15_setup.direction == direction,
        "m5_entry": m5_entry is not None
        and m5_entry.has_entry_trigger()
        and m5_entry.direction == direction,
        "m1_refinement": m1_refine is not None
        and m1_refine.has_refinement()
        and m1_refine.direction == direction,
        "risk_reward": risk_reward is not None and risk_reward >= min_rr,
    }

    return {
        "h4": h4,
        "h1": h1,
        "m15": m15_setup,
        "m5": m5_entry,
        "m1": m1_refine,
        "checks": checks,
        "direction": direction,
        "levels": levels,
        "risk_reward": risk_reward,
        "valid": all(checks.values()),
    }
