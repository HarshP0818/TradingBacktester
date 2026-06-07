from logging_config import get_logger
from BacktestingEngine.performanceMetrics import PerformanceMetrics
from BacktestingEngine.positionSizer import FixedSharesPositionSizer

logger = get_logger(__name__)


class BacktestEngine:
    """
    Backtesting engine that simulates trading based on signals.
    
    Maintains portfolio state (cash and position), executes trades based on signals,
    and calculates performance metrics. Prevents lookahead bias by using yesterday's
    signal to trade today.
    
    Supports:
    - Dynamic position sizing
    - Commission and slippage modeling
    - Multi-share positions (not just 0 or 1 share)
    """
    
    def __init__(self, initial_cash=100000, position_sizer=None, commission=0.001, slippage=0.0005):
        """
        Initialize the backtest engine.
        
        Args:
            initial_cash: Starting cash for portfolio (default 100000)
            position_sizer: PositionSizer instance for calculating trade sizes
                           (default: FixedSharesPositionSizer(1))
            commission: Commission per trade as a fraction (default 0.001 = 0.1%)
            slippage: Slippage per trade as a fraction (default 0.0005 = 0.05%)
        """
        self.initial_cash = initial_cash
        self.position_sizer = position_sizer or FixedSharesPositionSizer(1)
        self.commission = commission
        self.slippage = slippage
        self.trades = []
        self.entry_price = None
        self.position_size = 0
        
        logger.info(
            f"Initialized BacktestEngine: initial_cash={initial_cash}, "
            f"position_sizer={type(self.position_sizer).__name__}, "
            f"commission={commission*100}%, slippage={slippage*100}%"
        )

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
        position_size = 0
        self.entry_price = None
        self.trades = []
        
        for i in range(1, len(data)):
            signal = signals.iloc[i-1]
            current_price = data['open'].iloc[i]
            account_value = cash + position_size * current_price
            
            # BUY signal
            if signal == 1 and position_size == 0:
                # Calculate position size using position sizer
                shares_to_buy = self.position_sizer.calculate_position_size(
                    account_value=account_value,
                    current_price=current_price
                )
                
                if shares_to_buy > 0:
                    # Apply slippage to entry price
                    slipped_price = current_price * (1 + self.slippage)
                    trade_cost = shares_to_buy * slipped_price
                    
                    # Apply commission
                    commission_cost = trade_cost * self.commission
                    total_cost = trade_cost + commission_cost
                    
                    if cash >= total_cost:
                        position_size = shares_to_buy
                        cash -= total_cost
                        self.entry_price = slipped_price
                        
                        logger.debug(
                            f"BUY: {shares_to_buy} shares at ${current_price:.2f} "
                            f"(slipped: ${slipped_price:.2f}) on row {i} "
                            f"(cost: ${trade_cost:.2f}, commission: ${commission_cost:.2f})"
                        )
            
            # SELL signal
            elif signal == -1 and position_size > 0:
                # Apply slippage to exit price
                slipped_price = current_price * (1 - self.slippage)
                trade_revenue = position_size * slipped_price
                
                # Apply commission
                commission_cost = trade_revenue * self.commission
                net_revenue = trade_revenue - commission_cost
                
                profit = net_revenue - (position_size * self.entry_price)
                cash += net_revenue
                
                trade = {
                    'entry_date': data.index[i-1] if hasattr(data, 'index') else i-1,
                    'entry_price': self.entry_price,
                    'exit_date': data.index[i] if hasattr(data, 'index') else i,
                    'exit_price': slipped_price,
                    'profit': profit,
                    'shares': position_size,
                    'return_pct': (profit / (position_size * self.entry_price) * 100) if self.entry_price else 0
                }
                self.trades.append(trade)
                
                logger.debug(
                    f"SELL: {position_size} shares at ${current_price:.2f} "
                    f"(slipped: ${slipped_price:.2f}) on row {i} "
                    f"(revenue: ${trade_revenue:.2f}, commission: ${commission_cost:.2f}, profit: ${profit:.2f})"
                )
                
                position_size = 0
                self.entry_price = None
            
            # Update portfolio value at close
            portfolio_value.append(cash + position_size * data['close'].iloc[i])
        
        logger.info(
            "Backtest complete. Final portfolio value: %.2f, Trades executed: %s",
            portfolio_value[-1],
            len(self.trades)
        )
        
        # Return performance metrics object
        return PerformanceMetrics(portfolio_value, self.trades)
