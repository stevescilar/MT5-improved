from strategy.multi_timeframe import (
    analyze_market_bias,
    analyze_structure,
    direction_from_structure,
    has_entry_trigger,
    has_full_setup_model,
    has_refinement,
)


def test_direction_from_structure():
    assert direction_from_structure("BULLISH") == "BUY"
    assert direction_from_structure("BEARISH") == "SELL"
    assert direction_from_structure("RANGING") is None
    assert direction_from_structure(None) is None


def test_h4_bias_uses_market_structure(candles_from):
    candles = candles_from(
        [
            [1.0, 1.4, 1.0, 1.2],
            [1.2, 1.3, 0.8, 1.0],
            [1.0, 2.0, 1.1, 1.8],
            [1.8, 1.7, 1.3, 1.4],
            [1.4, 1.8, 1.1, 1.6],
            [1.6, 2.4, 1.4, 2.2],
            [2.2, 2.1, 1.5, 1.8],
        ]
    )

    bias = analyze_market_bias(candles, lookback=1)

    assert bias["structure"] == "BULLISH"
    assert bias["bias"] == "BUY"


def test_h1_structure_maps_to_direction(candles_from):
    candles = candles_from(
        [
            [2.0, 2.1, 1.6, 1.8],
            [1.8, 2.4, 1.7, 2.2],
            [2.2, 2.0, 1.2, 1.4],
            [1.4, 1.9, 1.5, 1.7],
            [1.7, 2.0, 1.1, 1.3],
            [1.3, 1.6, 0.8, 1.0],
            [1.0, 1.5, 0.9, 1.2],
        ]
    )

    structure = analyze_structure(candles, lookback=1)

    assert structure["structure"] == "BEARISH"
    assert structure["direction"] == "SELL"


def test_full_setup_model_does_not_require_valid_rr():
    setup = {
        "direction": "BUY",
        "sweep": {"type": "SELL_SIDE_SWEEP"},
        "choch": {"type": "BULLISH_CHOCH"},
        "displacement": {"type": "BULLISH_DISPLACEMENT"},
        "fvg": {"type": "BULLISH"},
        "order_block": {"type": "BULLISH_ORDER_BLOCK"},
        "valid": False,
    }

    assert has_full_setup_model(setup, "BUY")


def test_entry_trigger_requires_direction_and_execution_levels():
    setup = {
        "direction": "SELL",
        "choch": {"type": "BEARISH_CHOCH"},
        "displacement": {"type": "BEARISH_DISPLACEMENT"},
        "entry": 10,
        "stop": 11,
    }

    assert has_entry_trigger(setup, "SELL")
    assert not has_entry_trigger(setup, "BUY")


def test_refinement_requires_entry_and_stop():
    setup = {
        "direction": "BUY",
        "entry": 10,
        "stop": 9,
    }

    assert has_refinement(setup, "BUY")
