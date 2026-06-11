import os

from dotenv import load_dotenv

load_dotenv()


LOGIN = int(os.getenv("MT5_LOGIN", "436317515"))

PASSWORD = os.getenv("MT5_PASSWORD")

SERVER = "ExnessKE-MT5Trial9"

SYMBOLS = [
    "XAUUSDm",
    "EURUSDm",
    "GBPUSD",
]

TIMEFRAME = "M5"

CANDLE_COUNT = 500
