import pandas as pd
from logging_config import get_logger

logger = get_logger(__name__)

def clean_data(data):
    data = data.copy()

    logger.debug("Raw columns: %s", data.columns)
    logger.debug("Raw columns type: %s", type(data.columns))

    # 1. Reset index
    data = data.reset_index()

    # If yfinance returns a datetime index, reset_index may create a column named Date or index.
    if 'index' in data.columns and 'date' not in data.columns:
        data = data.rename(columns={'index': 'date'})

    # Flatten tuple columns from MultiIndex or mixed-type columns.
    def flatten_column(col):
        if isinstance(col, tuple):
            for candidate in col:
                if isinstance(candidate, str) and candidate.lower().replace(" ", "_") in [
                    'open', 'high', 'low', 'close', 'volume', 'adj_close', 'date'
                ]:
                    return candidate
            return col[0]
        return col

    data.columns = [flatten_column(col) for col in data.columns]

    # 2. Standardize columns
    data.columns = [str(col).lower().replace(" ", "_") for col in data.columns]

    if 'adj_close' in data.columns and 'close' not in data.columns:
        data = data.rename(columns={'adj_close': 'close'})

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