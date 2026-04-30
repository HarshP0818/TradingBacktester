import pandas as pd

def clean_data(data):
    data = data.copy()

    # 1. Reset index
    data = data.reset_index()

    # 2. Standardize columns
    data.columns = [col.lower().replace(" ", "_") for col in data.columns]

    # 3. Ensure required columns
    required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    missing = [col for col in required_columns if col not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # 4. Select only needed columns
    data = data[required_columns]

    # 5. Enforce datetime
    data['date'] = pd.to_datetime(data['date'])

    # 6. Drop rows with missing price data
    data = data.dropna(subset=['open','high','low','close'])

    # 7. Remove duplicates
    data = data.drop_duplicates(subset='date')

    # 8. Sort
    data = data.sort_values('date').reset_index(drop=True)

    # 9. Type enforcement
    data[['open','high','low','close','volume']] = data[
        ['open','high','low','close','volume']
    ].astype('float64')

    # 10. Validation
    invalid = data[data["high"] < data["low"]]
    if not invalid.empty:
        raise ValueError(f"Invalid OHLC rows:\n{invalid.head()}")

    if (data[['open','high','low','close']] <= 0).any().any():
        raise ValueError("Prices must be > 0")

    return data