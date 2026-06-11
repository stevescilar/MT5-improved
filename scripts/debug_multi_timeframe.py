import sys
from pathlib import Path

import MetaTrader5 as mt5

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from broker.mt5_client import MT5Client
from strategy.multi_timeframe import analyze_multi_timeframe


TIMEFRAMES = {
    "H4": mt5.TIMEFRAME_H4,
    "H1": mt5.TIMEFRAME_H1,
    "M15": mt5.TIMEFRAME_M15,
    "M5": mt5.TIMEFRAME_M5,
    "M1": mt5.TIMEFRAME_M1,
}


def status(value):
    return "YES" if value else "NO"


def setup_status(setup):
    if setup is None:
        return "NO SETUP"

    return setup["direction"]


def print_setup(label, setup, show_rr=False):
    print(f"{label}: {setup_status(setup)}")

    if setup is None:
        return

    print("  Liquidity Sweep:", status(setup["sweep"]))
    print("  CHOCH:", status(setup["choch"]))
    print("  Displacement:", status(setup["displacement"]))
    print("  FVG:", status(setup["fvg"]))
    print("  Order Block:", status(setup["order_block"]))
    if show_rr:
        print("  RR >= 1:3:", status(setup["valid"]))

    if setup["entry"] is not None:
        print("  Entry:", round(setup["entry"], 2))
        print("  Stop:", round(setup["stop"], 2))
        print("  Target:", round(setup["target"], 2))

        if setup["risk_reward"] is None:
            print("  RR: invalid")
        else:
            print("  RR:", round(setup["risk_reward"], 2))


def main():
    symbol = "XAUUSDm"
    client = MT5Client()

    try:
        client.connect()

        candles = {
            name: client.get_candles(symbol, timeframe, 300)
            for name, timeframe in TIMEFRAMES.items()
        }

        missing = [name for name, data in candles.items() if data is None]

        if missing:
            raise RuntimeError(f"No candles returned for: {', '.join(missing)}")

        analysis = analyze_multi_timeframe(
            candles["H4"],
            candles["H1"],
            candles["M15"],
            candles["M5"],
            candles["M1"],
        )

        print("MULTI-TIMEFRAME MODEL")
        print("Symbol:", symbol)
        print()

        print("H4 Market Bias:", analysis["h4"]["structure"], analysis["h4"]["bias"])
        print("H1 Structure:", analysis["h1"]["structure"], analysis["h1"]["direction"])
        print("Bias Matches Structure:", status(analysis["checks"]["bias_matches_structure"]))
        print("Model Direction:", analysis["direction"])
        print()

        print_setup("M15 Setup - full model", analysis["m15"])
        print()
        print_setup("M5 Entry - timing trigger", analysis["m5"])
        print()
        print_setup("M1 Refinement - tighter execution", analysis["m1"])
        print()

        print("FINAL EXECUTION")
        levels = analysis["levels"]
        if levels["entry"] is None:
            print("Entry: None")
            print("Stop: None")
            print("Target: None")
        else:
            print("Entry:", round(levels["entry"], 2))
            print("Stop:", round(levels["stop"], 2))
            print("Target:", round(levels["target"], 2))

        if analysis["risk_reward"] is None:
            print("RR: invalid")
        else:
            print("RR:", round(analysis["risk_reward"], 2))

        print("RR >= 1:3:", status(analysis["checks"]["risk_reward"]))
        print()

        print("CHECKLIST")
        for name, passed in analysis["checks"].items():
            print(name + ":", status(passed))

        print()
        print("VALID TRADE:", status(analysis["valid"]))

    finally:
        client.shutdown()


if __name__ == "__main__":
    main()
