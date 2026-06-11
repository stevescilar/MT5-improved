from strategy.market_structure import classify_structure
from strategy.swing_detector import detect_swings
from strategy.trade_setup import calculate_risk_reward, detect_trade_setup


def direction_from_structure(structure):

    if structure == "BULLISH":
        return "BUY"

    if structure == "BEARISH":
        return "SELL"

    return None


def analyze_market_bias(candles, lookback=3):

    swings = detect_swings(candles, lookback=lookback)
    structure = classify_structure(swings)

    return {
        "timeframe": "H4",
        "structure": structure,
        "bias": direction_from_structure(structure),
        "swings": swings,
    }


def analyze_structure(candles, lookback=3):

    swings = detect_swings(candles, lookback=lookback)
    structure = classify_structure(swings)

    return {
        "timeframe": "H1",
        "structure": structure,
        "direction": direction_from_structure(structure),
        "swings": swings,
    }


def has_full_setup_model(setup, direction):

    return (
        setup is not None
        and setup["direction"] == direction
        and setup["sweep"] is not None
        and setup["choch"] is not None
        and setup["displacement"] is not None
        and setup["fvg"] is not None
        and setup["order_block"] is not None
    )


def has_entry_trigger(setup, direction):

    return (
        setup is not None
        and setup["direction"] == direction
        and setup["choch"] is not None
        and setup["displacement"] is not None
        and setup["entry"] is not None
        and setup["stop"] is not None
    )


def has_refinement(setup, direction):

    return (
        setup is not None
        and setup["direction"] == direction
        and setup["entry"] is not None
        and setup["stop"] is not None
    )


def choose_execution_levels(m15_setup, m5_entry, m1_refinement):

    execution = m1_refinement or m5_entry or m15_setup
    target_source = m15_setup or m5_entry or m1_refinement

    if execution is None or target_source is None:
        return {
            "entry": None,
            "stop": None,
            "target": None,
        }

    return {
        "entry": execution["entry"],
        "stop": execution["stop"],
        "target": target_source["target"],
    }


def analyze_multi_timeframe(
    h4_candles,
    h1_candles,
    m15_candles,
    m5_candles,
    m1_candles,
    lookback=3,
    min_rr=3.0,
):

    h4 = analyze_market_bias(h4_candles, lookback=lookback)
    h1 = analyze_structure(h1_candles, lookback=lookback)
    direction = h4["bias"] if h4["bias"] == h1["direction"] else None
    m15_setup = detect_trade_setup(m15_candles, lookback=lookback, min_rr=0)
    m5_entry = detect_trade_setup(m5_candles, lookback=lookback, min_rr=0)
    m1_refinement = detect_trade_setup(m1_candles, lookback=lookback, min_rr=0)
    levels = choose_execution_levels(m15_setup, m5_entry, m1_refinement)
    risk_reward = None

    if direction and all(levels.values()):
        risk_reward = calculate_risk_reward(
            levels["entry"],
            levels["stop"],
            levels["target"],
            direction,
        )

    checks = {
        "h4_bias": h4["bias"] is not None,
        "h1_structure": h1["direction"] is not None,
        "bias_matches_structure": direction is not None,
        "m15_setup": has_full_setup_model(m15_setup, direction),
        "m5_entry": has_entry_trigger(m5_entry, direction),
        "m1_refinement": has_refinement(m1_refinement, direction),
        "risk_reward": risk_reward is not None and risk_reward >= min_rr,
    }

    return {
        "h4": h4,
        "h1": h1,
        "m15": m15_setup,
        "m5": m5_entry,
        "m1": m1_refinement,
        "checks": checks,
        "direction": direction,
        "levels": levels,
        "risk_reward": risk_reward,
        "valid": all(checks.values()),
    }
