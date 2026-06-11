import sys
from pathlib import Path

import MetaTrader5 as mt5

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from broker.mt5_client import MT5Client


def main():
    client = MT5Client()

    try:
        client.connect()

        candles = client.get_candles("EURUSDm", mt5.TIMEFRAME_M5, 20)

        if candles is None:
            raise RuntimeError("No candles returned from MT5")

        print(candles)

    finally:
        client.shutdown()


if __name__ == "__main__":
    main()
