import os

import MetaTrader5 as mt5
import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_MT5_INTEGRATION") != "1",
    reason="Set RUN_MT5_INTEGRATION=1 to run live MT5 integration tests.",
)


def test_xau_symbol_is_available():
    assert mt5.initialize()

    try:
        symbols = mt5.symbols_get()
        assert symbols is not None
        assert any("XAU" in symbol.name for symbol in symbols)
    finally:
        mt5.shutdown()
