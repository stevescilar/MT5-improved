import sys
from pathlib import Path

import MetaTrader5 as mt5

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from broker.mt5_client import MT5Client
from strategy.bos import detect_bos
from strategy.fvg import detect_fvg
from strategy.liquidity import detect_liquidity_sweep
from strategy.market_structure import classify_structure
from strategy.swing_detector import detect_swings
from strategy.trade_setup import detect_trade_setup


def status(value):
    return "YES" if value else "NO"


def main():
    client = MT5Client()

    try:
        client.connect()

        candles = client.get_candles("XAUUSDm", mt5.TIMEFRAME_M5, 300)

        if candles is None:
            raise RuntimeError("No candles returned from MT5")

        swings = detect_swings(candles)
        trend = classify_structure(swings)
        bos = detect_bos(candles, swings)
        sweep = detect_liquidity_sweep(candles, swings)
        fvgs = detect_fvg(candles)
        setup = detect_trade_setup(candles)

        print("MARKET SNAPSHOT")
        print("Symbol: XAUUSDm")
        print("Timeframe: M5")
        print("Trend:", trend)
        print("BOS:", bos)
        print("Current Candle Sweep:", sweep)
        print("FVG Count:", len(fvgs))
        print()

        print("RECENT SWINGS")
        for swing in swings[-10:]:
            print(swing.index, swing.type, round(swing.price, 2))

        print()
        print("TRADE FILTER")

        if setup is None:
            print("Valid Setup: NO")
            print("Reason: no recent liquidity sweep started the full model")
            return

        print("Direction:", setup["direction"])
        print("Liquidity Sweep:", status(setup["sweep"]))
        print("CHOCH:", status(setup["choch"]))
        print("Displacement:", status(setup["displacement"]))
        print("FVG:", status(setup["fvg"]))
        print("Order Block:", status(setup["order_block"]))
        print("Risk Reward >= 1:3:", status(setup["valid"]))
        print("Valid Setup:", status(setup["valid"]))

        if setup["entry"] is not None:
            print()
            print("LEVELS")
            print("Entry:", round(setup["entry"], 2))
            print("Stop:", round(setup["stop"], 2))
            print("Target:", round(setup["target"], 2))
            print("RR:", round(setup["risk_reward"], 2))

    finally:
        client.shutdown()


if __name__ == "__main__":
    main()
