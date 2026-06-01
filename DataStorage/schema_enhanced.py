"""
Enhanced Database Schema with Normalization
Demonstrates professional database design patterns:
- Normalized schema with foreign keys
- Data integrity constraints (CHECK constraints)
- Audit trails for compliance
- Audit table for change tracking
"""

CREATE_TICKERS_TABLE = """
CREATE TABLE IF NOT EXISTS tickers (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
"""

CREATE_STOCK_PRICES_TABLE = """
CREATE TABLE IF NOT EXISTS stock_prices (
    id SERIAL PRIMARY KEY,
    ticker_id INTEGER NOT NULL REFERENCES tickers(id) ON DELETE CASCADE,
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
    CHECK (high >= low),
    CHECK (high >= open AND high >= close),
    CHECK (low <= open AND low <= close)
);
"""

CREATE_STOCK_PRICES_AUDIT_TABLE = """
CREATE TABLE IF NOT EXISTS stock_prices_audit (
    id SERIAL PRIMARY KEY,
    price_id INTEGER,
    action VARCHAR(10) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT NOW()
);
"""

# Indexes for common queries
CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker_id ON stock_prices(ticker_id);
CREATE INDEX IF NOT EXISTS idx_stock_prices_date ON stock_prices(date);
CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker_date ON stock_prices(ticker_id, date);
CREATE INDEX IF NOT EXISTS idx_tickers_symbol ON tickers(symbol);
"""

SCHEMA_COMPARISON = """
OLD SCHEMA (Simple, Denormalized):
====================================
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

Limitations:
- Ticker string repeated for every row (data duplication)
- No foreign key to enforce referential integrity
- No audit trail for compliance
- No data quality tracking (quality_flag)
- No data lineage tracking (data_source)
- No history of data changes
- Limited data validation (no CHECK constraints)


NEW SCHEMA (Normalized):
========================
1. tickers (master table):
   - Centralized ticker information
   - Eliminates duplication
   - Foreign key enforcement

2. stock_prices (normalized facts):
   - Cleaner data model
   - References tickers via FK
   - Enhanced columns for production use:
     * adjusted_close: Handle stock splits/dividends
     * data_source: Track data lineage
     * quality_flag: Mark data quality issues
     * created_at/updated_at: Audit timestamps
   - CHECK constraints enforce data integrity

3. stock_prices_audit (audit trail):
   - Track all changes for compliance
   - Record who/what/when for modifications
   - Support for data recovery

Benefits:
✓ Data Integrity: Foreign keys and CHECK constraints
✓ No Duplication: Ticker stored once in tickers table
✓ Audit Trail: Complete history of changes
✓ Data Lineage: Know where data came from
✓ Quality Tracking: Flag unreliable data
✓ Compliance: Full audit trail for regulators
✓ Performance: Indexes on common queries
✓ Scalability: Ready for table partitioning
"""

print(SCHEMA_COMPARISON)
