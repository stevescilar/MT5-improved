import MetaTrader5 as mt5

from broker.mt5_client import MT5Client
from strategy.trade_setup import (
    detect_trade_setup,
    detect_liquidity_sweep_at,
    detect_choch,
    detect_displacement,
    find_order_block,
)
from strategy.fvg import detect_fvg, is_fvg_filled
from strategy.swing_detector import detect_swings


def test_setup_statistics():

    client = MT5Client()

    try:
        client.connect()

        candles = client.get_candles(
            "XAUUSDm",
            mt5.TIMEFRAME_M5,
            5000,
        )

        assert candles is not None
        assert len(candles) > 500

        swings = detect_swings(candles)

        stats = {
            "sweeps": 0,
            "choch": 0,
            "displacement": 0,
            "fvg": 0,
            "order_block": 0,
            "rr": 0,
            "valid": 0,
        }

        all_fvgs = detect_fvg(candles)

        open_fvgs = [fvg for fvg in all_fvgs if not is_fvg_filled(fvg, candles)]

        for idx in range(20, len(candles)):

            current_swings = [s for s in swings if s.index < idx]

            if len(current_swings) < 2:
                continue

            sweep = detect_liquidity_sweep_at(candles, idx, current_swings)

            if not sweep:
                continue

            stats["sweeps"] += 1

            direction = "BUY" if sweep == "SELL_SIDE_SWEEP" else "SELL"

            choch = detect_choch(candles, current_swings, direction, idx)

            if not choch:
                continue

            stats["choch"] += 1

            displacement = detect_displacement(candles, idx, direction)

            if not displacement:
                continue

            stats["displacement"] += 1

            fvg_type = "BULLISH" if direction == "BUY" else "BEARISH"

            relevant_fvgs = [fvg for fvg in open_fvgs if fvg["type"] == fvg_type]

            if not relevant_fvgs:
                continue

            stats["fvg"] += 1

            ob = find_order_block(candles, displacement.index, direction)

            if not ob:
                continue

            stats["order_block"] += 1

        print("\n" + "=" * 50)
        print("SMC STATISTICS")
        print("=" * 50)

        for key, value in stats.items():
            print(f"{key:<15}: {value}")

        print("=" * 50)

    finally:
        client.shutdown()


if __name__ == "__main__":
    test_setup_statistics()
