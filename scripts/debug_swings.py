import sys
from pathlib import Path

import MetaTrader5 as mt5

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from broker.mt5_client import MT5Client
from strategy.swing_detector import detect_swings


def main():
    client = MT5Client()

    try:
        client.connect()

        candles = client.get_candles("XAUUSDm", mt5.TIMEFRAME_M5, 100)

        if candles is None:
            raise RuntimeError("No candles returned from MT5")

        swings = detect_swings(candles, lookback=3)

        print("SWINGS FOUND")

        for swing in swings[-10:]:
            print(swing.type, round(swing.price, 2))

    finally:
        client.shutdown()


if __name__ == "__main__":
    main()
