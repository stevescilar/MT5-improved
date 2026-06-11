import os

import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_MT5_INTEGRATION") != "1",
    reason="Set RUN_MT5_INTEGRATION=1 to run live MT5 integration tests.",
)


def test_mt5_connection_returns_account_info(mt5_client):
    info = mt5_client.account_info()

    assert info is not None
    assert info.login
    assert info.server
