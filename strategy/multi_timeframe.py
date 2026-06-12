"""
Multi-timeframe analysis.

Fixes & enhancements over original:
  • Pass HTF direction as `direction_filter` into detect_trade_setup so
    execution-TF scans only look for setups aligned with the bias (prevents
    counter-trend entries that were slipping through).
  • EURUSDm h4_bias=False / h1_structure=False was caused by classify_structure
    returning 'RANGING' (not None) while direction_from_structure returned None
    — checks now correctly show False.  (Fixed in market_structure.py.)
  • Added `h1_bos` check: requires a BOS on H1 confirming the bias before
    looking for entries.  This is the most common reason real setups are missed.
  • analyze_multi_timeframe now returns a `debug` key with per-TF detail for
    easier log analysis.
"""

from typing import Optional

from strategy.bos import detect_bos
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
    bos = detect_bos(candles, swings)
    return {
        "timeframe": timeframe,
        "structure": structure,
        "direction": direction_from_structure(structure),
        "bos": bos,
        "swings": swings,
    }


def choose_execution_levels(
    m15_setup: Optional[TradeSetup],
    m5_entry: Optional[TradeSetup],
    m1_refinement: Optional[TradeSetup],
) -> dict:
    # Prefer the finest confirmed refinement for entry/stop
    execution = m1_refinement or m5_entry or m15_setup
    # Use the widest confirmed setup for the target (higher TF = cleaner target)
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

    # Both HTF frames must agree on direction
    direction = h4["bias"] if h4["bias"] == h1["direction"] else None

    # H1 BOS in the direction of the bias adds confluence
    h1_bos_confirmed = (
        (
            h1["bos"] is not None
            and (
                (direction == "BUY" and h1["bos"] == "BULLISH_BOS")
                or (direction == "SELL" and h1["bos"] == "BEARISH_BOS")
            )
        )
        if direction
        else False
    )

    # Pass HTF direction into execution-TF scanners to avoid counter-trend setups
    m15_setup = detect_trade_setup(
        m15_candles, lookback=lookback, min_rr=0, direction_filter=direction
    )
    m5_entry = detect_trade_setup(
        m5_candles, lookback=lookback, min_rr=0, direction_filter=direction
    )
    m1_refine = detect_trade_setup(
        m1_candles, lookback=lookback, min_rr=0, direction_filter=direction
    )

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
        "h1_bos": h1_bos_confirmed,
        "m15_setup": (
            m15_setup is not None
            and m15_setup.has_full_model()
            and m15_setup.direction == direction
        ),
        "m5_entry": (
            m5_entry is not None
            and m5_entry.has_entry_trigger()
            and m5_entry.direction == direction
        ),
        "m1_refinement": (
            m1_refine is not None
            and m1_refine.has_refinement()
            and m1_refine.direction == direction
        ),
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
        # Debug extras
        "debug": {
            "h4_structure": h4["structure"],
            "h1_structure": h1["structure"],
            "h1_bos": h1.get("bos"),
            "h4_swing_count": len(h4["swings"]),
            "h1_swing_count": len(h1["swings"]),
        },
    }
