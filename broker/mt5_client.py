
import MetaTrader5 as mt5
import pandas as pd
from config import LOGIN, PASSWORD, SERVER


class MT5Client:

    def connect(self):

        if not PASSWORD:
            raise ValueError("MT5_PASSWORD is not set")

        if not mt5.initialize():
            raise Exception(f"MT5 Initialize Failed: {mt5.last_error()}")

        authorized = mt5.login(LOGIN, PASSWORD, SERVER)

        if not authorized:
            raise Exception(f"MT5 Login Failed: {mt5.last_error()}")

        print("MT5 Connected")

    def account_info(self):
        return mt5.account_info()

    def shutdown(self):
        mt5.shutdown()

    def get_candles(self, symbol, timeframe, count=500):

        info = mt5.symbol_info(symbol)

        if info is None:
            print(f"Symbol not found: {symbol}")
            return None

        if not info.visible:
            mt5.symbol_select(symbol, True)

        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)

        if rates is None:
            print(f"Failed to get candles for {symbol}")
            print(mt5.last_error())
            return None

        df = pd.DataFrame(rates)

        df["time"] = pd.to_datetime(df["time"], unit="s")

        return df
