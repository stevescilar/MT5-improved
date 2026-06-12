import os

import pandas as pd
import pytest


def make_candles(rows):
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"])


@pytest.fixture
def candles_from():
    return make_candles


@pytest.fixture
def mt5_client():
    if os.getenv("RUN_MT5_INTEGRATION") != "1":
        pytest.skip("Set RUN_MT5_INTEGRATION=1 to run live MT5 integration tests")
    from broker.mt5_client import MT5Client

    client = MT5Client()
    client.connect()
    yield client
    client.shutdown()
