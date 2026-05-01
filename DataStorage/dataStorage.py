import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extras import execute_values

def store_data(data, ticker):

    # load environment variables
    load_dotenv()
    user = os.getenv('DB_USER')
    pw = os.getenv('DB_PASSWORD')

    # connect to stock_data database
    try: 
        with psycopg2.connect(
            host="localhost",
            database="stock_data",
            user=user,
            password=pw
        ) as conn:
            # ensure data is not empty
            if data.empty:
                print(f"No data to store for {ticker}")
                return
            # store all tickers in a single table with ticker as an additional column and batch insert
            data = data.copy()
            data['ticker'] = ticker
            cols = ['date', 'open', 'high', 'low', 'close', 'volume', 'ticker']
            data = data[cols]
            data_tuples = [tuple(x) for x in data.to_numpy()]
            # ensure no SQL injection can occur by using parameterized queries
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
            # use execute values to batch insert data for performance
                execute_values(cur, """
                    INSERT INTO stock_prices (date, open, high, low, close, volume, ticker)
                    VALUES %s
                    ON CONFLICT (date, ticker) DO NOTHING
                """, data_tuples)
    except Exception as e:
        print(f"Error storing data: {e}")