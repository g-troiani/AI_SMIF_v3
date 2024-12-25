import sqlite3
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

def save_performance_metrics(db_path: str, metrics: dict, mode: str = 'backtest'):
    """
    Saves performance metrics to a specified database.

    :param db_path: Path to the database file.
    :param metrics: Dictionary of fields, e.g. {
        'strategy_name': 'MACDStrategy',
        'ticker': 'AAPL',
        'start_date': '2022-01-01',
        'end_date': '2022-06-01',
        'cagr': 0.10,
        'total_return_pct': 15.0,
        'max_drawdown': -8.2,
        ...
    }
    :param mode: 'backtest' or 'live' or anything else as needed.
    """

    logger.info(f"save_performance_metrics called with mode={mode}, db_path={db_path}")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Single table for demonstration
    table_name = "performance_data"

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mode TEXT,
        strategy_name TEXT,
        ticker TEXT,
        start_date TEXT,
        end_date TEXT,
        cagr REAL,
        total_return_pct REAL,
        max_drawdown REAL,
        timestamp TEXT
    );
    """

    insert_sql = f"""
    INSERT INTO {table_name} (
        mode, strategy_name, ticker, start_date, end_date,
        cagr, total_return_pct, max_drawdown, timestamp
    ) VALUES (
        :mode, :strategy_name, :ticker, :start_date, :end_date,
        :cagr, :total_return_pct, :max_drawdown, :timestamp
    )
    """

    # Minimal example fields
    insert_dict = {
        'mode': mode,
        'strategy_name': metrics.get('strategy_name', ''),
        'ticker': metrics.get('ticker', ''),
        'start_date': metrics.get('start_date', ''),
        'end_date': metrics.get('end_date', ''),
        'cagr': metrics.get('cagr', 0.0),
        'total_return_pct': metrics.get('total_return_pct', 0.0),
        'max_drawdown': metrics.get('max_drawdown', 0.0),
        'timestamp': datetime.utcnow().isoformat()
    }

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        cursor.execute(insert_sql, insert_dict)
        conn.commit()
        logger.info(f"Performance metrics saved to {db_path} in table {table_name} (mode={mode}).")
    except Exception as e:
        logger.error(f"Error saving performance metrics: {str(e)}")
    finally:
        if conn:
            conn.close()
