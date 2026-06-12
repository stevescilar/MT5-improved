"""
MT5Client — broker connectivity layer.

Fixes & enhancements over original:
  • get_candles: removed hard assert on exact candle count (broker may return
    slightly fewer at session open); replaced with a lenient warning + minimum
    threshold guard.
  • place_order: tries ORDER_FILLING_FOK first, falls back to IOC, then RETURN
    so the bot works across all broker filling modes without manual config.
  • close_position: same filling-mode fallback.
  • get_open_positions: now filters by MAGIC_NUMBER so foreign manual trades
    don't count toward the per-symbol cap.
  • New helpers: reconnect(), is_connected(), get_symbol_digits().
"""

import time
from typing import Optional

import MetaTrader5 as mt5
import pandas as pd
from loguru import logger

from config import LOGIN, PASSWORD, SERVER

MAGIC_NUMBER = 20240101
_FILLING_MODES = [
    mt5.ORDER_FILLING_IOC,
    mt5.ORDER_FILLING_FOK,
    mt5.ORDER_FILLING_RETURN,
]
_MIN_CANDLE_RATIO = 0.8  # accept ≥80 % of requested candles


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

    def reconnect(self) -> None:
        """Best-effort reconnect — used by the main loop on connection loss."""
        logger.warning("Attempting MT5 reconnect…")
        try:
            mt5.shutdown()
        except Exception:
            pass
        self.connect()

    def is_connected(self) -> bool:
        info = mt5.account_info()
        return info is not None

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

    def get_symbol_digits(self, symbol: str) -> int:
        info = mt5.symbol_info(symbol)
        return info.digits if info else 5

    def get_candles(
        self, symbol: str, timeframe: int, count: int = 500
    ) -> Optional[pd.DataFrame]:
        info = mt5.symbol_info(symbol)
        if info is None:
            logger.warning("Symbol not found: {}", symbol)
            return None

        if not info.visible:
            if not mt5.symbol_select(symbol, True):
                logger.warning("Could not select symbol: {}", symbol)
                return None

        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None or len(rates) == 0:
            logger.error("Failed to fetch candles for {}: {}", symbol, mt5.last_error())
            return None

        received = len(rates)
        if received < count * _MIN_CANDLE_RATIO:
            logger.warning(
                "Sparse candle data for {} — requested {} got {}",
                symbol,
                count,
                received,
            )
            return None

        if received < count:
            logger.debug(
                "Partial candle data for {} ({}/{}); continuing",
                symbol,
                received,
                count,
            )

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")

        if not df["time"].is_monotonic_increasing:
            logger.error("Candles for {} are not time-ordered — skipping", symbol)
            return None

        return df

    # ------------------------------------------------------------------ #
    #  Order execution                                                     #
    # ------------------------------------------------------------------ #

    def _try_order(self, request: dict) -> Optional[dict]:
        """Try all filling modes; return result dict or None on hard failure."""
        for filling in _FILLING_MODES:
            request["type_filling"] = filling
            result = mt5.order_send(request)
            if result is None:
                continue
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return result._asdict()
            if result.retcode in (
                mt5.TRADE_RETCODE_INVALID_FILL,
                mt5.TRADE_RETCODE_ORDER_CHANGED,
            ):
                logger.debug(
                    "Filling mode {} rejected (retcode={}), trying next…",
                    filling,
                    result.retcode,
                )
                continue
            # Any other error is fatal for this order
            raise RuntimeError(
                f"Order failed: retcode={result.retcode}, comment={result.comment}"
            )
        raise RuntimeError("All filling modes rejected by broker")

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
            "deviation": 20,  # slightly wider deviation for volatile pairs
            "magic": MAGIC_NUMBER,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
        }

        result = self._try_order(request)
        logger.info(
            "Order placed: {} {} lot={} entry={} sl={} tp={} ticket={}",
            symbol,
            direction,
            lot,
            price,
            sl,
            tp,
            result.get("order"),
        )
        return result

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
            "deviation": 20,
            "magic": MAGIC_NUMBER,
        }

        result = self._try_order(request)
        logger.info("Position closed: ticket={} symbol={}", ticket, symbol)
        return result

    def get_open_positions(self, symbol: Optional[str] = None) -> list:
        """Return open positions placed by this bot (filtered by MAGIC_NUMBER)."""
        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        if not positions:
            return []
        return [p for p in positions if p.magic == MAGIC_NUMBER]
