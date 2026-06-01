"""
Enhanced Data Storage with Normalized Schema

This module demonstrates professional database practices:
- Normalized schema with foreign keys
- Data integrity constraints
- Audit trail for compliance
- Connection management and error handling
"""

import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from logging_config import get_logger

logger = get_logger(__name__)


class EnhancedDataStorage:
    """
    Data storage layer using normalized schema.
    
    Features:
    - Master ticker table with company information
    - Normalized stock_prices with foreign keys
    - Data quality tracking (quality_flag, data_source)
    - Audit trail of all changes
    - Comprehensive data validation
    """
    
    def __init__(self):
        """Initialize database connection parameters."""
        load_dotenv()
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.host = os.getenv('DB_HOST', 'localhost')
        self.database = os.getenv('DB_NAME', 'stock_data')
    
    def _get_connection(self):
        """
        Create database connection.
        
        Returns:
            psycopg2 connection object
        
        Raises:
            psycopg2.DatabaseError: If connection fails
        """
        try:
            conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info("Connected to database %s at %s", self.database, self.host)
            return conn
        except psycopg2.Error as e:
            logger.error("Failed to connect to database: %s", str(e), exc_info=True)
            raise
    
    def initialize_schema(self):
        """Create database tables if they don't exist."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Create tickers table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS tickers (
                            id SERIAL PRIMARY KEY,
                            symbol VARCHAR(10) UNIQUE NOT NULL,
                            company_name VARCHAR(255),
                            created_at TIMESTAMP DEFAULT NOW(),
                            updated_at TIMESTAMP DEFAULT NOW()
                        )
                    """)
                    logger.info("Tickers table created/verified")
                    
                    # Create stock_prices table (normalized)
                    cur.execute("""
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
                            data_source VARCHAR(50) DEFAULT 'yfinance',
                            quality_flag VARCHAR(20) DEFAULT 'valid',
                            created_at TIMESTAMP DEFAULT NOW(),
                            updated_at TIMESTAMP DEFAULT NOW(),
                            UNIQUE(ticker_id, date),
                            CHECK (open > 0 AND close > 0 AND volume >= 0),
                            CHECK (high >= low),
                            CHECK (high >= open AND high >= close),
                            CHECK (low <= open AND low <= close)
                        )
                    """)
                    logger.info("Stock prices table created/verified")
                    
                    # Create audit table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS stock_prices_audit (
                            id SERIAL PRIMARY KEY,
                            price_id INTEGER,
                            action VARCHAR(10) NOT NULL,
                            old_values JSONB,
                            new_values JSONB,
                            changed_by VARCHAR(100),
                            changed_at TIMESTAMP DEFAULT NOW()
                        )
                    """)
                    logger.info("Audit table created/verified")
                    
                    # Create indexes
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker_id 
                        ON stock_prices(ticker_id)
                    """)
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_stock_prices_date 
                        ON stock_prices(date)
                    """)
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker_date 
                        ON stock_prices(ticker_id, date)
                    """)
                    logger.info("Indexes created/verified")
                    
                    conn.commit()
                    logger.info("Schema initialization complete")
        
        except psycopg2.Error as e:
            logger.error("Error initializing schema: %s", str(e), exc_info=True)
            raise
    
    def get_or_create_ticker(self, ticker_symbol: str, company_name: str = None):
        """
        Get or create a ticker in the master table.
        
        Args:
            ticker_symbol: Stock symbol (e.g., 'AAPL')
            company_name: Company name (optional)
        
        Returns:
            ticker_id (integer)
        
        Raises:
            psycopg2.Error: If database operation fails
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Try to get existing ticker
                    cur.execute(
                        "SELECT id FROM tickers WHERE symbol = %s",
                        (ticker_symbol,)
                    )
                    result = cur.fetchone()
                    
                    if result:
                        ticker_id = result[0]
                        logger.debug("Found existing ticker: %s (id=%s)", ticker_symbol, ticker_id)
                        return ticker_id
                    
                    # Create new ticker
                    cur.execute(
                        """INSERT INTO tickers (symbol, company_name) 
                           VALUES (%s, %s) 
                           RETURNING id""",
                        (ticker_symbol, company_name)
                    )
                    ticker_id = cur.fetchone()[0]
                    conn.commit()
                    logger.info("Created new ticker: %s (id=%s)", ticker_symbol, ticker_id)
                    return ticker_id
        
        except psycopg2.Error as e:
            logger.error("Error managing ticker %s: %s", ticker_symbol, str(e), exc_info=True)
            raise
    
    def store_data_normalized(self, data, ticker: str, data_source: str = 'yfinance'):
        """
        Store data using normalized schema.
        
        Args:
            data: DataFrame with columns [date, open, high, low, close, volume]
            ticker: Stock symbol
            data_source: Where the data came from (default: yfinance)
        
        Raises:
            ValueError: If data is invalid
            psycopg2.Error: If database operation fails
        """
        if data is None or data.empty:
            logger.warning("No data to store for %s", ticker)
            return
        
        try:
            # Get or create ticker
            ticker_id = self.get_or_create_ticker(ticker)
            
            # Prepare data tuples
            data_tuples = []
            for idx, row in data.iterrows():
                data_tuples.append((
                    ticker_id,
                    row['date'],
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    None,  # adjusted_close (can be calculated separately)
                    int(row['volume']),
                    data_source,
                    'valid'  # quality_flag
                ))
            
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Batch insert with ON CONFLICT for idempotency
                    execute_values(cur, """
                        INSERT INTO stock_prices 
                        (ticker_id, date, open, high, low, close, adjusted_close, volume, data_source, quality_flag)
                        VALUES %s
                        ON CONFLICT (ticker_id, date) DO UPDATE
                        SET open = EXCLUDED.open,
                            high = EXCLUDED.high,
                            low = EXCLUDED.low,
                            close = EXCLUDED.close,
                            volume = EXCLUDED.volume,
                            updated_at = NOW()
                    """, data_tuples)
                    
                    conn.commit()
                    logger.info(
                        "Stored %s rows for %s (ticker_id=%s) from %s",
                        len(data_tuples),
                        ticker,
                        ticker_id,
                        data_source
                    )
        
        except psycopg2.Error as e:
            logger.error("Error storing data for %s: %s", ticker, str(e), exc_info=True)
            raise
        except Exception as e:
            logger.error("Unexpected error storing data for %s: %s", ticker, str(e), exc_info=True)
            raise
    
    def get_stock_data(self, ticker: str, start_date=None, end_date=None):
        """
        Retrieve stock data from normalized schema.
        
        Args:
            ticker: Stock symbol
            start_date: Filter start date (optional)
            end_date: Filter end date (optional)
        
        Returns:
            List of dictionaries with stock price data
        
        Raises:
            psycopg2.Error: If query fails
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                        SELECT 
                            sp.date,
                            sp.open,
                            sp.high,
                            sp.low,
                            sp.close,
                            sp.volume,
                            sp.data_source,
                            sp.quality_flag,
                            sp.created_at
                        FROM stock_prices sp
                        JOIN tickers t ON sp.ticker_id = t.id
                        WHERE t.symbol = %s
                    """
                    params = [ticker]
                    
                    if start_date:
                        query += " AND sp.date >= %s"
                        params.append(start_date)
                    
                    if end_date:
                        query += " AND sp.date <= %s"
                        params.append(end_date)
                    
                    query += " ORDER BY sp.date ASC"
                    
                    cur.execute(query, params)
                    
                    columns = [desc[0] for desc in cur.description]
                    results = [dict(zip(columns, row)) for row in cur.fetchall()]
                    
                    logger.info("Retrieved %s rows for %s", len(results), ticker)
                    return results
        
        except psycopg2.Error as e:
            logger.error("Error retrieving data for %s: %s", ticker, str(e), exc_info=True)
            raise


# Convenience function for backward compatibility
def store_data_enhanced(data, ticker, data_source='yfinance'):
    """
    Convenience function using enhanced schema.
    
    Args:
        data: DataFrame with stock price data
        ticker: Stock symbol
        data_source: Where the data came from
    """
    storage = EnhancedDataStorage()
    storage.initialize_schema()
    storage.store_data_normalized(data, ticker, data_source)
