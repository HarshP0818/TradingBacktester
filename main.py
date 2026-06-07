# this will be the main file that runs the backtesting process. It will call the data loader, data validator, and data storage modules to fetch, clean, and store the data. It will also run the backtesting logic and generate reports.
from DataLoader.dataLoader import load_data
from DataValidator.dataValidator import clean_data
from DataStorage.dataStorage import store_data
from BacktestingEngine.backtestEngine import BacktestEngine
from BacktestingEngine.strategy import Strategy
from BacktestingEngine.positionSizer import create_position_sizer
from config import load_config
from logging_config import get_logger
import argparse

logger = get_logger(__name__)


def run_backtest(config_path="config.yaml"):
    """
    Run complete backtesting workflow.
    
    Args:
        config_path: Path to configuration YAML file
    """
    # Load configuration
    config = load_config(config_path)
    logger.info(f"Loaded configuration from {config_path}")
    
    # Extract configuration parameters
    data_config = config.get_data_config()
    strategy_config = config.get_strategy_config()
    backtest_config = config.get_backtest_config()
    position_config = config.get_position_sizing_config()
    
    ticker = data_config.get("ticker", "AAPL")
    start_date = data_config.get("start_date", "2020-01-01")
    end_date = data_config.get("end_date", "2021-01-01")
    
    initial_cash = backtest_config.get("initial_cash", 100000)
    position_sizing_strategy = backtest_config.get("position_sizing_strategy", "fixed_percentage")
    
    logger.info(
        "Starting backtesting workflow for %s from %s to %s",
        ticker, start_date, end_date
    )
    logger.info(f"Using position sizing strategy: {position_sizing_strategy}")
    logger.info(f"Initial cash: ${initial_cash:,.2f}")

    try:
        # load data
        logger.info("Loading data...")
        raw_data = load_data(ticker, start_date, end_date)

        # clean data
        logger.info("Cleaning data...")
        cleaned_data = clean_data(raw_data)

        # store data
        logger.info("Storing data...")
        store_data(cleaned_data, ticker)

        # strategy object with configuration parameters
        logger.info(f"Initializing strategy: {strategy_config.get('name', 'moving_average_crossover')}")
        strategy = Strategy(
            fast_window=strategy_config.get("fast_window", 20),
            slow_window=strategy_config.get("slow_window", 50)
        )
        signals = strategy.generate_signals(cleaned_data)
        logger.info("Generated %s non-zero signals", int((signals != 0).sum()))

        # Create position sizer from config
        strategy_specific_config = position_config.get(position_sizing_strategy, {})
        position_sizer = create_position_sizer(position_sizing_strategy, strategy_specific_config)
        
        # run backtest and get performance metrics
        logger.info("Running backtest...")
        backtest_engine = BacktestEngine(
            initial_cash=initial_cash,
            position_sizer=position_sizer,
            commission=backtest_config.get("commission", 0.001),
            slippage=backtest_config.get("slippage", 0.0005)
        )
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
        return metrics
    
    except Exception as e:
        logger.error("Backtesting workflow failed: %s", str(e), exc_info=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run backtesting engine with configuration file"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration YAML file (default: config.yaml)"
    )
    
    args = parser.parse_args()
    run_backtest(args.config)