# components/data_management_module/feature_engineer.py

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import os
from pathlib import Path

MARKET_DB_PATH = 'data/market_data.db'
MODELING_DB_PATH = 'data/modeling_data.db'
WINDOW = 14

class FeatureEngineer:
    """Handles creation and updating of modeling_data.db from market_data.db"""

    def __init__(self, market_db_path=MARKET_DB_PATH, modeling_db_path=MODELING_DB_PATH, window=WINDOW):
        self.market_db_path = market_db_path
        self.modeling_db_path = modeling_db_path
        self.window = window

        # Ensure modeling_data.db is initialized
        self._init_modeling_db()

    def _init_modeling_db(self):
        """Initialize the modeling_data.db if not already done."""
        conn = sqlite3.connect(self.modeling_db_path)
        cur = conn.cursor()
        # Create table if not exists
        # We'll keep the same schema as previously discussed
        # If it already exists, we won't drop it.
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS modeling_data (
            ticker_symbol TEXT,
            timestamp DATETIME,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            return REAL,
            vol REAL,
            mom REAL,
            sma REAL,
            rolling_min REAL,
            rolling_max REAL,
            diff_close REAL,
            PRIMARY KEY (ticker_symbol, timestamp)
        ) WITHOUT ROWID;
        """
        cur.execute(create_table_sql)
        conn.commit()
        conn.close()

    def update_modeling_data_for_ticker(self, ticker, start_date=None, end_date=None):
        """
        Fetch data for a specific ticker from market_data.db,
        compute features, and update modeling_data.db.

        If start_date/end_date are provided, use them to limit the range.
        Otherwise, it fetches all data.
        """
        market_conn = sqlite3.connect(self.market_db_path)
        query = f"SELECT ticker_symbol, timestamp, open, high, low, close, volume FROM historical_data WHERE ticker_symbol='{ticker}'"
        if start_date is not None:
            query += f" AND timestamp >= '{start_date.isoformat()}'"
        if end_date is not None:
            query += f" AND timestamp <= '{end_date.isoformat()}'"
        query += " ORDER BY timestamp ASC"

        data = pd.read_sql_query(query, market_conn, parse_dates=['timestamp'])
        market_conn.close()

        if data.empty:
            # No new data for this ticker
            return

        data.set_index('timestamp', inplace=True)

        # Compute features
        data['return'] = np.log(data['close'] / data['close'].shift(1))
        data['vol'] = data['return'].rolling(self.window).std()
        data['mom'] = np.sign(data['return'].rolling(self.window).mean())
        data['sma'] = data['close'].rolling(self.window).mean()
        data['rolling_min'] = data['close'].rolling(self.window).min()
        data['rolling_max'] = data['close'].rolling(self.window).max()
        data['diff_close'] = data['close'].diff()

        data.dropna(inplace=True)

        if data.empty:
            return

        data['ticker_symbol'] = ticker
        data.reset_index(inplace=True)

        # Insert or update into modeling_data.db
        modeling_conn = sqlite3.connect(self.modeling_db_path)
        # We'll use the 'replace' option so that if we re-run on overlapping data,
        # it updates the rows.
        data.to_sql('modeling_data', modeling_conn, if_exists='replace', index=False)
        modeling_conn.close()
