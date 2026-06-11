import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from broker.mt5_client import MT5Client


def main():
    client = MT5Client()

    try:
        client.connect()

        info = client.account_info()

        if info is None:
            raise RuntimeError("No account info returned from MT5")

        print("Connected Successfully")
        print(f"Login: {info.login}")
        print(f"Balance: {info.balance}")
        print(f"Equity: {info.equity}")
        print(f"Server: {info.server}")

    finally:
        client.shutdown()


if __name__ == "__main__":
    main()
