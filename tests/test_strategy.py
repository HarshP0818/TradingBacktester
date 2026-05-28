import pandas as pd
from BacktestingEngine.strategy import Strategy


def test_generate_signals_returns_series():
    data = pd.DataFrame(
        {"close": [1.0, 2.0, 3.0, 4.0, 5.0]},
        index=pd.date_range("2020-01-01", periods=5),
    )
    strategy = Strategy(fast_window=2, slow_window=3)

    signals = strategy.generate_signals(data)

    assert list(signals.index) == list(data.index)
    assert signals.iloc[0] == 0
    assert signals.iloc[-1] == 1
