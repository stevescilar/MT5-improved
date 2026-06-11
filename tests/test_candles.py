import os

import MetaTrader5 as mt5
import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_MT5_INTEGRATION") != "1",
    reason="Set RUN_MT5_INTEGRATION=1 to run live MT5 integration tests.",
)


def test_get_candles_returns_dataframe(mt5_client):
    candles = mt5_client.get_candles("EURUSDm", mt5.TIMEFRAME_M5, 20)

    assert candles is not None
    assert len(candles) == 20
    assert {"time", "open", "high", "low", "close"}.issubset(candles.columns)
