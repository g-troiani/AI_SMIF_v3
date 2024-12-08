import sqlite3
import logging
from datetime import datetime
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            # Create data directory in project root if it doesn't exist
            data_dir = Path(__file__).parent.parent.parent / 'data'
            data_dir.mkdir(exist_ok=True)
            self.db_path = data_dir / 'market_data.db'
        else:
            self.db_path = Path(db_path)
        
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS historical_data (
                    ticker_symbol TEXT,
                    timestamp DATETIME,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    PRIMARY KEY (ticker_symbol, timestamp)
                ) WITHOUT ROWID;
            """)

    def save_historical_data(self, ticker: str, data: pd.DataFrame) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                records = data.apply(
                    lambda row: (
                        ticker,
                        row.name.isoformat(),
                        row['open'],
                        row['high'],
                        row['low'],
                        row['close'],
                        row['volume']
                    ),
                    axis=1
                ).tolist()
                
                cursor.executemany("""
                    INSERT OR IGNORE INTO historical_data 
                    (ticker_symbol, timestamp, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, records)
                
                new_records = cursor.rowcount
                logger.info(f"Inserted {new_records} new records for {ticker}")
                return new_records
                
        except Exception as e:
            logger.error(f"Error saving historical data for {ticker}: {str(e)}")
            raise

    def get_last_timestamp(self, ticker: str) -> datetime:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT MAX(timestamp) 
                    FROM historical_data 
                    WHERE ticker_symbol = ?
                """, (ticker,))
                result = cursor.fetchone()[0]
                return datetime.fromisoformat(result) if result else None
                
        except Exception as e:
            logger.error(f"Error getting last timestamp for {ticker}: {str(e)}")
            return None