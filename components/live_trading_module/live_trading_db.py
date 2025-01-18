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
        # Create the usual live_* tables in self.db_path
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

            # Ensure we have a 'strategies' table in self.db_path so set_strategy_live() can UPDATE it
            conn.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                name TEXT PRIMARY KEY,
                mode TEXT NOT NULL DEFAULT 'backtest'
                    CHECK (mode IN ('live','backtest'))
            ) WITHOUT ROWID;
            """)

        # Also ensure the 'strategies' table exists in the DB used by is_strategy_live (the config DB)
        strategies_db = config.get('DEFAULT', 'database_path', fallback='data/market_data.db')
        try:
            with sqlite3.connect(strategies_db) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS strategies (
                    name TEXT PRIMARY KEY,
                    mode TEXT NOT NULL DEFAULT 'backtest'
                    CHECK (mode IN ('live','backtest'))
                ) WITHOUT ROWID;
                """)
        except Exception as e:
            logger.error(f"Error ensuring 'strategies' table in {strategies_db}: {str(e)}")



    def save_market_data_point(self, symbol, timestamp, o, h, l, c, v):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                INSERT OR IGNORE INTO live_prices (symbol, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (symbol, timestamp.isoformat(), o, h, l, c, v))
                # For simplicity, no frequent ANALYZE here. If needed, add a counter or scheduler.
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

    def get_latest_price(self, symbol):
        """Retrieve the most recent bar for a given symbol."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("""
                SELECT *
                FROM live_prices
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """, (symbol,))
                row = cur.fetchone()
                return row
        except Exception as e:
            logger.error(f"Error retrieving latest price for {symbol}: {str(e)}")
            return None
        
    def is_strategy_live(self, strategy_name: str) -> bool:
        """
        Checks the 'strategies' table in the DB (config's 'database_path') for mode='live'.
        """
        try:
            strategies_db = config.get('DEFAULT', 'database_path', fallback='data/market_data.db')
            with sqlite3.connect(strategies_db) as conn:
                cur = conn.cursor()
                row = cur.execute(
                    "SELECT mode FROM strategies WHERE name = ?",
                    (strategy_name,)
                ).fetchone()
                if row is not None and row[0] == 'live':
                    return True
        except Exception as e:
            logger.error(f"Error checking is_strategy_live for {strategy_name}: {str(e)}")
        return False



    ####################################################################
    # NEW METHOD ADDED: set_strategy_live
    # This fixes the AttributeError by providing the method that
    # LiveTradingManager.start() attempts to call (line 488).
    ####################################################################

    def set_strategy_live(self, strategy_name: str, is_live: bool):
        """
        Updates the 'strategies' table, setting mode='live' if is_live=True,
        or mode='backtest' if is_live=False.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                new_mode = 'live' if is_live else 'backtest'
                conn.execute("""
                    INSERT OR IGNORE INTO strategies (name, mode)
                    VALUES (?, 'backtest')
                """, (strategy_name,))
                conn.execute("""
                    UPDATE strategies
                       SET mode=?
                     WHERE name=?
                """, (new_mode, strategy_name))
                conn.commit()
                logger.info(f"Strategy {strategy_name} updated to mode='{new_mode}' in LiveTradingDB.")
        except Exception as e:
            logger.error(f"Error updating strategy {strategy_name} to mode='{new_mode}': {str(e)}")
            raise


    # ------------------------------------------------------------
    # FIX: Add get_last_market_timestamp to fix the AttributeError
    # ------------------------------------------------------------
    def get_last_market_timestamp(self, symbol: str):
        """
        Returns the most recent timestamp for the given symbol from live_prices,
        or None if no record is found.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                row = cur.execute("""
                    SELECT MAX(timestamp) as last_ts
                    FROM live_prices
                    WHERE symbol = ?
                """, (symbol,)).fetchone()

                if row and row['last_ts']:
                    return datetime.fromisoformat(row['last_ts'])
                return None

        except Exception as e:
            logger.error(f"Error getting last market timestamp for {symbol}: {str(e)}")
            return None