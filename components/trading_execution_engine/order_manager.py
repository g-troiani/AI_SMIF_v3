# File: components/trading_execution_engine/order_manager.py
# Type: py

import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
from .config import CONFIG  # Changed from config

class OrderManager:
    """
    Tracks order statuses and manages executions with performance monitoring.
    """

    def __init__(self):
        self.db_file = CONFIG['database']['orders_db']  # Changed from config
        os.makedirs('data', exist_ok=True)
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self.conn.execute('PRAGMA journal_mode=WAL;')
        try:
            self._create_tables()
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise

    def _create_tables(self):
        try:
            with self.conn:
                # Orders table
                self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS orders (
                        order_id TEXT PRIMARY KEY,
                        ticker TEXT,
                        quantity REAL,
                        side TEXT,
                        status TEXT,
                        submitted_at TEXT,
                        filled_at TEXT,
                        filled_qty REAL,
                        strategy_id TEXT,
                        execution_price REAL,
                        is_manual INTEGER DEFAULT 0
                    )
                ''')

                # Failed trades table
                self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS failed_trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trade_signal TEXT,
                        error_message TEXT,
                        timestamp TEXT,
                        retry_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        last_retry TEXT,
                        resolved_at TEXT
                    )
                ''')

                # Error log table
                self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS error_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_id TEXT,
                        error_type TEXT,
                        error_message TEXT,
                        timestamp TEXT,
                        additional_info TEXT
                    )
                ''')

                # Execution metrics table
                self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS execution_metrics (
                        order_id TEXT PRIMARY KEY,
                        submission_time TEXT,
                        execution_time TEXT,
                        execution_latency REAL,
                        intended_price REAL,
                        execution_price REAL,
                        price_slippage REAL,
                        order_type TEXT,
                        market_impact REAL,
                        strategy_id TEXT,
                        success INTEGER DEFAULT 1,
                        FOREIGN KEY (order_id) REFERENCES orders(order_id)
                    )
                ''')
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
            raise

    def add_order(self, order_info: Dict[str, Any]) -> None:
        """Adds a new order to the database with initial metrics."""
        if not isinstance(order_info, dict):
            raise ValueError("order_info must be a dictionary")

        try:
            with self.conn:
                # Insert order
                self.conn.execute('''
                    INSERT OR REPLACE INTO orders (
                        order_id, ticker, quantity, side, status, submitted_at,
                        filled_at, filled_qty, strategy_id, execution_price, is_manual
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    order_info['id'],
                    order_info['symbol'],
                    float(order_info['qty']),
                    order_info['side'],
                    order_info['status'],
                    order_info.get('submitted_at'),
                    order_info.get('filled_at'),
                    float(order_info.get('filled_qty', 0)),
                    order_info.get('client_order_id', ''),
                    float(order_info.get('filled_avg_price', 0)),
                    order_info.get('is_manual', 0)
                ))

                # Initialize execution metrics
                self.conn.execute('''
                    INSERT OR REPLACE INTO execution_metrics (
                        order_id, submission_time, order_type, strategy_id
                    ) VALUES (?, ?, ?, ?)
                ''', (
                    order_info['id'],
                    order_info.get('submitted_at'),
                    order_info.get('type', 'market'),
                    order_info.get('client_order_id', '')
                ))
        except sqlite3.Error as e:
            self.log_error(order_info.get('id'), 'database_error', str(e))
            raise
        except Exception as e:
            self.log_error(order_info.get('id'), 'unexpected_error', str(e))
            raise

    def update_order(self, order_info: Dict[str, Any]):
        """
        Updates an existing order and its execution metrics.
        """
        try:
            with self.conn:
                # Update order status
                self.conn.execute('''
                    UPDATE orders SET
                        status = ?,
                        filled_at = ?,
                        filled_qty = ?,
                        execution_price = ?
                    WHERE order_id = ?
                ''', (
                    order_info['status'],
                    order_info.get('filled_at'),
                    float(order_info.get('filled_qty', 0)),
                    float(order_info.get('filled_avg_price', 0)),
                    order_info['id']
                ))

                # Update execution metrics
                if order_info['status'] == 'filled':
                    submission_time = datetime.fromisoformat(order_info['submitted_at'].replace('Z', '+00:00')) if order_info.get('submitted_at') else datetime.utcnow()
                    fill_time = datetime.fromisoformat(order_info['filled_at'].replace('Z', '+00:00')) if order_info.get('filled_at') else datetime.utcnow()
                    execution_latency = (fill_time - submission_time).total_seconds()

                    self.conn.execute('''
                        UPDATE execution_metrics SET
                            execution_time = ?,
                            execution_latency = ?,
                            execution_price = ?,
                            price_slippage = ?,
                            success = 1
                        WHERE order_id = ?
                    ''', (
                        order_info['filled_at'],
                        execution_latency,
                        float(order_info.get('filled_avg_price', 0)),
                        self._calculate_slippage(order_info),
                        order_info['id']
                    ))
                elif order_info['status'] in ('canceled', 'rejected'):
                    self.conn.execute('''
                        UPDATE execution_metrics SET
                            success = 0
                        WHERE order_id = ?
                    ''', (order_info['id'],))

        except sqlite3.Error as e:
            self.log_error(order_info.get('id'), 'database_error', str(e))
            raise

    def _calculate_slippage(self, order_info: Dict[str, Any]) -> float:
        """
        Calculates price slippage for an order.
        """
        try:
            intended_price = float(order_info.get('limit_price', 0) or order_info.get('stop_price', 0))
            if intended_price == 0:  # Market order
                return 0.0

            executed_price = float(order_info.get('filled_avg_price', 0))
            side = order_info['side']

            if side == 'buy' and intended_price != 0:
                slippage = (executed_price - intended_price) / intended_price * 100
            elif side == 'sell' and intended_price != 0:
                slippage = (intended_price - executed_price) / intended_price * 100
            else:
                slippage = 0.0

            return round(slippage, 4)

        except (KeyError, ValueError) as e:
            return 0.0

    def get_execution_metrics(self, start_time: Optional[str] = None, end_time: Optional[str] = None) -> list:
        """
        Retrieves execution metrics for analysis.
        """
        try:
            query = '''
                SELECT 
                    em.*,
                    o.ticker,
                    o.quantity,
                    o.side
                FROM execution_metrics em
                JOIN orders o ON em.order_id = o.order_id
                WHERE 1=1
            '''
            params = []

            if start_time:
                query += ' AND em.submission_time >= ?'
                params.append(start_time)
            if end_time:
                query += ' AND em.submission_time <= ?'
                params.append(end_time)

            cursor = self.conn.execute(query, params)
            metrics = cursor.fetchall()
            cursor.close()

            return metrics

        except sqlite3.Error as e:
            print(f"Error retrieving execution metrics: {e}")
            raise

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves an order from the database.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,))
            order = cursor.fetchone()
            col_names = [description[0] for description in cursor.description]
            cursor.close()

            if order:
                return dict(zip(col_names, order))
            return None

        except sqlite3.Error as e:
            self.log_error(order_id, 'database_error', str(e))
            raise

    def log_failed_trade(self, trade_signal, error_message: str):
        """
        Logs a failed trade for recovery.
        """
        try:
            with self.conn:
                self.conn.execute('''
                    INSERT INTO failed_trades (
                        trade_signal,
                        error_message,
                        timestamp,
                        status
                    ) VALUES (?, ?, ?, ?)
                ''', (
                    json.dumps(trade_signal.to_dict()),
                    str(error_message),
                    datetime.utcnow().isoformat(),
                    'pending'
                ))
        except sqlite3.Error as e:
            print(f"Error logging failed trade: {e}")
            raise

    def get_pending_failed_trades(self, max_retry_count: int = 3) -> list:
        """
        Retrieves pending failed trades for recovery.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, trade_signal, error_message, retry_count
                FROM failed_trades
                WHERE status = 'pending'
                AND retry_count < ?
                ORDER BY timestamp ASC
            ''', (max_retry_count,))
            failed_trades = cursor.fetchall()
            cursor.close()
            return failed_trades
        except sqlite3.Error as e:
            print(f"Error retrieving failed trades: {e}")
            raise

    def update_failed_trade_status(self, trade_id: int, status: str, error_message: Optional[str] = None):
        """
        Updates the status of a failed trade.
        """
        try:
            with self.conn:
                if status == 'retry':
                    self.conn.execute('''
                        UPDATE failed_trades
                        SET retry_count = retry_count + 1,
                            last_retry = ?,
                            error_message = CASE WHEN ? IS NOT NULL THEN ? ELSE error_message END
                        WHERE id = ?
                    ''', (datetime.utcnow().isoformat(), error_message, error_message, trade_id))
                else:
                    self.conn.execute('''
                        UPDATE failed_trades
                        SET status = ?,
                            resolved_at = ?
                        WHERE id = ?
                    ''', (status, datetime.utcnow().isoformat(), trade_id))
        except sqlite3.Error as e:
            print(f"Error updating failed trade status: {e}")
            raise

    def log_error(self, order_id: str, error_type: str, error_message: str, additional_info: Optional[Dict] = None):
        """
        Logs an error in the error_log table.
        """
        try:
            with self.conn:
                self.conn.execute('''
                    INSERT INTO error_log (
                        order_id,
                        error_type,
                        error_message,
                        timestamp,
                        additional_info
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    order_id,
                    error_type,
                    error_message,
                    datetime.utcnow().isoformat(),
                    json.dumps(additional_info) if additional_info else None
                ))
        except sqlite3.Error as e:
            print(f"Error logging error: {e}")
            raise

    def close(self):
        """
        Closes the database connection.
        """
        self.conn.close()
