# app.py or db_init.py

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'backtesting_results.db')

def initialize_db():
    """
    Example single DB init function that ensures tables exist without duplicating code.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Existing 'backtest_summary' or other tables creation might already be here.

    # 1) Create or ensure "strategies" table exists:
    cur.execute('''
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            mode TEXT DEFAULT 'backtest' CHECK(mode IN ('backtest','live')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
