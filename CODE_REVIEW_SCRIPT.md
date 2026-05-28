# CS 499 CODE REVIEW SCRIPT - Stock Market Backtesting Engine

## INTRODUCTION (2-3 minutes)

**Opening:**
"Hi, I'm reviewing a stock market backtesting engine that I built for analyzing trading strategies. The system downloads historical stock data from Yahoo Finance, validates and cleans the data, generates trading signals using a technical analysis strategy, simulates trades in a portfolio, and stores the results in a PostgreSQL database—all containerized with Docker.

The architecture has five main components working together: the data loader fetches prices, the validator cleans and normalizes the data, the strategy generates buy/sell signals, the backtesting engine executes simulated trades, and the data storage layer persists everything to the database.

Today I'll walk through the code and discuss three areas: software design and engineering, algorithms and data structures, and databases. For each area, I'll show what's working well, identify specific weaknesses, and explain how I plan to enhance it."

---

## CATEGORY 1: SOFTWARE DESIGN & ENGINEERING (15-20 minutes)

### Part 1A: Existing Code Overview (5 min)

**Talking Points:**

"Let me start by showing you the overall architecture. [Show main.py on screen]

Here's the main entry point. You can see the workflow: we load data for AAPL from 2020 to 2021, clean it, store it, generate signals, and run the backtest. The code is organized into separate modules—each with a single responsibility.

[Show folder structure: DataLoader/, DataValidator/, BacktestingEngine/, DataStorage/]

This modular design means I can update one module without affecting others. For example, I could swap out the data source from Yahoo Finance to another provider without touching the backtesting logic.

Now let me highlight the strengths of the current design:

**Strength 1: Separation of Concerns**
[Show imports in main.py]
Each module has one job. DataLoader only fetches. DataValidator only cleans. Strategy only generates signals. This makes the code easier to test, debug, and maintain.

**Strength 2: Error Handling**
[Show try-catch in dataStorage.py]
We have error handling in place—specifically in the database layer where we wrap the connection in a try-except. We also handle the case where data is empty before attempting to insert.

**Strength 3: Security: SQL Injection Prevention**
[Show dataStorage.py around line 35-40]
Notice here we're using execute_values() with parameterized queries. We're NOT concatenating strings into SQL—that would be a major vulnerability. Instead, we pass data separately from the query, which prevents SQL injection attacks.

**Strength 4: Configuration Management**
[Show .env.example]
We're using environment variables for database credentials. The database password isn't hardcoded. We load it from a .env file using python-dotenv. This is a professional practice.

**Strength 5: Containerization**
[Show Dockerfile and docker-compose.yml]
The entire application is containerized. We have a Dockerfile for the app and a docker-compose file that orchestrates the app and database. This means the project runs consistently whether it's on my machine, a colleague's machine, or a production server.

**Strength 6: Logging and Test Support**
[Show logging_config.py and tests/ folder]
I implemented structured logging using Python's logging module, and I added an initial pytest test suite to cover key modules. This improves observability and gives the project a foundation for automated quality checks.

So that's a solid foundation. Now let me dig into the weaknesses."

---

### Part 1B: Weaknesses & Analysis (10 min)

**Talking Points:**

"**Finding 1: Generic Error Handling**

[Show dataStorage.py, line 47-48]
Look at this catch block. If something goes wrong, we just print a generic message: 'Error storing data: {e}'. That's it.

Why is this a problem? In a production system, this makes debugging very difficult. I don't know if the error was:
- A network timeout (transient, should retry)
- Invalid credentials (critical, needs manual intervention)
- Data integrity issue (database schema mismatch)
- A one-off connection blip (might resolve itself)

Currently, all these cases look the same. And we have no logging to track when errors occur. This would be nightmare in production.

---

**Finding 2: Hardcoded Configuration Values**

[Show backtestEngine.py, line 11]
Here's an example: initial_cash=100000 is hardcoded. What if I want to backtest with $50,000 instead?

[Show strategy.py, line 9]
Same issue here: fast_window=20 and slow_window=50 are hardcoded. What if I want to test with a 10/30 crossover instead?

Currently, I have to modify the source code and rerun. In a real system, I'd want to:
- Pass these as command-line arguments
- Load them from a config file
- Maybe even store them in a database with my backtest results

Right now, this makes it hard to run multiple backtests with different parameters.

---

**Finding 3: Missing Input Validation**

[Show dataValidator.py]
The validator does a lot of good work: checking for required columns, handling datetime conversion, checking for negative prices. That's great.

But look at the main.py [show line 13-15]:
```
start_date = '2020-01-01'
end_date = '2021-01-01'
```

There's no validation here. What if I accidentally pass:
- An invalid date format?
- A start date after the end date?
- A date 100 years in the future?
- An empty ticker string?

The code would fail downstream, possibly with a cryptic error message. Better to validate at the entry point and fail fast with a clear message.

---

**Finding 4: Lack of Type Hints and Docstrings**

[Show main.py, line 1-7]
Notice these functions have no type hints. I don't know what arguments they expect or what they return without reading the entire function body.

Compare this to best practice:
```python
def load_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    '''Fetch historical stock data from Yahoo Finance.
    
    Args:
        ticker: Stock symbol (e.g., 'AAPL')
        start_date: Start date as 'YYYY-MM-DD'
        end_date: End date as 'YYYY-MM-DD'
    
    Returns:
        DataFrame with OHLCV data
    
    Raises:
        ValueError: If data cannot be fetched after retries
    '''
```

With type hints, an IDE can warn me of misuse. And the docstring tells me the contract: what goes in, what comes out, what can go wrong.

Currently, someone using this code has to guess or read the implementation.

---

**Finding 5: Limited Automated Tests**

[Show project structure]
There is now a `tests/` folder with initial pytest coverage for the validator, strategy, and backtest engine. However, test coverage remains limited and does not yet include the storage layer, loader retries, or failure modes.

This is still an area for improvement because:
- the repository needs broader coverage for regression safety
- edge cases like missing ticker symbols or malformed API responses are not fully tested
- integration tests across the full workflow are still missing

In a professional environment, strong automated coverage is expected for reliability."

---

### Part 1C: Planned Enhancements (5 min)

**Talking Points:**

"**Enhancement 1: Structured Logging**

I'm going to replace all the print() statements with Python's logging module. Instead of:
```python
print(f'Error storing data: {e}')
```

I'll have:
```python
logger.error(f'Failed to insert data for {ticker}', exc_info=True)
logger.warning(f'Data was empty for {ticker}, skipping')
logger.info(f'Successfully stored {len(data)} rows')
```

This gives us:
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Timestamps automatically
- Stack traces when we want them
- Output to both console and file for audit trails

This demonstrates professional software engineering practices and aligns with Course Outcome 2: building secure, professional-quality applications.

---

**Enhancement 2: Configuration Framework**

I'm going to move all the magic numbers to a config file:

**config.yaml:**
```yaml
backtest:
  initial_cash: 100000
  commission: 0

strategy:
  fast_window: 20
  slow_window: 50

data:
  ticker: AAPL
  start_date: 2020-01-01
  end_date: 2021-01-01
```

Then in main.py:
```python
config = load_config('config.yaml')
strategy = Strategy(
    fast_window=config['strategy']['fast_window'],
    slow_window=config['strategy']['slow_window']
)
```

This means I can run multiple backtests with different parameters without changing code:
```bash
python main.py --config backtest_20_50.yaml
python main.py --config backtest_10_30.yaml
```

This demonstrates flexibility and maintainability—key software engineering principles.

---

**Enhancement 3: Input Validation & Type Hints**

I'll add comprehensive type hints to all functions and validate inputs at entry points:

```python
def load_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    if not ticker or not isinstance(ticker, str):
        raise ValueError(f'Invalid ticker: {ticker}')
    
    try:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
    except:
        raise ValueError(f'Invalid date format. Use YYYY-MM-DD')
    
    if start >= end:
        raise ValueError(f'Start date must be before end date')
    
    # ... rest of function
```

This demonstrates defensive programming—catching errors early with clear messages.

---

**Enhancement 4: Comprehensive Documentation**

I'll add:
- Module docstrings explaining the purpose of each module
- Function docstrings with Args, Returns, Raises
- A detailed README with architecture diagrams
- An ARCHITECTURE.md explaining design decisions
- Code comments for non-obvious logic

This demonstrates professional communication and helps other developers (or future-me) understand the system.

These enhancements support Course Outcome 5: practicing professional communication and collaboration."

---

## CATEGORY 2: ALGORITHMS & DATA STRUCTURES (15-20 minutes)

### Part 2A: Existing Code Overview (5 min)

**Talking Points:**

"Now let's look at the algorithms and data structures powering the strategy and backtest engine.

[Show strategy.py]

**The Strategy:**
I'm using a Simple Moving Average (SMA) crossover strategy. Here's how it works:

1. Calculate a fast-moving average (20 days)
2. Calculate a slow-moving average (50 days)
3. When fast > slow, that's a BUY signal (1)
4. When fast < slow, that's a SELL signal (-1)
5. Otherwise, HOLD (0)

[Show the code]:
```python
fast = data['close'].rolling(window=self.fast_window).mean()
slow = data['close'].rolling(window=self.slow_window).mean()
signal[fast > slow] = 1
signal[fast < slow] = -1
```

This is efficient—pandas' rolling() function uses a sliding window algorithm. It's O(n) time complexity, which is optimal for this problem.

[Show backtestEngine.py]

**The Portfolio Engine:**
The backtest engine simulates trading by:
1. Maintaining state: cash and position (number of shares)
2. For each day, checking the previous day's signal
3. If it's a BUY signal and we have cash and no position, buy 1 share at today's open price
4. If it's a SELL signal and we have a position, sell it
5. Calculate end-of-day portfolio value: cash + (shares * close price)

**Strength 1: Prevents Lookahead Bias**

[Show backtestEngine.py, line 26]
Notice we use signals[i-1] (yesterday's signal) to trade today. This is crucial—it prevents 'lookahead bias' where we'd be using future information to make past decisions, which would give unrealistic results.

In real trading, you can only use information available up to today. This code respects that constraint.

**Strength 2: Efficient MA Calculation**

Using pandas' rolling() is smart. It's optimized in C and much faster than a manual loop. For 252 trading days, this is nearly instant.

**Strength 3: Clear State Management**

The engine maintains position (shares owned) and cash separately, then combines them to get portfolio value. This is easy to understand and debug."

---

### Part 2B: Weaknesses & Analysis (10 min)

**Talking Points:**

"**Finding 1: Static Strategy with No Adaptability**

[Show strategy.py, line 9]
The MA windows (20/50) are hardcoded. This strategy might work great in one market, but terrible in another.

In a trending market, short windows might work.
In a choppy market, longer windows might be better.
In a crisis, you might need no strategy at all.

Currently, I can't adapt. I'm stuck with 20/50. This is a major limitation.

---

**Finding 2: Fixed Position Sizing**

[Show backtestEngine.py, line 27]
Position sizing is simply: position += 1

This means:
- With $100,000 cash and AAPL at $150, I can buy only ~666 shares max
- If I start with a $50,000 account, I can still only buy 1 share
- This wastes capital in the small account, and is conservative in the large account

Real trading uses position sizing based on risk:
- Kelly criterion: bet a percentage of your bankroll
- Volatility-based: bigger positions in calm markets, smaller in volatile ones
- Account percentage: always risk 2% of account per trade

Currently, I'm not doing any of this.

---

**Finding 3: Missing Performance Metrics**

[Show backtestEngine.py, line 43]
We return portfolio_value—a list of numbers. That's it.

I have no metrics to assess the strategy:
- **Sharpe Ratio**: How much return per unit of risk?
- **Max Drawdown**: What's the worst peak-to-trough decline?
- **Win Rate**: What % of trades were profitable?
- **Profit Factor**: Gross profit / gross loss
- **Sortino Ratio**: Like Sharpe, but only penalizes downside volatility

Without these, I'm flying blind. I only know the final P&L, not whether the strategy is actually good or just got lucky.

---

**Finding 4: Overlapping Signal Handling**

[Show strategy.py, line 30-31]
```python
signal[fast > slow] = 1
signal[fast < slow] = -1
```

If fast == slow exactly, we get a hold signal (0) from initialization, which is fine.

But here's a subtle issue: if fast and slow cross multiple times in a single day (unlikely but possible in intraday data), we only see the final cross. More importantly, with the logic as-is, if we have fast > slow on day N, we buy. On day N+1, if it's fast < slow, we sell. But what if it happens the same day? This code structure handles it, but it's not explicit about the priority.

---

**Finding 5: No Commission or Slippage**

[Show backtestEngine.py]
We trade at exactly the open price, every time, with no cost. Real trading has:
- Commission: $5 to $10 per trade (depending on broker)
- Slippage: We might not get exactly the open price; market impact means large orders move prices
- Spreads: Bid-ask spread costs us money

Ignoring these inflates backtest results. A strategy that loses after commissions might look profitable here.

---

**Finding 6: Single Ticker, No Diversification**

The entire system backtests a single ticker. Real strategies diversify across multiple assets. This is a simplification, but a significant limitation."

---

### Part 2C: Planned Enhancements (5 min)

**Talking Points:**

"**Enhancement 1: Comprehensive Performance Metrics**

I'm going to calculate and return a PerformanceMetrics object:

```python
class PerformanceMetrics:
    def __init__(self, portfolio_values, trades):
        self.total_return = (portfolio_values[-1] - portfolio_values[0]) / portfolio_values[0]
        self.sharpe_ratio = self._calc_sharpe(portfolio_values)
        self.max_drawdown = self._calc_max_drawdown(portfolio_values)
        self.win_rate = sum(1 for trade in trades if trade['profit'] > 0) / len(trades)
        self.profit_factor = self._calc_profit_factor(trades)
```

Then I can log:
```
Total Return: 15.3%
Sharpe Ratio: 1.2
Max Drawdown: -8.5%
Win Rate: 58%
```

This transforms backtest results from opaque numbers into actionable insights. It demonstrates advanced financial analysis—Course Outcome 3.

---

**Enhancement 2: Position Sizing**

I'll implement multiple position sizing strategies:

```python
class PositionSizer:
    def fixed_percentage(self, account_value, risk_percent=0.02):
        '''Risk 2% per trade'''
        return account_value * risk_percent / price
    
    def kelly_criterion(self, account_value, win_rate, profit_loss_ratio):
        '''Optimal position size given win rate'''
        kelly_frac = (win_rate * profit_loss_ratio - (1 - win_rate)) / profit_loss_ratio
        return account_value * kelly_frac
```

Now trades scale with account size and market conditions. This is more realistic and shows sophisticated financial knowledge.

---

**Enhancement 3: Risk Management**

I'll add stop-loss and take-profit logic:

```python
if position > 0:
    unrealized_loss = (entry_price - current_price) / entry_price
    if unrealized_loss > STOP_LOSS_PCT:
        # Force sell to limit losses
        position = 0
```

This protects against catastrophic losses—essential in real trading.

---

**Enhancement 4: Strategy Abstraction**

I'll create an abstract Strategy class and implement multiple strategies:

```python
class StrategyBase:
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        raise NotImplementedError

class MovingAverageCrossover(StrategyBase):
    # Current implementation
    
class MomentumStrategy(StrategyBase):
    # New: buy if price up 5% in last 20 days
    
class MeanReversionStrategy(StrategyBase):
    # New: buy if price down 10% from mean
```

This allows strategy comparison and demonstrates design patterns (polymorphism)—Course Outcome 1.

These enhancements show sophisticated algorithm design and financial knowledge—Course Outcome 3: implementing complex algorithms."

---

## CATEGORY 3: DATABASES (15-20 minutes)

### Part 3A: Existing Code Overview (5 min)

**Talking Points:**

"Now let's examine the database layer.

[Show dataStorage.py]

**Current Schema:**

```sql
CREATE TABLE stock_prices (
    date DATE,
    open NUMERIC(18, 6),
    high NUMERIC(18, 6),
    low NUMERIC(18, 6),
    close NUMERIC(18, 6),
    volume NUMERIC(18, 6),
    ticker VARCHAR(10),
    PRIMARY KEY (date, ticker)
)
```

**Strengths:**

**Strength 1: Efficient Batch Insertion**

[Show dataStorage.py, line 35-40]
We use execute_values() for batch insertion:
```python
execute_values(cur, '''
    INSERT INTO stock_prices (date, open, high, low, close, volume, ticker)
    VALUES %s
    ON CONFLICT (date, ticker) DO NOTHING
''', data_tuples)
```

Instead of:
```python
for row in data:
    cur.execute('INSERT ...')  # Slow! 500 trips to DB
```

We send 500 rows in one batch—much faster.

**Strength 2: SQL Injection Prevention**

The parameterized query structure prevents SQL injection. We're not concatenating user input into SQL strings.

**Strength 3: Conflict Handling**

ON CONFLICT (date, ticker) DO NOTHING means if we try to insert duplicate data, it silently skips instead of crashing. This is robust—we can re-run the job without errors.

**Strength 4: Composite Primary Key**

PRIMARY KEY (date, ticker) ensures we can't have duplicate prices for the same ticker on the same day. Data integrity is enforced at the database level."

---

### Part 3B: Weaknesses & Analysis (10 min)

**Talking Points:**

"**Finding 1: Missing Crucial Columns**

[Show the schema again]

The table stores OHLCV (Open, High, Low, Close, Volume), but real financial data needs more:

- **created_at, updated_at**: When was this row inserted/modified? Needed for auditing
- **data_source**: Did this come from Yahoo, Bloomberg, or our own model? Track data lineage
- **adjusted_close**: Stocks split and pay dividends. This column adjusts for those events
- **quality_flag**: Is the data trusted? Real-time feeds sometimes have errors before correction

Without these, I can't:
- Track data lineage (important for compliance)
- Handle corporate actions (mergers, splits)
- Know if data is stale or erroneous

---

**Finding 2: No Indexes for Common Queries**

Currently only the PRIMARY KEY is indexed. That means the (date, ticker) combination is fast, but:

Query: 'Get all AAPL data'
```sql
SELECT * FROM stock_prices WHERE ticker = 'AAPL'
```
This requires a full table scan—slow if we have millions of rows.

Query: 'Get data for a date range'
```sql
SELECT * FROM stock_prices 
WHERE date BETWEEN '2020-01-01' AND '2020-12-31'
```
Also a full scan.

I should add:
```sql
CREATE INDEX idx_ticker ON stock_prices(ticker);
CREATE INDEX idx_date ON stock_prices(date);
CREATE INDEX idx_ticker_date ON stock_prices(ticker, date);
```

---

**Finding 3: Missing Data Integrity Constraints**

The schema has no CHECK constraints:

```sql
-- Should prices be negative? No!
-- Should volume be zero? Maybe, but unusual.
-- Should open be higher than high? Never!
```

Currently:
- Invalid data could be inserted
- The application assumes data is valid
- If data is corrupted, we don't catch it until analysis fails

Better:
```sql
ALTER TABLE stock_prices
ADD CHECK (open > 0 AND high > 0 AND low > 0 AND close > 0),
ADD CHECK (high >= low),
ADD CHECK (high >= open AND high >= close),
ADD CHECK (low <= open AND low <= close),
ADD CHECK (volume >= 0),
ADD CONSTRAINT fk_ticker FOREIGN KEY (ticker) REFERENCES tickers(symbol);
```

---

**Finding 4: No Scalability Strategy**

[Show the data insert logic]

All data goes into one table. As we add more tickers and more historical data, the table grows:

- 1 ticker, 1 year: ~250 rows
- 500 tickers, 10 years: ~1.25 million rows
- 5,000 tickers, 20 years: ~25 million rows

At 25 million rows:
- Queries slow down
- Indexes become large
- Backups take forever
- We might not even fit in memory for analysis

I should consider:
- **Table partitioning by date** (monthly or yearly partitions)
- **Archival strategy** (move old data to cold storage)
- **Time-series database** (TimescaleDB extension) built for this exact use case

---

**Finding 5: Generic Error Handling & No Connection Pooling**

[Show dataStorage.py, line 47-48]
```python
except Exception as e:
    print(f'Error storing data: {e}')
```

If the database is temporarily down:
- We fail immediately with no retry
- We don't know if it's a transient error or permanent
- We should have exponential backoff

Also, each call to store_data() creates a new connection. If we call this function 1,000 times:
- 1,000 connection handshakes (slow)
- 1,000 connection teardowns

A connection pool would reuse 5-10 connections, much faster.

---

**Finding 6: No Audit Trail**

If data gets deleted or modified, we have no record:
- Who deleted it?
- When?
- What was the value before?

For compliance and debugging, we need an audit table or versioning."

---

### Part 3C: Planned Enhancements (5 min)

**Talking Points:**

"**Enhancement 1: Enhanced Schema with Normalization**

I'll redesign to:

```sql
-- Ticker master table
CREATE TABLE tickers (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Stock prices (normalized with FK)
CREATE TABLE stock_prices (
    id SERIAL PRIMARY KEY,
    ticker_id INTEGER NOT NULL REFERENCES tickers(id),
    date DATE NOT NULL,
    open NUMERIC(18, 6) NOT NULL,
    high NUMERIC(18, 6) NOT NULL,
    low NUMERIC(18, 6) NOT NULL,
    close NUMERIC(18, 6) NOT NULL,
    adjusted_close NUMERIC(18, 6),
    volume BIGINT NOT NULL,
    data_source VARCHAR(50),
    quality_flag VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker_id, date),
    CHECK (open > 0 AND close > 0 AND volume >= 0),
    CHECK (high >= low)
);

-- Audit table
CREATE TABLE stock_prices_audit (
    id SERIAL PRIMARY KEY,
    price_id INTEGER,
    action VARCHAR(10),
    old_values JSONB,
    new_values JSONB,
    changed_at TIMESTAMP DEFAULT NOW()
);
```

This demonstrates professional database design—normalization, referential integrity, audit trails. Course Outcome 4.

---

**Enhancement 2: Query Optimization**

I'll add indexes:
```sql
CREATE INDEX idx_ticker_id_date ON stock_prices(ticker_id, date);
CREATE INDEX idx_ticker_date ON stock_prices(ticker_id) INCLUDE (date);
```

Then analyze query performance with EXPLAIN ANALYZE to find bottlenecks.

---

**Enhancement 3: Scalability**

I'll implement table partitioning by date:

```sql
CREATE TABLE stock_prices (...)
PARTITION BY RANGE (EXTRACT(YEAR FROM date)) (
    PARTITION stock_prices_2020 VALUES FROM (2020) TO (2021),
    PARTITION stock_prices_2021 VALUES FROM (2021) TO (2022),
    ...
);
```

This allows:
- Old partitions to be archived to cheaper storage
- Parallel queries across partitions
- Easier maintenance (drop old year without touching recent data)

---

**Enhancement 4: Connection Pooling & Resilience**

I'll implement connection pooling:

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'postgresql://...',
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600
)
```

And add retry logic:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential())
def insert_with_retry(data, ticker):
    store_data(data, ticker)
```

This makes the system production-ready—resilient to transient failures.

---

**Enhancement 5: Monitoring & Performance**

I'll add:
- Slow query log to find problematic queries
- Table size monitoring (alert when table is growing too fast)
- Backup and recovery procedures
- Query performance dashboard

These enhancements demonstrate advanced database design, scalability, and professional operations—Course Outcome 4: designing effective databases."

---

## CLOSING REMARKS (2-3 minutes)

"So to summarize:

**Software Design**: I have a solid modular foundation, but I need better error handling, configuration management, input validation, and testing.

**Algorithms**: My MA strategy works, but it's static and has no risk management. I need performance metrics, adaptive strategies, and position sizing.

**Databases**: The schema is simple but missing crucial fields, indexes, and scalability. I need normalization, query optimization, and connection management.

**Priority for enhancement:**

Phase 1 (Critical):
- Add type hints and docstrings
- Implement logging
- Add indexes to database
- Implement basic performance metrics

Phase 2 (Important):
- Configuration framework
- Input validation
- Position sizing and stop-loss
- Connection pooling

Phase 3 (Nice-to-have):
- Multiple strategies
- Table partitioning
- Audit trail
- Advanced metrics

These enhancements will demonstrate all five course outcomes:
1. **Component-based development**: Modular design, testing
2. **Professional-quality applications**: Logging, configuration, error handling
3. **Complex algorithms**: Performance metrics, risk management, multiple strategies
4. **Effective databases**: Normalization, indexing, scalability
5. **Professional communication**: Documentation, code clarity

Thanks for watching."

---

## APPENDIX: Visual Aids You Can Show

- **Architecture diagram**: Data flow from yfinance → Validator → Strategy → BacktestEngine → Database
- **Schema diagram**: Tables and relationships
- **Performance chart**: Portfolio value over time (current backtest result)
- **Code snippets**: Key functions to highlight strengths/weaknesses
