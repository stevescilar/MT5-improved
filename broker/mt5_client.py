import time

import MetaTrader5 as mt5
import pandas as pd
from loguru import logger

from config import LOGIN, PASSWORD, SERVER

MAGIC_NUMBER = 20240101


class MT5Client:

    # ------------------------------------------------------------------ #
    #  Connection                                                          #
    # ------------------------------------------------------------------ #

    def connect(self, retries: int = 5, delay: int = 10) -> None:
        if not PASSWORD:
            raise ValueError("MT5_PASSWORD environment variable is not set")

        for attempt in range(1, retries + 1):
            try:
                if not mt5.initialize():
                    raise ConnectionError(f"MT5 initialize failed: {mt5.last_error()}")
                if not mt5.login(LOGIN, PASSWORD, SERVER):
                    raise ConnectionError(f"MT5 login failed: {mt5.last_error()}")
                logger.info("MT5 connected (login={}, server={})", LOGIN, SERVER)
                return
            except Exception as exc:
                logger.warning(
                    "Connect attempt {}/{} failed: {}", attempt, retries, exc
                )
                if attempt < retries:
                    backoff = delay * (2 ** (attempt - 1))
                    logger.info("Retrying in {} seconds…", backoff)
                    time.sleep(backoff)

        raise RuntimeError(f"Could not connect to MT5 after {retries} attempts")

    def shutdown(self) -> None:
        mt5.shutdown()
        logger.info("MT5 disconnected")

    # ------------------------------------------------------------------ #
    #  Account                                                             #
    # ------------------------------------------------------------------ #

    def account_info(self):
        return mt5.account_info()

    # ------------------------------------------------------------------ #
    #  Market data                                                         #
    # ------------------------------------------------------------------ #

    def get_candles(
        self, symbol: str, timeframe: int, count: int = 500
    ) -> pd.DataFrame | None:
        info = mt5.symbol_info(symbol)
        if info is None:
            logger.warning("Symbol not found: {}", symbol)
            return None

        if not info.visible:
            mt5.symbol_select(symbol, True)

        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None:
            logger.error("Failed to fetch candles for {}: {}", symbol, mt5.last_error())
            return None

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")

        assert df[
            "time"
        ].is_monotonic_increasing, f"Candles for {symbol} are not time-ordered"
        assert len(df) == count, f"Expected {count} candles for {symbol}, got {len(df)}"

        return df

    # ------------------------------------------------------------------ #
    #  Order execution                                                     #
    # ------------------------------------------------------------------ #

    def place_order(
        self,
        symbol: str,
        direction: str,
        lot: float,
        sl: float,
        tp: float,
        comment: str = "",
    ) -> dict:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(f"Cannot get tick for {symbol}")

        if direction == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        else:
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 10,
            "magic": MAGIC_NUMBER,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(
                f"Order failed for {symbol} {direction}: "
                f"retcode={result.retcode}, comment={result.comment}"
            )

        logger.info(
            "Order placed: {} {} lot={} entry={} sl={} tp={} ticket={}",
            symbol,
            direction,
            lot,
            price,
            sl,
            tp,
            result.order,
        )
        return result._asdict()

    def close_position(
        self, ticket: int, symbol: str, lot: float, direction: str
    ) -> dict:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(f"Cannot get tick for {symbol}")

        if direction == "BUY":
            close_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            close_type = mt5.ORDER_TYPE_BUY
            price = tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": symbol,
            "volume": lot,
            "type": close_type,
            "price": price,
            "deviation": 10,
            "magic": MAGIC_NUMBER,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(
                f"Close failed for ticket={ticket}: "
                f"retcode={result.retcode}, comment={result.comment}"
            )

        logger.info("Position closed: ticket={} symbol={}", ticket, symbol)
        return result._asdict()

    def get_open_positions(self, symbol: str | None = None) -> list:
        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        return list(positions) if positions else []
