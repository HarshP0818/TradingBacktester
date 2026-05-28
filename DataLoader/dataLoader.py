import logging
import pandas as pd
import yfinance as yf
import os
import time
from logging_config import get_logger

logger = get_logger(__name__)

def load_data(ticker, start_date, end_date, retries=3):
    for i in range(retries):
        data = yf.download(ticker, start=start_date, end=end_date)
        if not data.empty:
            logger.info("Loaded %s rows for %s", len(data), ticker)
            return data
        logger.warning("Attempt %s failed to load data for %s", i + 1, ticker)
        time.sleep(1)

    logger.error("Failed to fetch data for %s after %s retries", ticker, retries)
    raise ValueError(f"Failed to fetch data for {ticker}")

