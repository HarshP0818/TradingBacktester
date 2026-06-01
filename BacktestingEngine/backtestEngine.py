from logging_config import get_logger
from BacktestingEngine.performanceMetrics import PerformanceMetrics

logger = get_logger(__name__)


class BacktestEngine:
    """
    Backtesting engine that simulates trading based on signals.
    
    Maintains portfolio state (cash and position), executes trades based on signals,
    and calculates performance metrics. Prevents lookahead bias by using yesterday's
    signal to trade today.
    """
    
    def __init__(self, initial_cash=100000):
        """
        Initialize the backtest engine.
        
        Args:
            initial_cash: Starting cash for portfolio (default 100000)
        """
        self.initial_cash = initial_cash
        self.trades = []
        self.entry_price = None

    def run_backtest(self, data, signals):
        """
        Run backtest simulation.
        
        Args:
            data: DataFrame with OHLCV data (columns: open, high, low, close, volume)
            signals: Series of trading signals (1=buy, -1=sell, 0=hold)
        
        Returns:
            PerformanceMetrics object with comprehensive performance analysis
        
        Raises:
            ValueError: If data or signals are invalid
        """
        if data is None or signals is None or len(data) == 0:
            raise ValueError("Data and signals cannot be empty")
        
        if len(data) != len(signals):
            raise ValueError("Data and signals must have same length")
        
        logger.info(
            "Starting backtest with %s rows and initial cash %s",
            len(data),
            self.initial_cash
        )
        
        portfolio_value = []
        cash = self.initial_cash
        portfolio_value.append(self.initial_cash)
        position = 0
        self.entry_price = None
        self.trades = []
        
        for i in range(1, len(data)):
            signal = signals.iloc[i-1]
            current_price = data['open'].iloc[i]
            
            # BUY signal
            if signal == 1 and cash > current_price and position == 0:
                position += 1
                cash -= current_price
                self.entry_price = current_price
                logger.debug(
                    "BUY: 1 share at %.2f on row %s (date: %s)",
                    current_price,
                    i,
                    data.index[i] if hasattr(data, 'index') else i
                )
            
            # SELL signal
            elif signal == -1 and position == 1:
                position -= 1
                profit = (current_price - self.entry_price) if self.entry_price else 0
                cash += current_price
                
                trade = {
                    'entry_date': data.index[i-1] if hasattr(data, 'index') else i-1,
                    'entry_price': self.entry_price,
                    'exit_date': data.index[i] if hasattr(data, 'index') else i,
                    'exit_price': current_price,
                    'profit': profit,
                    'return_pct': (profit / self.entry_price * 100) if self.entry_price else 0
                }
                self.trades.append(trade)
                
                logger.debug(
                    "SELL: 1 share at %.2f on row %s (profit: %.2f)",
                    current_price,
                    i,
                    profit
                )
                
                self.entry_price = None
            
            # Update portfolio value at close
            portfolio_value.append(cash + position * data['close'].iloc[i])
        
        logger.info(
            "Backtest complete. Final portfolio value: %.2f, Trades executed: %s",
            portfolio_value[-1],
            len(self.trades)
        )
        
        # Return performance metrics object
        return PerformanceMetrics(portfolio_value, self.trades)
