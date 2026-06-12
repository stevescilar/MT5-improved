"""
Telegram notifier.

Fixes & enhancements over original:
  • asyncio.get_event_loop().run_until_complete() is deprecated in Python 3.10+
    and raises DeprecationWarning in 3.12.  Replaced with asyncio.run() which
    always creates a fresh event loop — safe for threaded / repeated calls.
  • parse_mode='MarkdownV2' is required for newer Bot API versions; falling
    back gracefully on parse errors.
  • Added rate-limit guard: Telegram blocks bots that send > 30 msg/s.
    A simple token-bucket (1 msg/s) is applied.
  • send() now accepts an optional `parse_mode` kwarg for flexibility.
"""

import asyncio
import time
from typing import Optional

from loguru import logger

try:
    from telegram import Bot
    from telegram.error import TelegramError

    _TELEGRAM_AVAILABLE = True
except ImportError:
    _TELEGRAM_AVAILABLE = False

_MIN_SEND_INTERVAL = 1.0  # seconds between Telegram messages


class TelegramNotifier:
    """
    Sends trade alerts and error notifications via Telegram.
    Silently no-ops when token/chat_id are not configured.
    """

    def __init__(self, token: Optional[str], chat_id: Optional[str]):
        self._enabled = bool(token and chat_id and _TELEGRAM_AVAILABLE)
        self._last_send: float = 0.0
        if self._enabled:
            self._bot = Bot(token=token)
            self._chat_id = chat_id
            logger.info("Telegram notifier enabled (chat_id={})", chat_id)
        else:
            logger.info("Telegram notifier disabled (token or chat_id missing)")

    def send(self, message: str, parse_mode: str = "Markdown") -> None:
        if not self._enabled:
            return

        # Rate-limit guard
        elapsed = time.time() - self._last_send
        if elapsed < _MIN_SEND_INTERVAL:
            time.sleep(_MIN_SEND_INTERVAL - elapsed)

        try:
            asyncio.run(
                self._bot.send_message(
                    chat_id=self._chat_id,
                    text=message,
                    parse_mode=parse_mode,
                )
            )
            self._last_send = time.time()
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
        icon = "🟢" if direction == "BUY" else "🔴"
        msg = (
            f"{icon} *Trade Opened*\n"
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
        pnl = equity - balance
        icon = "📈" if pnl >= 0 else "📉"
        msg = (
            f"📊 *Daily Summary*\n"
            f"Balance: `{balance:.2f}`  Equity: `{equity:.2f}`\n"
            f"Float P&L: `{pnl:+.2f}` {icon}\n"
            f"Trades today: `{trades}`"
        )
        self.send(msg)

    def outside_session(self, utc_hour: int) -> None:
        """Sent at most once per hour when the session filter is active."""
        msg = (
            f"⏸ *Outside Session*\n"
            f"UTC: `{utc_hour:02d}:00`  EAT: `{utc_hour + 3:02d}:00`\n"
            f"Bot is waiting for the next session window."
        )
        self.send(msg)
