import numpy as np
import pandas as pd
from logging_config import get_logger

logger = get_logger(__name__)


class PerformanceMetrics:
    """
    Calculate and store performance metrics for backtesting results.
    
    Metrics include:
    - Total Return: Overall percentage return
    - Sharpe Ratio: Return per unit of risk
    - Max Drawdown: Worst peak-to-trough decline
    - Win Rate: Percentage of profitable trades
    - Profit Factor: Gross profit / gross loss
    """
    
    def __init__(self, portfolio_values, trades=None):
        """
        Initialize performance metrics.
        
        Args:
            portfolio_values: List of portfolio values at each time step
            trades: List of trade dictionaries with 'entry', 'exit', 'profit' keys
        
        Raises:
            ValueError: If portfolio_values is empty or None
        """
        if not portfolio_values or len(portfolio_values) < 2:
            raise ValueError("Portfolio values must have at least 2 values")
        
        self.portfolio_values = np.array(portfolio_values)
        self.trades = trades or []
        
        # Calculate metrics
        self.total_return = self._calc_total_return()
        self.sharpe_ratio = self._calc_sharpe_ratio()
        self.max_drawdown = self._calc_max_drawdown()
        self.win_rate = self._calc_win_rate()
        self.profit_factor = self._calc_profit_factor()
        self.cumulative_returns = self._calc_cumulative_returns()
        
        logger.info(
            "Performance metrics calculated: "
            "return=%.2f%%, sharpe=%.2f, max_dd=%.2f%%, win_rate=%.2f%%",
            self.total_return * 100,
            self.sharpe_ratio,
            self.max_drawdown * 100,
            self.win_rate * 100 if self.win_rate else 0
        )
    
    def _calc_total_return(self) -> float:
        """Calculate total return as percentage."""
        initial = self.portfolio_values[0]
        final = self.portfolio_values[-1]
        
        if initial <= 0:
            raise ValueError("Initial portfolio value must be positive")
        
        return (final - initial) / initial
    
    def _calc_cumulative_returns(self) -> np.ndarray:
        """Calculate daily cumulative returns."""
        initial = self.portfolio_values[0]
        returns = (self.portfolio_values - initial) / initial
        return returns
    
    def _calc_sharpe_ratio(self, risk_free_rate=0.0, periods_per_year=252) -> float:
        """
        Calculate Sharpe Ratio.
        
        Sharpe Ratio = (Return - Risk Free Rate) / Volatility
        Measures risk-adjusted return.
        
        Args:
            risk_free_rate: Annual risk-free rate (default 0%)
            periods_per_year: Trading periods per year (default 252 for daily)
        
        Returns:
            Sharpe ratio
        """
        returns = np.diff(self.portfolio_values) / self.portfolio_values[:-1]
        excess_return = np.mean(returns) - risk_free_rate / periods_per_year
        volatility = np.std(returns)
        
        if volatility == 0:
            logger.warning("Volatility is zero, Sharpe ratio undefined")
            return 0.0
        
        sharpe = (excess_return * np.sqrt(periods_per_year)) / volatility
        return sharpe
    
    def _calc_max_drawdown(self) -> float:
        """
        Calculate maximum drawdown.
        
        Max Drawdown = worst peak-to-trough decline
        Important for understanding downside risk.
        
        Returns:
            Maximum drawdown as decimal (negative value)
        """
        cumulative_returns = self.cumulative_returns
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = cumulative_returns - running_max
        max_drawdown = np.min(drawdown)
        
        return max_drawdown
    
    def _calc_win_rate(self) -> float:
        """
        Calculate win rate (percentage of profitable trades).
        
        Returns:
            Win rate as decimal (0.0 to 1.0), or 0 if no trades
        """
        if not self.trades:
            logger.warning("No trades recorded, win rate is 0")
            return 0.0
        
        winning_trades = sum(1 for trade in self.trades if trade.get('profit', 0) > 0)
        win_rate = winning_trades / len(self.trades)
        
        return win_rate
    
    def _calc_profit_factor(self) -> float:
        """
        Calculate profit factor.
        
        Profit Factor = Gross Profit / Gross Loss
        Indicates profitability relative to losses.
        > 1.5 is generally considered good.
        
        Returns:
            Profit factor, or 0 if no trades
        """
        if not self.trades:
            logger.warning("No trades recorded, profit factor is 0")
            return 0.0
        
        gross_profit = sum(trade.get('profit', 0) for trade in self.trades 
                          if trade.get('profit', 0) > 0)
        gross_loss = abs(sum(trade.get('profit', 0) for trade in self.trades 
                            if trade.get('profit', 0) < 0))
        
        if gross_loss == 0:
            logger.warning("No losing trades, profit factor undefined")
            return 0.0
        
        profit_factor = gross_profit / gross_loss
        return profit_factor
    
    def summary(self) -> str:
        """
        Return a formatted summary of performance metrics.
        
        Returns:
            Formatted string summary
        """
        summary = f"""
        ========== PERFORMANCE SUMMARY ==========
        Total Return:     {self.total_return*100:>8.2f}%
        Sharpe Ratio:     {self.sharpe_ratio:>8.2f}
        Max Drawdown:     {self.max_drawdown*100:>8.2f}%
        Win Rate:         {self.win_rate*100:>8.2f}%
        Profit Factor:    {self.profit_factor:>8.2f}
        Total Trades:     {len(self.trades):>8d}
        ========================================
        """
        return summary
    
    def __str__(self) -> str:
        """Return summary when converted to string."""
        return self.summary()
