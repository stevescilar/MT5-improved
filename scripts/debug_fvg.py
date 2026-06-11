import sys
from pathlib import Path

import MetaTrader5 as mt5

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from broker.mt5_client import MT5Client
from strategy.fvg import detect_fvg


def main():
    client = MT5Client()

    try:
        client.connect()

        candles = client.get_candles("XAUUSDm", mt5.TIMEFRAME_M5, 1000)

        if candles is None:
            raise RuntimeError("No candles returned from MT5")

        fvgs = detect_fvg(candles)

        print(f"FVG Count: {len(fvgs)}")

        for fvg in fvgs[-5:]:
            print(fvg)

    finally:
        client.shutdown()


if __name__ == "__main__":
    main()
