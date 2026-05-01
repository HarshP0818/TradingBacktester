import pandas as pd

def clean_data(data):
    data = data.copy()

    print(data.columns)
    print(type(data.columns))

    # 1. Reset index
    data = data.reset_index()

    # we need to normalize the columns
    # if index is datetime, we need to reset the index and make it a column
    # if the columns are a multi-index, we need to flatten them and standardize the column names, we will take the last level of the multi-index as the column name, this is because some data sources have a multi-index with ticker and date, and we want to keep the date as a column and not have it as an index, we also want to standardize the column names to be lowercase and replace spaces with underscores for consistency across different data sources


    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)  # get the last level of the multi-index if it exists

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