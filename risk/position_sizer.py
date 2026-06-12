import MetaTrader5 as mt5
from loguru import logger


class RiskManager:
    """
    Calculates position size based on a fixed percentage of account balance,
    and enforces simple guards against over-trading.
    """

    def __init__(self, risk_pct: float = 0.01, max_positions_per_symbol: int = 1):
        self.risk_pct = risk_pct
        self.max_positions_per_symbol = max_positions_per_symbol

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

        # Value per 1 lot for the SL distance
        value_per_lot = sym.trade_tick_value * (sl_distance / sym.trade_tick_size)
        if value_per_lot == 0:
            raise ValueError(f"Cannot compute value per lot for {symbol}")

        raw_lot = risk_amount / value_per_lot
        # Normalise to broker step / min / max
        step = sym.volume_step
        lot = round(raw_lot / step) * step
        lot = max(sym.volume_min, min(sym.volume_max, lot))
        lot = round(lot, 2)

        logger.info(
            "Lot size: symbol={} balance={:.2f} risk={:.2f} sl_dist={} lot={}",
            symbol,
            balance,
            risk_amount,
            sl_distance,
            lot,
        )
        return lot

    def can_trade(self, symbol: str) -> bool:
        """Return True if we are below the per-symbol position cap."""
        positions = mt5.positions_get(symbol=symbol)
        count = len(positions) if positions else 0
        allowed = count < self.max_positions_per_symbol
        if not allowed:
            logger.debug("Trade blocked for {}: {} open position(s)", symbol, count)
        return allowed
