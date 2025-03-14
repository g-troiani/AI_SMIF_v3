# File: components/backtesting_module/results_viewer.py
# Type: py

import pandas as pd
import sqlite3
import json
from datetime import datetime

class ResultsViewer:
    """
    Handles retrieval and visualization of backtest results.
    """
    
    def __init__(self):
        self.db_path = 'data/results/backtest_results.db'
    
    def get_results(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT * FROM backtest_results 
            ORDER BY timestamp DESC 
            LIMIT ?
        """
        results = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()

        results['strategy_params'] = results['strategy_params'].apply(json.loads)
        return results

    def get_specific_result(self, backtest_id):
        conn = sqlite3.connect(self.db_path)
        query = "SELECT * FROM backtest_results WHERE id = ?"
        result = pd.read_sql_query(query, conn, params=(backtest_id,))
        conn.close()

        if not result.empty:
            result['strategy_params'] = result['strategy_params'].apply(json.loads)
        return result
