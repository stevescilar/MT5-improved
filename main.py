"""
MT5 Improved — Main trading loop.

Runs continuously, analysing each configured symbol across five timeframes
and placing orders when a valid SMC setup is confirmed.

Usage:
    python main.py

Environment variables (see .env.example):
    MT5_LOGIN, MT5_PASSWORD, MT5_SERVER
    MT5_SYMBOLS, MT5_TIMEFRAME, MT5_CANDLE_COUNT
    MT5_RISK_PCT, MT5_MIN_RR, MT5_POLL_INTERVAL
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    SESSION_START_UTC, SESSION_END_UTC
"""

import sys
import time
from datetime import datetime, timezone

import MetaTrader5 as mt5
from loguru import logger

import config
from broker.mt5_client import MT5Client
from notifications.telegram_bot import TelegramNotifier
from risk.position_sizer import RiskManager
from strategy.multi_timeframe import analyze_multi_timeframe

# ------------------------------------------------------------------ #
#  Logging setup                                                       #
# ------------------------------------------------------------------ #

logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
)
logger.add(
    "logs/mt5_bot_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level="DEBUG",
    encoding="utf-8",
)


# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _today_utc():
    return _now_utc().date()


# ------------------------------------------------------------------ #
#  Session filter                                                      #
# ------------------------------------------------------------------ #


def in_trading_session() -> bool:
    """
    Return True only during the configured UTC trading window.

    Defaults to New York session: 12:00–21:00 UTC
    (= 15:00–00:00 EAT, capturing NY open + London/NY overlap)

    Override via .env:
        SESSION_START_UTC=12   # hour, 0-23
        SESSION_END_UTC=21     # hour, 0-23 (exclusive)

    Set both to 0 to disable the filter and trade 24/5.
    """
    start = config.SESSION_START_UTC
    end = config.SESSION_END_UTC

    # Both zero → filter disabled, always trade
    if start == 0 and end == 0:
        return True

    now_hour = _now_utc().hour

    # Handle windows that cross midnight e.g. 22:00–02:00
    if start < end:
        return start <= now_hour < end
    else:
        return now_hour >= start or now_hour < end


# ------------------------------------------------------------------ #
#  Timeframe drill-down map                                            #
# ------------------------------------------------------------------ #

TF_DRILL_DOWN = {
    "H4": (
        mt5.TIMEFRAME_H4,
        mt5.TIMEFRAME_H1,
        mt5.TIMEFRAME_M15,
        mt5.TIMEFRAME_M5,
        mt5.TIMEFRAME_M1,
    ),
    "H1": (
        mt5.TIMEFRAME_H1,
        mt5.TIMEFRAME_M30,
        mt5.TIMEFRAME_M15,
        mt5.TIMEFRAME_M5,
        mt5.TIMEFRAME_M1,
    ),
    "M15": (
        mt5.TIMEFRAME_M15,
        mt5.TIMEFRAME_M5,
        mt5.TIMEFRAME_M5,
        mt5.TIMEFRAME_M1,
        mt5.TIMEFRAME_M1,
    ),
    "M5": (
        mt5.TIMEFRAME_M5,
        mt5.TIMEFRAME_M5,
        mt5.TIMEFRAME_M1,
        mt5.TIMEFRAME_M1,
        mt5.TIMEFRAME_M1,
    ),
}


def get_timeframes() -> tuple:
    tf_key = config.TIMEFRAME
    if tf_key not in TF_DRILL_DOWN:
        logger.warning("Unknown TIMEFRAME '{}', defaulting to M5", tf_key)
        tf_key = "M5"
    return TF_DRILL_DOWN[tf_key]


# ------------------------------------------------------------------ #
#  Per-symbol analysis + execution                                     #
# ------------------------------------------------------------------ #


def process_symbol(
    symbol: str,
    client: MT5Client,
    risk: RiskManager,
    notifier: TelegramNotifier,
    timeframes: tuple,
) -> None:
    tf_h4, tf_h1, tf_m15, tf_m5, tf_m1 = timeframes
    count = config.CANDLE_COUNT

    candles = {
        "h4": client.get_candles(symbol, tf_h4, count),
        "h1": client.get_candles(symbol, tf_h1, count),
        "m15": client.get_candles(symbol, tf_m15, count),
        "m5": client.get_candles(symbol, tf_m5, count),
        "m1": client.get_candles(symbol, tf_m1, count),
    }

    if any(v is None for v in candles.values()):
        logger.warning("Skipping {} — missing candle data", symbol)
        return

    result = analyze_multi_timeframe(
        candles["h4"],
        candles["h1"],
        candles["m15"],
        candles["m5"],
        candles["m1"],
        min_rr=config.MIN_RR,
    )

    logger.debug(
        "{} | dir={} rr={} valid={} checks={}",
        symbol,
        result["direction"],
        result["risk_reward"],
        result["valid"],
        result["checks"],
    )

    if not result["valid"]:
        return

    direction = result["direction"]
    levels = result["levels"]
    rr = result["risk_reward"]

    if not risk.can_trade(symbol):
        logger.info("{} | Trade skipped — position already open", symbol)
        return

    lot = risk.lot_size(symbol, levels["entry"], levels["stop"])

    order = client.place_order(
        symbol=symbol,
        direction=direction,
        lot=lot,
        sl=levels["stop"],
        tp=levels["target"],
        comment=f"SMC {direction} RR={rr:.2f}",
    )

    notifier.trade_opened(
        symbol=symbol,
        direction=direction,
        lot=lot,
        entry=levels["entry"],
        sl=levels["stop"],
        tp=levels["target"],
        rr=rr,
    )

    logger.success(
        "Trade placed: {} {} lot={} entry={} sl={} tp={} rr={:.2f} ticket={}",
        symbol,
        direction,
        lot,
        levels["entry"],
        levels["stop"],
        levels["target"],
        rr,
        order.get("order"),
    )


# ------------------------------------------------------------------ #
#  Main loop                                                           #
# ------------------------------------------------------------------ #


def run() -> None:
    logger.info("Starting MT5 Improved bot")
    logger.info(
        "Session filter: {:02d}:00–{:02d}:00 UTC  ({} EAT – {} EAT)",
        config.SESSION_START_UTC,
        config.SESSION_END_UTC,
        config.SESSION_START_UTC + 3,
        config.SESSION_END_UTC + 3,
    )

    client = MT5Client()
    risk = RiskManager(risk_pct=config.RISK_PCT)
    notifier = TelegramNotifier(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID)
    timeframes = get_timeframes()

    client.connect()

    daily_trade_count = 0
    last_summary_date = _today_utc()
    last_session_log = None  # avoid spamming "outside session" every minute

    try:
        while True:
            # ── Daily summary rollover ──────────────────────────────
            today = _today_utc()
            if today != last_summary_date:
                info = client.account_info()
                if info:
                    notifier.daily_summary(info.balance, info.equity, daily_trade_count)
                daily_trade_count = 0
                last_summary_date = today

            # ── Session gate ────────────────────────────────────────
            if not in_trading_session():
                now_hour = _now_utc().hour
                if last_session_log != now_hour:
                    logger.info(
                        "Outside trading session ({:02d}:00 UTC / {:02d}:00 EAT) — waiting…",
                        now_hour,
                        now_hour + 3,
                    )
                    last_session_log = now_hour
                time.sleep(60)
                continue

            last_session_log = None  # reset so we log again when next gap occurs

            # ── Symbol scan ─────────────────────────────────────────
            for symbol in config.SYMBOLS:
                try:
                    process_symbol(symbol, client, risk, notifier, timeframes)
                except Exception as exc:
                    logger.error("Error processing {}: {}", symbol, exc)
                    notifier.error(f"process_symbol({symbol})", exc)

            time.sleep(config.POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as exc:
        logger.critical("Fatal error: {}", exc)
        notifier.error("main loop", exc)
        raise
    finally:
        client.shutdown()


if __name__ == "__main__":
    run()
