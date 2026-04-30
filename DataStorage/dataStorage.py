import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extras import execute_values

def store_data(data, ticker):

    load_dotenv()
    user = os.getenv('DB_USER')
    pw = os.getenv('DB_PASSWORD')

    if data.empty:
        return

    data = data.copy()
    data['ticker'] = ticker

    cols = ['date', 'open', 'high', 'low', 'close', 'volume', 'ticker']
    data = data[cols]

    data_tuples = [tuple(x) for x in data.to_numpy()]

    try:
        with psycopg2.connect(
            host="localhost",
            database="stock_data",
            user=user,
            password=pw
        ) as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS stock_prices (
                        date DATE,
                        open NUMERIC(18, 6),
                        high NUMERIC(18, 6),
                        low NUMERIC(18, 6),
                        close NUMERIC(18, 6),
                        volume NUMERIC(18, 6),
                        ticker VARCHAR(10),
                        PRIMARY KEY (date, ticker)
                    )
                """)

                execute_values(
                    cur,
                    """
                    INSERT INTO stock_prices 
                    (date, open, high, low, close, volume, ticker)
                    VALUES %s
                    ON CONFLICT (date, ticker) DO NOTHING
                    """,
                    data_tuples
                )

    except Exception as e:
        print(f"Error storing data: {e}")