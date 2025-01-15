# components/portfolio_management_module/monitor.py

import sqlite3
from datetime import datetime
import threading
from queue import Queue

class PortfolioMonitor:
    def __init__(self, db_path="data/portfolio.db"):
        self.db_path = db_path
        self._initialize_db()
        self.update_queue = Queue()
        self.monitor_thread = None
        self.is_running = False

    def _initialize_db(self):
        """Initialize SQLite database for storing portfolio data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio_values (
            timestamp DATETIME,
            strategy_id TEXT,
            value REAL,
            cash_balance REAL
        )''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS strategy_allocations (
            timestamp DATETIME,
            strategy_id TEXT,
            allocation REAL
        )''')
        
        conn.commit()
        conn.close()

    def start_monitoring(self):
        """Start the monitoring thread."""
        if not self.is_running:
            self.is_running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join()

    def _monitor_loop(self):
        """Main monitoring loop that processes updates."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        while self.is_running:
            try:
                update = self.update_queue.get(timeout=1.0)
                timestamp = datetime.now()
                
                if update['type'] == 'portfolio_value':
                    cursor.execute(
                        'INSERT INTO portfolio_values VALUES (?, ?, ?, ?)',
                        (timestamp, update['strategy_id'], update['value'], update['cash_balance'])
                    )
                elif update['type'] == 'allocation':
                    cursor.execute(
                        'INSERT INTO strategy_allocations VALUES (?, ?, ?)',
                        (timestamp, update['strategy_id'], update['allocation'])
                    )
                
                conn.commit()
                
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                continue
        
        conn.close()

    def record_portfolio_value(self, strategy_id, value, cash_balance):
        """Queue a portfolio value update."""
        self.update_queue.put({
            'type': 'portfolio_value',
            'strategy_id': strategy_id,
            'value': value,
            'cash_balance': cash_balance
        })

    def record_allocation(self, strategy_id, allocation):
        """Queue an allocation update."""
        self.update_queue.put({
            'type': 'allocation',
            'strategy_id': strategy_id,
            'allocation': allocation
        })

    def get_strategy_history(self, strategy_id, start_date=None, end_date=None):
        """Retrieve historical data for a strategy."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
        SELECT timestamp, value, cash_balance 
        FROM portfolio_values 
        WHERE strategy_id = ?
        '''
        params = [strategy_id]
        
        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date)
            
        query += ' ORDER BY timestamp'
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        return results
