import os

import MetaTrader5 as mt5
from dotenv import load_dotenv

load_dotenv()

LOGIN = int(os.getenv("MT5_LOGIN", "0"))
PASSWORD = os.getenv("MT5_PASSWORD")
SERVER = os.getenv("MT5_SERVER", "ExnessKE-MT5Trial9")

# Broker-specific symbol names (Exness uses trailing 'm' for micro accounts)
SYMBOLS = os.getenv("MT5_SYMBOLS", "XAUUSDm,EURUSDm,GBPUSDm").split(",")

TIMEFRAME = os.getenv("MT5_TIMEFRAME", "M5")
CANDLE_COUNT = int(os.getenv("MT5_CANDLE_COUNT", "500"))

RISK_PCT = float(os.getenv("MT5_RISK_PCT", "0.01"))
MAX_DAILY_DRAWDOWN_PCT = float(
    os.getenv("MT5_MAX_DAILY_DRAWDOWN_PCT", "0.05")
)  # 5 % daily stop

MIN_RR = float(os.getenv("MT5_MIN_RR", "3.0"))

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

POLL_INTERVAL_SECONDS = int(os.getenv("MT5_POLL_INTERVAL", "60"))

# Trading session window in UTC hours (24h clock).
# Default: New York session  12:00–21:00 UTC = 15:00–00:00 EAT
# Set both to 0 to disable the filter and trade 24/5.
SESSION_START_UTC = int(os.getenv("SESSION_START_UTC", "12"))
SESSION_END_UTC = int(os.getenv("SESSION_END_UTC", "21"))

TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}
