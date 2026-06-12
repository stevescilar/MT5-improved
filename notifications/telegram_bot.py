import asyncio
from typing import Optional

from loguru import logger

try:
    from telegram import Bot
    from telegram.error import TelegramError

    _TELEGRAM_AVAILABLE = True
except ImportError:
    _TELEGRAM_AVAILABLE = False


class TelegramNotifier:
    """
    Sends trade alerts and error notifications via Telegram.
    Silently no-ops when token/chat_id are not configured.
    """

    def __init__(self, token: Optional[str], chat_id: Optional[str]):
        self._enabled = bool(token and chat_id and _TELEGRAM_AVAILABLE)
        if self._enabled:
            self._bot = Bot(token=token)
            self._chat_id = chat_id
            logger.info("Telegram notifier enabled (chat_id={})", chat_id)
        else:
            logger.info("Telegram notifier disabled (token or chat_id missing)")

    def send(self, message: str) -> None:
        if not self._enabled:
            return
        try:
            asyncio.get_event_loop().run_until_complete(
                self._bot.send_message(chat_id=self._chat_id, text=message)
            )
        except Exception as exc:
            logger.warning("Telegram send failed: {}", exc)

    def trade_opened(
        self,
        symbol: str,
        direction: str,
        lot: float,
        entry: float,
        sl: float,
        tp: float,
        rr: float,
    ) -> None:
        msg = (
            f"🟢 *Trade Opened*\n"
            f"Symbol: `{symbol}`\n"
            f"Direction: `{direction}`\n"
            f"Lot: `{lot}`\n"
            f"Entry: `{entry}`  SL: `{sl}`  TP: `{tp}`\n"
            f"R:R  `{rr:.2f}`"
        )
        self.send(msg)

    def trade_closed(self, symbol: str, direction: str, pnl: float) -> None:
        icon = "💰" if pnl >= 0 else "🔴"
        msg = (
            f"{icon} *Trade Closed*\n"
            f"Symbol: `{symbol}`  Direction: `{direction}`\n"
            f"P&L: `{pnl:+.2f}`"
        )
        self.send(msg)

    def error(self, context: str, exc: Exception) -> None:
        msg = f"⚠️ *Error*\n`{context}`\n`{type(exc).__name__}: {exc}`"
        self.send(msg)

    def daily_summary(self, balance: float, equity: float, trades: int) -> None:
        msg = (
            f"📊 *Daily Summary*\n"
            f"Balance: `{balance:.2f}`  Equity: `{equity:.2f}`\n"
            f"Trades today: `{trades}`"
        )
        self.send(msg)
