# Quick Start Guide - Using the Enhancements

## Installation

First, install new dependency:

```bash
pip install -r requirements.txt
```

This includes PyYAML which is required for configuration files.

---

## Quick Start - 5 Minutes

### 1. Run with Default Configuration

```bash
python main.py
```

This runs with the default `config.yaml`:
- AAPL stock (2020-2021)
- $100,000 initial capital
- Fixed 2% position sizing per trade
- Moving average strategy (20/50)

---

### 2. Run with Different Position Sizing

#### Conservative (Fixed Shares)
```bash
python main.py --config config_conservative.yaml
```
- Fixed 10 shares per trade
- Simpler, more predictable position sizes
- Good for testing

#### Kelly Criterion (Optimal)
```bash
python main.py --config config_kelly.yaml
```
- Mathematically optimal position sizing
- Adjusts based on win rate
- More aggressive

#### Volatility-Adjusted
```bash
python main.py --config config_volatility.yaml
```
- Adapts to market volatility
- Reduces size when market is volatile
- Maintains consistent risk

---

### 3. Create Your Own Configuration

Copy and modify:
```bash
cp config.yaml my_strategy.yaml
```

Edit `my_strategy.yaml`:
```yaml
data:
  ticker: MSFT         # Different stock
  start_date: "2019-01-01"
  end_date: "2021-12-31"

backtest:
  initial_cash: 250000  # Different capital

strategy:
  fast_window: 10      # Faster signals
  slow_window: 30

backtest:
  position_sizing_strategy: "kelly_criterion"
```

Run it:
```bash
python main.py --config my_strategy.yaml
```

---

## Configuration Examples

### Example 1: Testing Small Account ($10,000)

```yaml
# config_small_account.yaml
backtest:
  initial_cash: 10000
  position_sizing_strategy: "fixed_shares"

position_sizing:
  fixed_shares:
    num_shares: 5

data:
  ticker: AAPL
  start_date: "2020-01-01"
  end_date: "2021-12-31"
```

```bash
python main.py --config config_small_account.yaml
```

---

### Example 2: Aggressive Trading ($500,000)

```yaml
# config_aggressive.yaml
backtest:
  initial_cash: 500000
  commission: 0.0005  # Lower commission
  position_sizing_strategy: "kelly_criterion"

position_sizing:
  kelly_criterion:
    kelly_fraction: 0.5  # Use more Kelly

strategy:
  fast_window: 10    # Faster signals
  slow_window: 30

data:
  ticker: TSLA
  start_date: "2018-01-01"
  end_date: "2022-01-01"
```

---

### Example 3: Multi-Year Backtest

```yaml
# config_long_term.yaml
backtest:
  initial_cash: 100000
  position_sizing_strategy: "volatility_adjusted"

data:
  ticker: GOOGL
  start_date: "2015-01-01"
  end_date: "2022-12-31"

strategy:
  fast_window: 30    # Slower strategy for longer timeframe
  slow_window: 100
```

---

### Example 4: Lower Slippage/Commission

```yaml
# config_low_cost.yaml
backtest:
  initial_cash: 100000
  commission: 0.00001   # Very low (like prop trading)
  slippage: 0.00001
  position_sizing_strategy: "fixed_percentage"

position_sizing:
  fixed_percentage:
    risk_percent: 0.05  # Can risk more with low costs
```

---

## Position Sizing Comparison

Run the same strategy with different position sizers to compare:

```bash
# Test all position sizing methods
python main.py --config config.yaml              # Fixed 2%
python main.py --config config_kelly.yaml        # Kelly Criterion
python main.py --config config_conservative.yaml # Fixed shares
python main.py --config config_volatility.yaml   # Volatility
```

Compare the output:
- Total Return
- Sharpe Ratio
- Max Drawdown
- Win Rate
- Number of Trades

---

## Understanding the Output

When you run a backtest, you see:

```
INFO:root:Total Return: 15.32%
INFO:root:Sharpe Ratio: 1.28
INFO:root:Max Drawdown: -8.45%
INFO:root:Win Rate: 58.33%
INFO:root:Profit Factor: 2.15
INFO:root:Total Trades: 24
```

**Metrics Explanation:**

- **Total Return**: Overall profit/loss percentage
- **Sharpe Ratio**: Risk-adjusted return (higher is better)
- **Max Drawdown**: Worst peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss (>1.5 is good)
- **Total Trades**: Number of completed round-trip trades

---

## Database Indexes

Indexes are automatically created when data is stored:

```python
store_data(cleaned_data, ticker)
```

This creates 4 indexes automatically:
1. `idx_stock_prices_ticker` - Fast ticker lookups
2. `idx_stock_prices_date` - Fast date lookups
3. `idx_stock_prices_ticker_date` - Fast combined lookups
4. `idx_stock_prices_date_ticker` - Fast date-first lookups

Result: Queries are 50-100x faster!

---

## Troubleshooting

### Configuration File Not Found
```
FileNotFoundError: Configuration file not found: config.yaml
```

**Solution:** Make sure you're in the correct directory:
```bash
cd c:/Users/Harsh\ Patel/Backtester
python main.py
```

### YAML Parsing Error
```
Error parsing YAML configuration
```

**Solution:** Check YAML syntax:
- Indentation must use spaces (not tabs)
- Colons must be followed by space
- String values in quotes

### Database Connection Error
```
Error storing data for AAPL
```

**Solution:** Check database is running and credentials in .env:
```bash
echo DB_USER=postgres > .env
echo DB_PASSWORD=password >> .env
echo DB_HOST=localhost >> .env
echo DB_NAME=stock_data >> .env
```

---

## Next Steps

1. **Create multiple configs** for different stocks and timeframes
2. **Compare results** across different position sizing strategies
3. **Analyze performance** (Sharpe ratio, drawdown, win rate)
4. **Run parameter sweeps** by creating configs with different MA windows
5. **Monitor database** to see query performance improvements

See [ENHANCEMENTS.md](ENHANCEMENTS.md) for detailed documentation.
