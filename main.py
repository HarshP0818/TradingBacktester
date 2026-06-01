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

    try:
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

        # run backtest and get performance metrics
        backtest_engine = BacktestEngine(initial_cash=100000)
        metrics = backtest_engine.run_backtest(cleaned_data, signals)
        
        # Display comprehensive performance metrics
        logger.info("Backtest complete. Performance metrics:")
        logger.info("Total Return: %.2f%%", metrics.total_return * 100)
        logger.info("Sharpe Ratio: %.2f", metrics.sharpe_ratio)
        logger.info("Max Drawdown: %.2f%%", metrics.max_drawdown * 100)
        logger.info("Win Rate: %.2f%%", metrics.win_rate * 100 if metrics.win_rate else 0)
        logger.info("Profit Factor: %.2f", metrics.profit_factor)
        logger.info("Total Trades: %s", len(metrics.trades))
        
        # Print summary to console
        print(metrics.summary())
    
    except Exception as e:
        logger.error("Backtesting workflow failed: %s", str(e), exc_info=True)
        raise