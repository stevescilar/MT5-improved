import pandas as pd
import pytest


def make_candles(rows):
    return pd.DataFrame(
        rows,
        columns=["open", "high", "low", "close"],
    )


@pytest.fixture
def candles_from():
    return make_candles


@pytest.fixture
def mt5_client():
    from broker.mt5_client import MT5Client

    client = MT5Client()

    client.connect()

    yield client

    client.shutdown()
