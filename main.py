# this will be the main file that runs the backtesting process. It will call the data loader, data validator, and data storage modules to fetch, clean, and store the data. It will also run the backtesting logic and generate reports.
from DataLoader.dataLoader import load_data
from DataValidator.dataValidator import clean_data
from DataStorage.dataStorage import store_data
from BacktestingEngine.backtestEngine import BacktestEngine
from BacktestingEngine.strategy import Strategy
from logging_config import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    # define parameters
    ticker = "AAPL"
    start_date = "2020-01-01"
    end_date = "2021-01-01"

    logger.info("Starting backtesting workflow for %s from %s to %s", ticker, start_date, end_date)

    # load data
    raw_data = load_data(ticker, start_date, end_date)

    # clean data
    cleaned_data = clean_data(raw_data)

    # store data
    store_data(cleaned_data, ticker)

    # strategy object
    strategy = Strategy()
    signals = strategy.generate_signals(cleaned_data)
    logger.info("Generated %s non-zero signals", int((signals != 0).sum()))

    # run backtest
    backtest_engine = BacktestEngine()
    portfolio_value = backtest_engine.run_backtest(cleaned_data, signals)
    logger.info("Backtest complete. Final portfolio value: %s", portfolio_value[-1] if portfolio_value else None)