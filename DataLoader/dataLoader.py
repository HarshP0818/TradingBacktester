import pandas as pd
import yfinance as yf
import os
import time

def load_data(ticker, start_date, end_date, retries=3):
    for i in range(retries):
        data = yf.download(ticker, start=start_date, end=end_date)
        if not data.empty:
            return data
        time.sleep(1)

    raise ValueError(f"Failed to fetch data for {ticker}")

