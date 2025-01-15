# File: components/backtesting_module/results_viewer.py
# Type: py

import pandas as pd
import sqlite3
import json
import logging
from datetime import datetime

class ResultsViewer:
    """
    Handles retrieval and visualization of backtest results.
    Now updated to unify queries from both 'backtest_results' (older) and 
    'backtest_summary' (newer) so the UI sees all data.
    """

    def __init__(self):
        # Keep the old DB path, so we do not break references.
        # self.db_path = 'data/results/backtest_results.db'
        self.db_path = 'data/results/backtest_summary.db'
        self.logger = logging.getLogger(__name__)

    def get_results(self, limit=10):
        """
        Returns backtest results strictly from 'backtest_summary',
        ignoring the old 'backtest_results' table.

        We select the common columns:
        id, strategy_name, strategy_params, ticker,
        start_date, end_date, final_value, total_return,
        sharpe_ratio, max_drawdown, timestamp
        and simply order them by timestamp DESC, limiting rows as requested.
        """

        conn = sqlite3.connect(self.db_path)
        try:
            query = f"""
                SELECT
                    id,
                    strategy_name,
                    strategy_params,
                    ticker,
                    start_date,
                    end_date,
                    final_value,
                    total_return,
                    sharpe_ratio,
                    max_drawdown,
                    timestamp
                FROM backtest_summary
                ORDER BY timestamp DESC
                LIMIT ?
            """

            results = pd.read_sql_query(query, conn, params=(limit,))
        except Exception as e:
            self.logger.error(f"Error loading backtest results from backtest_summary: {e}")
            raise
        finally:
            conn.close()

        # Convert 'strategy_params' from JSON if present
        def try_json_load(s):
            if s is None:
                return {}
            try:
                return json.loads(s)
            except:
                return {}

        if not results.empty:
            results['strategy_params'] = results['strategy_params'].apply(try_json_load)

        return results



    def get_specific_result(self, backtest_id):
        """
        Gets a single row by 'id'. 
        Because 'id' might be in the old 'backtest_results' or 
        in the new 'backtest_summary', we do a two-step approach:

         1) Look in backtest_results WHERE id = ?
         2) If not found, look in backtest_summary WHERE id = ?

        This ensures we do not break code that expects to pass 
        an ID referencing either table.
        """

        conn = sqlite3.connect(self.db_path)
        try:
            # Step 1: Attempt in old table
            query_old = "SELECT * FROM backtest_results WHERE id = ?"
            result_old = pd.read_sql_query(query_old, conn, params=(backtest_id,))

            if not result_old.empty:
                # parse strategy_params
                result_old['strategy_params'] = result_old['strategy_params'].apply(
                    lambda s: json.loads(s) if s else {}
                )
                return result_old

            # Step 2: If not found, attempt in new table
            query_new = "SELECT * FROM backtest_summary WHERE id = ?"
            result_new = pd.read_sql_query(query_new, conn, params=(backtest_id,))
            if not result_new.empty:
                # parse strategy_params
                result_new['strategy_params'] = result_new['strategy_params'].apply(
                    lambda s: json.loads(s) if s else {}
                )
                return result_new

            # If neither table has a row, return empty DataFrame
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Error loading specific result ID={backtest_id}: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
