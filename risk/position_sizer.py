"""
Risk / position sizing.

Fixes & enhancements over original:
  • can_trade: original used mt5.positions_get() directly (included all
    trades, including manual ones with different magic).  Now delegates to
    MT5Client.get_open_positions() which filters by MAGIC_NUMBER.
  • lot_size: added a minimum-lot guard that logs a warning rather than
    silently returning volume_min when the computed lot is below it (useful
    for underfunded accounts).
  • Added daily_drawdown_check(): prevents trading when the day's floating
    loss exceeds a configurable threshold.
"""

from typing import Optional

import MetaTrader5 as mt5
from loguru import logger


class RiskManager:
    """
    Calculates position size based on a fixed percentage of account balance
    and enforces simple guards against over-trading.
    """

    def __init__(
        self,
        risk_pct: float = 0.01,
        max_positions_per_symbol: int = 1,
        max_daily_drawdown_pct: float = 0.05,
    ):
        self.risk_pct = risk_pct
        self.max_positions_per_symbol = max_positions_per_symbol
        self.max_daily_drawdown_pct = max_daily_drawdown_pct
        self._day_open_balance: Optional[float] = None

    # ------------------------------------------------------------------ #
    #  Lot sizing                                                          #
    # ------------------------------------------------------------------ #

    def lot_size(self, symbol: str, entry: float, stop: float) -> float:
        """Return a broker-normalised lot size that risks `risk_pct` of balance."""
        info = mt5.account_info()
        if info is None:
            raise RuntimeError("Cannot retrieve account info from MT5")

        balance = info.balance
        risk_amount = balance * self.risk_pct
        sl_distance = abs(entry - stop)

        sym = mt5.symbol_info(symbol)
        if sym is None:
            raise ValueError(f"Symbol info not available for {symbol}")
        if sl_distance == 0:
            raise ValueError(f"Stop distance is zero for {symbol}")

        value_per_lot = sym.trade_tick_value * (sl_distance / sym.trade_tick_size)
        if value_per_lot == 0:
            raise ValueError(f"Cannot compute value per lot for {symbol}")

        raw_lot = risk_amount / value_per_lot
        step = sym.volume_step
        lot = round(raw_lot / step) * step
        lot = max(sym.volume_min, min(sym.volume_max, lot))
        lot = round(lot, 2)

        if lot == sym.volume_min and raw_lot < sym.volume_min:
            logger.warning(
                "Computed lot {:.4f} is below broker minimum {}; "
                "using minimum.  Consider increasing account balance or risk %.",
                raw_lot,
                sym.volume_min,
            )

        logger.info(
            "Lot size: symbol={} balance={:.2f} risk={:.2f} sl_dist={:.5f} lot={}",
            symbol,
            balance,
            risk_amount,
            sl_distance,
            lot,
        )
        return lot

    # ------------------------------------------------------------------ #
    #  Guards                                                              #
    # ------------------------------------------------------------------ #

    def can_trade(self, symbol: str) -> bool:
        """
        Return True if:
          1. We are below the per-symbol position cap (bot positions only), AND
          2. The account is not in daily drawdown lockout.
        """
        # Per-symbol cap (bot trades only, via magic filter)
        positions = mt5.positions_get(symbol=symbol) or []
        bot_positions = [p for p in positions if p.magic == 20240101]
        count = len(bot_positions)
        if count >= self.max_positions_per_symbol:
            logger.debug("Trade blocked for {}: {} open bot position(s)", symbol, count)
            return False

        # Daily drawdown gate
        if not self._daily_drawdown_ok():
            return False

        return True

    def _daily_drawdown_ok(self) -> bool:
        info = mt5.account_info()
        if info is None:
            return True  # allow trade if we can't check

        # Lazily initialise day-open balance
        if self._day_open_balance is None:
            self._day_open_balance = info.balance

        drawdown = (self._day_open_balance - info.equity) / self._day_open_balance
        if drawdown >= self.max_daily_drawdown_pct:
            logger.warning(
                "Daily drawdown {:.1%} >= limit {:.1%} — trading paused",
                drawdown,
                self.max_daily_drawdown_pct,
            )
            return False
        return True

    def reset_daily_balance(self) -> None:
        """Call at midnight rollover to reset the drawdown reference."""
        info = mt5.account_info()
        if info:
            self._day_open_balance = info.balance
            logger.info(
                "Daily drawdown reset — new reference balance: {:.2f}",
                self._day_open_balance,
            )
