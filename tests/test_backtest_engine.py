import pandas as pd
from BacktestingEngine.backtestEngine import BacktestEngine


def test_run_backtest_buy_and_sell_sequence():
    data = pd.DataFrame(
        {
            "open": [10.0, 11.0, 12.0, 13.0, 14.0],
            "close": [10.0, 11.0, 13.0, 14.0, 15.0],
        },
        index=pd.date_range("2020-01-01", periods=5),
    )
    signals = pd.Series([0, 1, 0, -1, 0], index=data.index)

    engine = BacktestEngine(initial_cash=100.0)
    portfolio_values = engine.run_backtest(data, signals)

    assert isinstance(portfolio_values, list)
    assert portfolio_values[0] == 100.0
    assert portfolio_values[1] == 100.0
    assert portfolio_values[2] == 101.0
    assert portfolio_values[3] == 102.0
    assert portfolio_values[4] == 102.0
