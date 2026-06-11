import sys
from pathlib import Path

import MetaTrader5 as mt5

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from broker.mt5_client import MT5Client
from strategy.bos import detect_bos
from strategy.swing_detector import detect_swings


def main():
    client = MT5Client()

    try:
        client.connect()

        candles = client.get_candles("XAUUSDm", mt5.TIMEFRAME_M5, 200)

        if candles is None:
            raise RuntimeError("No candles returned from MT5")

        swings = detect_swings(candles)
        bos = detect_bos(candles, swings)

        print("BOS:", bos)

    finally:
        client.shutdown()


if __name__ == "__main__":
    main()
