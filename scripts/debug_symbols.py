import MetaTrader5 as mt5


def main():
    if not mt5.initialize():
        raise RuntimeError(f"MT5 Initialize Failed: {mt5.last_error()}")

    try:
        symbols = mt5.symbols_get()

        if symbols is None:
            raise RuntimeError(f"Failed to get symbols: {mt5.last_error()}")

        for symbol in symbols:
            if "XAU" in symbol.name:
                print(symbol.name)

    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
