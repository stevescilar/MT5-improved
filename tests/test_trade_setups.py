import MetaTrader5 as mt5

from broker.mt5_client import MT5Client
from strategy.trade_setup import detect_trade_setup

client = MT5Client()

try:
    client.connect()

    candles = client.get_candles("XAUUSDm", mt5.TIMEFRAME_M5, 5000)

    setups = detect_trade_setup(candles, min_rr=1.5)

    print(f"\nTotal setups: {len(setups)}")

    valid = [s for s in setups if s.valid]

    print(f"Valid setups: {len(valid)}")

    for setup in setups[:10]:

        print("\n------------------")
        print("Direction:", setup.direction)
        print("Entry:", setup.entry)
        print("Stop:", setup.stop)
        print("Target:", setup.target)
        print("RR:", setup.risk_reward)
        print("Valid:", setup.valid)

finally:
    client.shutdown()
