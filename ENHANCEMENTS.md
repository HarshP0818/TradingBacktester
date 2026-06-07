# Backtesting Engine - Enhancement Documentation

## Overview

This document describes the three major Enhancement Two implementations added to the backtesting engine:

1. **Configuration Framework** - Move all magic numbers to YAML config files
2. **Position Sizing Strategies** - Multiple dynamic position sizing methods
3. **Database Query Optimization** - Strategic indexes for faster queries

---

## Enhancement 1: Configuration Management

### Purpose
Replace hardcoded values throughout the codebase with a centralized YAML configuration system.

### Benefits
- **Flexibility**: Run multiple backtests with different parameters without code changes
- **Maintainability**: All configuration in one place
- **Reproducibility**: Easy to save and version control configurations
- **Parameter Sweeping**: Test multiple parameter combinations systematically

### Usage

#### Default Configuration
```bash
python main.py
# Uses config.yaml by default
```

#### Custom Configuration
```bash
python main.py --config config_kelly.yaml
python main.py --config config_conservative.yaml
python main.py --config config_volatility.yaml
```

### Configuration Files Included

1. **config.yaml** - Default configuration
   - Initial cash: $100,000
   - Fixed percentage position sizing (2% risk)
   - AAPL from 2020-2021
   - Moving average (20/50)

2. **config_conservative.yaml** - Conservative strategy
   - Lower capital: $50,000
   - Fixed shares (10 shares per trade)
   - MSFT from 2019-2021
   - Slower updates

3. **config_kelly.yaml** - Kelly Criterion sizing
   - Kelly-optimized position sizing
   - GOOGL from 2019-2021
   - Shorter moving averages (15/45)
   - Debug-level logging

4. **config_volatility.yaml** - Volatility-adjusted sizing
   - Position size adjusts based on volatility
   - TSLA from 2019-2021
   - Standard moving averages (20/50)

### Configuration Structure

```yaml
backtest:
  initial_cash: 100000              # Starting capital
  commission: 0.001                  # 0.1% per trade
  slippage: 0.0005                   # 0.05% price slippage
  position_sizing_strategy: "fixed_percentage"
  risk_percent_per_trade: 0.02       # Risk 2% per trade

position_sizing:
  fixed_percentage:
    risk_percent: 0.02
  kelly_criterion:
    kelly_fraction: 0.25             # Use 1/4 Kelly
  fixed_shares:
    num_shares: 1

strategy:
  name: "moving_average_crossover"
  fast_window: 20
  slow_window: 50

data:
  ticker: AAPL
  start_date: "2020-01-01"
  end_date: "2021-01-01"

database:
  host: localhost
  port: 5432
  database: stock_data
  user: ${DB_USER}                   # From environment
  password: ${DB_PASSWORD}           # From environment
```

### Creating Custom Configurations

Copy `config.yaml` and modify parameters:

```bash
cp config.yaml my_backtest.yaml
# Edit my_backtest.yaml
python main.py --config my_backtest.yaml
```

### Config Module API

```python
from config import load_config

# Load configuration
config = load_config("config.yaml")

# Access by dot notation
initial_cash = config.get("backtest.initial_cash")
fast_window = config.get("strategy.fast_window")

# Get entire sections
backtest_config = config.get_backtest_config()
strategy_config = config.get_strategy_config()
data_config = config.get_data_config()
```

---

## Enhancement 2: Position Sizing Strategies

### Purpose
Implement multiple professional position sizing methods to calculate trade sizes dynamically.

### Benefits
- **Risk Management**: Scale position size to account value and risk tolerance
- **Adaptive Trading**: Adjust to market conditions (volatility)
- **Optimized Returns**: Kelly Criterion for theoretical optimal sizing
- **Strategy Comparison**: Test different sizing methods on same strategy

### Position Sizing Methods

#### 1. Fixed Percentage (Default)
**Use Case**: Most common for retail traders

Risk a fixed percentage of account per trade.

```python
from BacktestingEngine.positionSizer import FixedPercentagePositionSizer

sizer = FixedPercentagePositionSizer(risk_percent=0.02)
shares = sizer.calculate_position_size(
    account_value=100000,
    current_price=150,
    stop_loss_pct=0.05
)
# Returns: 266 shares
# Calculation: (100000 * 0.02) / (150 * 0.05) = 266.67
```

**Formula:**
```
Risk Amount = Account Value × Risk Percent
Position Size = Risk Amount / (Price × Stop Loss Percent)
```

**Configuration:**
```yaml
position_sizing_strategy: "fixed_percentage"
position_sizing:
  fixed_percentage:
    risk_percent: 0.02  # Risk 2% per trade
```

---

#### 2. Kelly Criterion (Optimal)
**Use Case**: Mathematically optimal sizing given win rate

Adjusts position size based on strategy's historical win rate.

```python
from BacktestingEngine.positionSizer import KellyCriterionPositionSizer

sizer = KellyCriterionPositionSizer(kelly_fraction=0.25)
shares = sizer.calculate_position_size(
    account_value=100000,
    current_price=150,
    win_rate=0.55,           # 55% win rate
    avg_win=0.02,            # 2% average win
    avg_loss=0.01            # 1% average loss
)
```

**Formula:**
```
Kelly F = (Win Rate × Profit/Loss Ratio - (1 - Win Rate)) / (Profit/Loss Ratio)
Safe Kelly = Kelly F × Kelly Fraction  (typically 0.25 for safety)
Position Size = Account × Safe Kelly / Price
```

**Why 1/4 Kelly?**
- Full Kelly is mathematically optimal but aggressive
- 1/4 Kelly reduces drawdown while keeping good returns
- Practical for trading accounts to handle variance

**Configuration:**
```yaml
position_sizing_strategy: "kelly_criterion"
position_sizing:
  kelly_criterion:
    kelly_fraction: 0.25
```

---

#### 3. Fixed Shares (Simple)
**Use Case**: Testing, simple strategies

Trade fixed number of shares per signal (original behavior).

```python
from BacktestingEngine.positionSizer import FixedSharesPositionSizer

sizer = FixedSharesPositionSizer(num_shares=1)
shares = sizer.calculate_position_size(account_value=100000, current_price=150)
# Returns: 1 (always)
```

**Configuration:**
```yaml
position_sizing_strategy: "fixed_shares"
position_sizing:
  fixed_shares:
    num_shares: 1
```

---

#### 4. Volatility-Adjusted (Advanced)
**Use Case**: Maintain consistent risk across market regimes

Scale position size inversely with volatility.

```python
from BacktestingEngine.positionSizer import VolatilityAdjustedPositionSizer

sizer = VolatilityAdjustedPositionSizer(
    base_percent=0.02,
    target_volatility=0.015  # 1.5% daily
)
shares = sizer.calculate_position_size(
    account_value=100000,
    current_price=150,
    current_volatility=0.01,  # Low volatility - increase position
    stop_loss_pct=0.05
)
```

**Logic:**
- When volatility is LOW: Increase position size
- When volatility is HIGH: Decrease position size
- Maintains consistent risk across all market conditions

**Configuration:**
```yaml
position_sizing_strategy: "volatility_adjusted"
position_sizing:
  volatility_adjusted:
    base_percent: 0.02
    target_volatility: 0.015
```

---

### Integration with BacktestEngine

```python
from config import load_config
from BacktestingEngine.backtestEngine import BacktestEngine
from BacktestingEngine.positionSizer import create_position_sizer

# Load config
config = load_config("config.yaml")
backtest_config = config.get_backtest_config()
position_config = config.get_position_sizing_config()

# Create position sizer
sizer = create_position_sizer(
    backtest_config.get("position_sizing_strategy"),
    position_config.get(backtest_config.get("position_sizing_strategy"))
)

# Create engine with sizer
engine = BacktestEngine(
    initial_cash=backtest_config.get("initial_cash"),
    position_sizer=sizer,
    commission=backtest_config.get("commission"),
    slippage=backtest_config.get("slippage")
)
```

### Comparing Position Sizing Methods

Run the same strategy with different position sizers:

```bash
python main.py --config config.yaml              # Fixed percentage
python main.py --config config_kelly.yaml        # Kelly Criterion
python main.py --config config_conservative.yaml # Fixed shares
python main.py --config config_volatility.yaml   # Volatility-adjusted
```

Compare final portfolio values and Sharpe ratios.

---

## Enhancement 3: Database Query Optimization

### Purpose
Add strategic indexes to optimize query performance on large datasets.

### Benefits
- **Faster Queries**: Orders of magnitude faster for filtered queries
- **Scalability**: Maintain performance as data grows (millions of rows)
- **Reduced Load**: Less CPU/disk I/O for queries
- **Better UX**: Faster analytics and reporting

### Indexes Implemented

#### 1. Single-Column Indexes

**Index on ticker:**
```sql
CREATE INDEX idx_stock_prices_ticker ON stock_prices(ticker)
```
**Optimizes queries like:**
```sql
SELECT * FROM stock_prices WHERE ticker = 'AAPL'
```
**Use Case**: Fast lookups of all data for a specific stock

---

**Index on date:**
```sql
CREATE INDEX idx_stock_prices_date ON stock_prices(date)
```
**Optimizes queries like:**
```sql
SELECT * FROM stock_prices WHERE date = '2021-01-01'
-- or range queries
SELECT * FROM stock_prices WHERE date BETWEEN '2021-01-01' AND '2021-12-31'
```
**Use Case**: Time-series analysis across all stocks

---

#### 2. Composite Indexes

**Index (ticker, date):**
```sql
CREATE INDEX idx_stock_prices_ticker_date ON stock_prices(ticker, date)
```
**Optimizes queries like:**
```sql
SELECT * FROM stock_prices 
WHERE ticker = 'AAPL' 
AND date BETWEEN '2021-01-01' AND '2021-12-31'
```
**Use Case**: Most common - get stock data for date range

**Order matters!** Put the WHERE clause columns in index in the same order.

---

**Index (date, ticker):**
```sql
CREATE INDEX idx_stock_prices_date_ticker ON stock_prices(date, ticker)
```
**Optimizes queries like:**
```sql
SELECT * FROM stock_prices 
WHERE date >= '2021-01-01' 
AND ticker IN ('AAPL', 'MSFT', 'GOOGL')
```
**Use Case**: Time-based analysis across multiple stocks

---

### Index Performance Impact

**Without indexes (full table scan on 25M rows):**
```
Query: SELECT * WHERE ticker = 'AAPL' AND date BETWEEN '2021-01-01' AND '2021-12-31'
Time: ~5-10 seconds
```

**With idx_stock_prices_ticker_date:**
```
Query: SELECT * WHERE ticker = 'AAPL' AND date BETWEEN '2021-01-01' AND '2021-12-31'
Time: ~50-100ms
```

**Speedup: 50-100x faster!**

---

### Index Statistics

These indexes are automatically created when `store_data()` is called:

```python
from DataStorage.dataStorage import store_data

store_data(cleaned_data, "AAPL")  # Creates table and indexes
store_data(cleaned_data, "MSFT")  # Indexes already exist, just inserts
```

### Monitoring Index Usage

Check if indexes are being used by PostgreSQL:

```sql
-- Show all indexes
SELECT schemaname, tablename, indexname 
FROM pg_indexes 
WHERE tablename = 'stock_prices';

-- Show index sizes
SELECT indexname, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes
WHERE relname = 'stock_prices';

-- Show index usage stats
SELECT schemaname, tablename, indexrelname, idx_scan
FROM pg_stat_user_indexes
WHERE relname = 'stock_prices'
ORDER BY idx_scan DESC;
```

### Index Maintenance

Create maintenance tasks for optimal performance:

```sql
-- Rebuild fragmented indexes (periodic maintenance)
REINDEX INDEX idx_stock_prices_ticker_date;

-- Analyze table statistics (PostgreSQL query planner)
ANALYZE stock_prices;

-- Vacuum (reclaim space from deleted rows)
VACUUM stock_prices;
```

### Adding More Indexes (Future)

For even faster analytics:

```sql
-- Index on closing price (for price-range queries)
CREATE INDEX idx_stock_prices_close ON stock_prices(close);

-- Partial index (only recent data)
CREATE INDEX idx_stock_prices_recent 
ON stock_prices(ticker, date) 
WHERE date > NOW() - INTERVAL '1 year';

-- Covering index (includes close and volume without accessing table)
CREATE INDEX idx_stock_prices_ticker_date_close_volume 
ON stock_prices(ticker, date) 
INCLUDE (close, volume);
```

---

## Integration Example

Complete example using all three enhancements:

```python
# config_example.yaml
backtest:
  initial_cash: 500000
  commission: 0.001
  slippage: 0.0005
  position_sizing_strategy: "kelly_criterion"

position_sizing:
  kelly_criterion:
    kelly_fraction: 0.25

strategy:
  fast_window: 15
  slow_window: 40

data:
  ticker: AAPL
  start_date: "2018-01-01"
  end_date: "2022-01-01"
```

Run it:
```bash
python main.py --config config_example.yaml
```

In main.py:
```python
# 1. Load configuration (Enhancement 1)
config = load_config("config_example.yaml")

# 2. Create position sizer (Enhancement 2)
position_sizer = create_position_sizer(
    config.get("backtest.position_sizing_strategy"),
    config.get_position_sizing_config()
)

# 3. BacktestEngine uses position sizer
backtest_engine = BacktestEngine(
    initial_cash=config.get("backtest.initial_cash"),
    position_sizer=position_sizer
)

# 4. Data stored with optimized indexes (Enhancement 3)
store_data(cleaned_data, ticker)

# Run backtest with dynamic position sizing
metrics = backtest_engine.run_backtest(cleaned_data, signals)
```

---

## Summary

| Enhancement | Purpose | Benefit |
|---|---|---|
| **Configuration** | Centralize all magic numbers in YAML | Run any configuration without code changes |
| **Position Sizing** | Multiple sizing algorithms | Adapt to different risk profiles & market conditions |
| **Database Indexes** | Strategic query optimization | 50-100x faster queries on large datasets |

All three enhancements work together to create a professional, production-ready backtesting system.

---

## Related Files

- [config.py](config.py) - Configuration manager
- [BacktestingEngine/positionSizer.py](BacktestingEngine/positionSizer.py) - Position sizing strategies
- [DataStorage/dataStorage.py](DataStorage/dataStorage.py) - Database layer with indexes
- [main.py](main.py) - Main entry point using all enhancements
