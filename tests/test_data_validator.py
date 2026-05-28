import pandas as pd
from DataValidator.dataValidator import clean_data


def test_clean_data_multiindex_columns():
    index = pd.to_datetime(["2020-01-02", "2020-01-03"])
    columns = pd.MultiIndex.from_tuples(
        [
            ("Close", "AAPL"),
            ("High", "AAPL"),
            ("Low", "AAPL"),
            ("Open", "AAPL"),
            ("Volume", "AAPL"),
        ],
        names=["Price", "Ticker"],
    )
    raw = pd.DataFrame(
        [
            [72.33, 72.39, 71.09, 71.34, 135480400],
            [71.63, 72.39, 71.41, 71.56, 146322800],
        ],
        index=index,
        columns=columns,
    )

    cleaned = clean_data(raw)

    assert list(cleaned.columns) == ["date", "open", "high", "low", "close", "volume"]
    assert cleaned.shape == (2, 6)
    assert cleaned.loc[0, "date"] == pd.Timestamp("2020-01-02")
    assert cleaned.loc[1, "volume"] == 146322800.0


def test_clean_data_raises_missing_columns():
    raw = pd.DataFrame(
        {
            "open": [1.0, 2.0],
            "high": [1.1, 2.1],
            "low": [0.9, 1.9],
        },
        index=pd.to_datetime(["2020-01-01", "2020-01-02"]),
    )

    try:
        clean_data(raw)
        assert False, "Expected ValueError for missing columns"
    except ValueError as exc:
        assert "Missing required columns" in str(exc)
