"""
Position Sizing Strategies for the backtesting engine.

Different position sizing methods to calculate how many shares to buy/sell
based on account value, risk tolerance, and win rate.
"""
from logging_config import get_logger
from abc import ABC, abstractmethod

logger = get_logger(__name__)


class PositionSizer(ABC):
    """Abstract base class for position sizing strategies."""
    
    @abstractmethod
    def calculate_position_size(self, account_value, current_price, **kwargs):
        """
        Calculate position size.
        
        Args:
            account_value: Current account equity/cash
            current_price: Current price of the asset
            **kwargs: Additional strategy-specific parameters
            
        Returns:
            Number of shares to buy/sell
        """
        pass


class FixedPercentagePositionSizer(PositionSizer):
    """
    Risk a fixed percentage of account per trade.
    
    This is the most common position sizing method for retail traders.
    It scales position size with account growth and limits drawdown.
    """
    
    def __init__(self, risk_percent=0.02):
        """
        Initialize fixed percentage sizer.
        
        Args:
            risk_percent: Percentage of account to risk per trade (e.g., 0.02 = 2%)
        """
        self.risk_percent = risk_percent
        logger.info(f"Initialized FixedPercentagePositionSizer with {risk_percent*100}% risk")
    
    def calculate_position_size(self, account_value, current_price, stop_loss_pct=0.05):
        """
        Calculate position size based on fixed percentage of account.
        
        Args:
            account_value: Current account value
            current_price: Current asset price
            stop_loss_pct: Stop loss percentage (e.g., 0.05 = 5% stop)
            
        Returns:
            Number of shares to trade
            
        Example:
            account = $100,000
            risk_percent = 0.02 (2%)
            current_price = $150
            stop_loss_pct = 0.05 (5%)
            
            risk_amount = $100,000 * 0.02 = $2,000
            position_size = $2,000 / ($150 * 0.05) = 266.67 shares
        """
        if current_price <= 0:
            logger.warning(f"Invalid price {current_price}, returning 0 shares")
            return 0
        
        risk_amount = account_value * self.risk_percent
        stop_loss_amount = current_price * stop_loss_pct
        
        if stop_loss_amount <= 0:
            logger.warning(f"Invalid stop loss amount, returning 0 shares")
            return 0
        
        position_size = int(risk_amount / stop_loss_amount)
        logger.debug(
            f"Fixed %% sizer: account={account_value}, price={current_price}, "
            f"risk_amount={risk_amount}, position_size={position_size}"
        )
        return position_size


class KellyCriterionPositionSizer(PositionSizer):
    """
    Use Kelly Criterion for optimal position sizing.
    
    Kelly Criterion: f* = (bp - q) / b
    where:
      f* = fraction of bankroll to bet
      b = odds received on bet
      p = probability of winning
      q = probability of losing (1 - p)
    
    For trading: f* = (win_rate * profit_loss_ratio - (1 - win_rate)) / profit_loss_ratio
    
    Note: Kelly's formula is aggressive. In practice, use fractional Kelly (e.g., 0.25*Kelly)
    to reduce drawdown.
    """
    
    def __init__(self, kelly_fraction=0.25):
        """
        Initialize Kelly Criterion sizer.
        
        Args:
            kelly_fraction: Fraction of Kelly to use (e.g., 0.25 = 1/4 Kelly for safety)
        """
        if not (0 < kelly_fraction <= 1):
            raise ValueError("kelly_fraction must be between 0 and 1")
        self.kelly_fraction = kelly_fraction
        logger.info(f"Initialized KellyCriterionPositionSizer with {kelly_fraction} Kelly fraction")
    
    def calculate_position_size(
        self,
        account_value,
        current_price,
        win_rate=0.55,
        avg_win=0.02,
        avg_loss=0.01
    ):
        """
        Calculate position size using Kelly Criterion.
        
        Args:
            account_value: Current account value
            current_price: Current asset price
            win_rate: Win rate of strategy (0 to 1, e.g., 0.55 = 55%)
            avg_win: Average winning trade return (e.g., 0.02 = 2%)
            avg_loss: Average losing trade return (e.g., 0.01 = 1%)
            
        Returns:
            Number of shares to trade
            
        Example:
            win_rate = 0.55 (55%)
            avg_win = 0.02 (2% gain)
            avg_loss = 0.01 (1% loss)
            kelly_fraction = 0.25
            
            kelly_f = ((0.55 * 0.02) / 0.01 - (1 - 0.55)) / (0.02 / 0.01)
                    = (1.1 - 0.45) / 2
                    = 0.325
            position_f = 0.325 * 0.25 = 0.08125 (8.125% of account)
        """
        if current_price <= 0 or avg_loss <= 0:
            logger.warning(f"Invalid parameters, returning 0 shares")
            return 0
        
        if not (0 <= win_rate <= 1):
            logger.warning(f"Invalid win_rate {win_rate}, clamping to [0, 1]")
            win_rate = max(0, min(1, win_rate))
        
        # Kelly's formula: f = (p*b - q) / b
        # where p = win rate, q = 1 - p, b = win/loss ratio
        profit_loss_ratio = avg_win / avg_loss
        kelly_f = (win_rate * profit_loss_ratio - (1 - win_rate)) / profit_loss_ratio
        
        # Apply kelly fraction for safety
        safe_kelly_f = kelly_f * self.kelly_fraction
        safe_kelly_f = max(0, min(safe_kelly_f, 0.25))  # Cap at 25% for safety
        
        position_dollars = account_value * safe_kelly_f
        position_size = int(position_dollars / current_price)
        
        logger.debug(
            f"Kelly sizer: kelly_f={kelly_f:.4f}, safe_f={safe_kelly_f:.4f}, "
            f"position_size={position_size}, win_rate={win_rate}, "
            f"avg_win={avg_win}, avg_loss={avg_loss}"
        )
        return position_size


class FixedSharesPositionSizer(PositionSizer):
    """
    Trade a fixed number of shares per trade.
    
    Simple but doesn't adapt to account growth or market conditions.
    Useful for testing and simple strategies.
    """
    
    def __init__(self, num_shares=1):
        """
        Initialize fixed shares sizer.
        
        Args:
            num_shares: Number of shares to trade per signal
        """
        if num_shares < 1 or not isinstance(num_shares, int):
            raise ValueError("num_shares must be a positive integer")
        self.num_shares = num_shares
        logger.info(f"Initialized FixedSharesPositionSizer with {num_shares} shares")
    
    def calculate_position_size(self, account_value, current_price, **kwargs):
        """
        Return fixed number of shares.
        
        Args:
            account_value: Current account value (unused)
            current_price: Current asset price (unused)
            **kwargs: Additional parameters (unused)
            
        Returns:
            Fixed number of shares
        """
        logger.debug(f"Fixed shares sizer: returning {self.num_shares} shares")
        return self.num_shares


class VolatilityAdjustedPositionSizer(PositionSizer):
    """
    Adjust position size based on volatility.
    
    Reduce position size when volatility is high, increase when it's low.
    This helps maintain consistent risk across different market regimes.
    """
    
    def __init__(self, base_percent=0.02, target_volatility=0.015):
        """
        Initialize volatility-adjusted sizer.
        
        Args:
            base_percent: Base risk percentage (when volatility = target)
            target_volatility: Target volatility level (e.g., 0.015 = 1.5% daily)
        """
        self.base_percent = base_percent
        self.target_volatility = target_volatility
        logger.info(f"Initialized VolatilityAdjustedPositionSizer with base {base_percent*100}%")
    
    def calculate_position_size(
        self,
        account_value,
        current_price,
        current_volatility=0.015,
        stop_loss_pct=0.05,
        **kwargs
    ):
        """
        Calculate position size adjusted for volatility.
        
        Args:
            account_value: Current account value
            current_price: Current asset price
            current_volatility: Current volatility level (e.g., 0.015 = 1.5%)
            stop_loss_pct: Stop loss percentage
            **kwargs: Additional parameters
            
        Returns:
            Volatility-adjusted position size
            
        Example:
            When volatility is high, reduce position size to maintain risk
            When volatility is low, increase position size
        """
        if current_price <= 0 or current_volatility <= 0:
            logger.warning(f"Invalid parameters, returning 0 shares")
            return 0
        
        # Adjust risk based on volatility ratio
        vol_ratio = self.target_volatility / current_volatility
        adjusted_percent = self.base_percent * vol_ratio
        adjusted_percent = max(0.005, min(0.05, adjusted_percent))  # Cap between 0.5% and 5%
        
        risk_amount = account_value * adjusted_percent
        stop_loss_amount = current_price * stop_loss_pct
        position_size = int(risk_amount / stop_loss_amount)
        
        logger.debug(
            f"Vol-adjusted sizer: vol_ratio={vol_ratio:.2f}, "
            f"adjusted_percent={adjusted_percent*100:.2f}%, position_size={position_size}"
        )
        return position_size


def create_position_sizer(strategy_name="fixed_percentage", config=None):
    """
    Factory function to create appropriate position sizer.
    
    Args:
        strategy_name: Name of position sizing strategy
        config: Configuration dict with strategy parameters
        
    Returns:
        PositionSizer instance
    """
    config = config or {}
    
    if strategy_name == "fixed_percentage":
        risk_percent = config.get("risk_percent", 0.02)
        return FixedPercentagePositionSizer(risk_percent)
    
    elif strategy_name == "kelly_criterion":
        kelly_fraction = config.get("kelly_fraction", 0.25)
        return KellyCriterionPositionSizer(kelly_fraction)
    
    elif strategy_name == "fixed_shares":
        num_shares = config.get("num_shares", 1)
        return FixedSharesPositionSizer(num_shares)
    
    elif strategy_name == "volatility_adjusted":
        base_percent = config.get("base_percent", 0.02)
        target_vol = config.get("target_volatility", 0.015)
        return VolatilityAdjustedPositionSizer(base_percent, target_vol)
    
    else:
        logger.warning(f"Unknown position sizer: {strategy_name}, using fixed_percentage")
        return FixedPercentagePositionSizer()
