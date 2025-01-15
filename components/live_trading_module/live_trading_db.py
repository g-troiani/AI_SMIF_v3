# components/live_trading_module/live_trading_db.py

import sqlite3
from pathlib import Path
from datetime import datetime
import logging
from components.data_management_module.config import config

logger = logging.getLogger(__name__)

class LiveTradingDB:
    """
    Sprint 4:
    - Already have tables: live_prices, account_equity, live_trades.
    - Add indexes for better performance.
    - Confirmed schema stability.
    """

    def __init__(self):
        self.db_path = Path(config.get('DEFAULT', 'live_trading_database_path'))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS live_prices (
                symbol TEXT,
                timestamp DATETIME,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                PRIMARY KEY (symbol, timestamp)
            ) WITHOUT ROWID;            
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS account_equity (
                timestamp DATETIME PRIMARY KEY,
                equity REAL
            ) WITHOUT ROWID;
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS live_trades (
                strategy_name TEXT,
                timestamp DATETIME,
                symbol TEXT,
                side TEXT,
                qty INTEGER,
                price REAL,
                PRIMARY KEY (strategy_name, timestamp, symbol)
            ) WITHOUT ROWID;
            """)

            # Add indexes for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_live_prices_symbol ON live_prices (symbol);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_live_prices_timestamp ON live_prices (timestamp);")

            conn.execute("CREATE INDEX IF NOT EXISTS idx_live_trades_strategy ON live_trades (strategy_name);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_live_trades_symbol ON live_trades (symbol);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_live_trades_timestamp ON live_trades (timestamp);")


    def save_market_data_point(self, symbol, timestamp, o, h, l, c, v):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                INSERT OR IGNORE INTO live_prices (symbol, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (symbol, timestamp.isoformat(), o, h, l, c, v))
                # Consider running ANALYZE after many inserts or periodically
                # For simplicity, no frequent ANALYZE here. If needed, we can add a counter.
        except Exception as e:
            logger.error(f"Error saving market data point: {str(e)}")

    def save_account_equity(self, timestamp, equity):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                INSERT OR REPLACE INTO account_equity (timestamp, equity)
                VALUES (?, ?)
                """, (timestamp.isoformat(), equity))
        except Exception as e:
            logger.error(f"Error saving account equity: {str(e)}")

    def save_trade(self, strategy_name, timestamp, symbol, side, qty, price):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                INSERT OR IGNORE INTO live_trades (strategy_name, timestamp, symbol, side, qty, price)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (strategy_name, timestamp.isoformat(), symbol, side, qty, price))
        except Exception as e:
            logger.error(f"Error saving trade: {str(e)}")
    # Optional helper methods for debugging or data retrieval (not required but helpful)
    def get_latest_price(self, symbol):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("""
                SELECT * FROM live_prices
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """, (symbol,))
                row = cur.fetchone()
                return row
        except Exception as e:
            logger.error(f"Error retrieving latest price for {symbol}: {str(e)}")
            return None

