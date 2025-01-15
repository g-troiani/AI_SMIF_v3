# File: components/strategy_management_module/strategy_manager.py
# Type: py

import logging
from typing import Dict, Any, List
import sqlite3
import json
from components.data_management_module.config import config  # Ensure we use the unified config in data_management_module
# If we need a live trading manager import:
from components.live_trading_module.live_trading_manager import LiveTradingManager


logger = logging.getLogger('strategy_manager')


class ParameterValidator:
    """
    Validates strategy parameters and enforces optimization limits.
    Example parameter validator. 
    If you have real parameter constraints, you can implement them here.
    """
    DEFAULT_RANGES = {
        'MovingAverageCrossover': {
            'short_window': {'min': 5, 'max': 15, 'step': 1},
            'long_window': {'min': 10, 'max': 20, 'step': 1}
        },
        'RSIStrategy': {
            'rsi_period': {'min': 5, 'max': 30, 'step': 5},
            'oversold': {'min': 20, 'max': 40, 'step': 5},
            'overbought': {'min': 60, 'max': 80, 'step': 5}
        },
        'MACDStrategy': {
            'fast_period': {'min': 12, 'max': 16, 'step': 1},
            'slow_period': {'min': 26, 'max': 30, 'step': 1},
            'signal_period': {'min': 9, 'max': 12, 'step': 1}
        },
        'BollingerBandsStrategy': {
            'window': {'min': 20, 'max': 30, 'step': 5},
            'num_std': {'min': 2, 'max': 3, 'step': 0.5}
        }
    }
       
    @staticmethod
    def validate_parameters(strategy_name: str, params: Dict[str, Any]) -> bool:
        if strategy_name not in ParameterValidator.DEFAULT_RANGES:
            logging.warning(f"No validation rules for strategy: {strategy_name}")
            return True
            
        ranges = ParameterValidator.DEFAULT_RANGES[strategy_name]
        for param, value in params.items():
            if param in ranges:
                if value < ranges[param]['min'] or value > ranges[param]['max']:
                    raise ValueError(
                        f"Parameter {param} value {value} outside valid range "
                        f"({ranges[param]['min']}-{ranges[param]['max']})"
                    )
        return True

    @staticmethod
    def generate_grid_parameters(strategy_name: str) -> Dict[str, List[float]]:
        if strategy_name not in ParameterValidator.DEFAULT_RANGES:
            raise ValueError(f"No grid search parameters defined for {strategy_name}")
            
        ranges = ParameterValidator.DEFAULT_RANGES[strategy_name]
        grid_params = {}
        
        for param, range_info in ranges.items():
            values = list(range(
                range_info['min'],
                range_info['max'] + range_info['step'],
                range_info['step']
            ))
            grid_params[param] = values
            
        return grid_params

class StrategyManager:
    """
    Manages strategies, each of which can be in 'live' or 'backtest' mode,
    and validates their parameters. Also persists modes in a local DB so that
    if the server restarts, the 'live' ones can be auto-started again.
    """

    def __init__(self):
        self.logger = logger
        self.strategies = {}   # e.g. { name: { 'mode':..., 'params':..., 'timeframe':...}, ...}
        self.live_managers = {}  # { strategy_name: LiveTradingManager instance }
        self.parameter_validator = ParameterValidator()  # if you have one

        # Optional: we store reference to DB path
        self.db_path = config.get('DEFAULT', 'database_path', fallback='data/strategies.db')
        # For the 'strategies' table, we can store mode in it
        self._init_db()
        self._load_strategies_from_db()

        # Auto-start any that are 'live'
        self._auto_start_live_strategies()


    def _init_db(self):
        """
        Creates or updates the 'strategies' table that holds each strategy's name + mode.
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        # Possibly add columns if not present
        cur.execute('''
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            mode TEXT DEFAULT 'backtest' CHECK (mode IN ('live','backtest')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            params TEXT DEFAULT '{}',
            timeframe TEXT DEFAULT '1Min'
        )
        ''')
        conn.commit()
        conn.close()

    def _load_strategies_from_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        rows = cur.execute("""
            SELECT name, mode, params, timeframe
            FROM strategies
        """).fetchall()
        conn.close()

        for (name, mode, params_str, timeframe) in rows:
            try:
                params_dict = json.loads(params_str) if params_str else {}
            except:
                params_dict = {}
            self.strategies[name] = {
                'mode': mode,
                'params': params_dict,
                'timeframe': timeframe or '1Min'
            }

        self.logger.info(f"Loaded {len(self.strategies)} strategies from DB.")

    def _auto_start_live_strategies(self):
        """
        For any strategy in self.strategies that has mode='live', start it automatically 
        so that if server restarts, they remain live.
        """
        for strat_name, strat_info in self.strategies.items():
            if strat_info['mode'] == 'live':
                self._run_live_pipeline(strat_name)

    def _run_live_pipeline(self, strat_name: str):
        """
        Start or ensure we have a live manager for the given strategy
        """
        if strat_name in self.live_managers:
            self.logger.info(f"Strategy {strat_name} is already running in live mode.")
            return
        # Otherwise create a LiveTradingManager
        self.logger.info(f"Starting live trading manager for {strat_name}.")
        manager = LiveTradingManager(strat_name=strat_name)
        manager.start(force_live=True) # manager.start()
        self.live_managers[strat_name] = manager

    def _stop_live_pipeline(self, strat_name: str):
        """
        Stop the live manager if it exists
        """
        if strat_name in self.live_managers:
            self.logger.info(f"Stopping live manager for {strat_name}.")
            self.live_managers[strat_name].stop()
            del self.live_managers[strat_name]

    def change_strategy_mode(self, strat_name, new_mode, params: Dict[str, Any] = None):
        """
        Change a strategy's mode ('live' or 'backtest') and optionally update its parameters
        (allocation, stop_loss, take_profit, tickers, timeframe) in the DB.

        If new_mode='live', we auto-start that pipeline. If 'backtest', stop the pipeline.
        """
        if new_mode not in ['live', 'backtest']:
            new_mode = 'backtest'

        if params is None:
            params = {}

        # If not present, create an entry in self.strategies or in DB
        if strat_name not in self.strategies:
            self.strategies[strat_name] = {'mode': 'backtest', 'params': {}}
            self._insert_new_strategy(strat_name, new_mode, params)
        else:
            # Just update the DB record
            self._update_strategy_mode_db(strat_name, new_mode, params)

        old_mode = self.strategies[strat_name]['mode']
        self.strategies[strat_name]['mode'] = new_mode
        self.strategies[strat_name]['params'] = params

        # If switching from live -> backtest, stop manager
        if old_mode == 'live' and new_mode == 'backtest':
            self._stop_live_pipeline(strat_name)
        # If switching from backtest -> live, run live
        elif old_mode != 'live' and new_mode == 'live':
            self._run_live_pipeline(strat_name)

        self.logger.info(f"Strategy {strat_name} changed from {old_mode} to {new_mode} in DB & memory.")
        return True


    def _insert_new_strategy(self, strat_name: str, new_mode: str, params: Dict[str, Any]):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO strategies (name, mode, params)
            VALUES (?, ?, ?)
        ''', (strat_name, new_mode, json.dumps(params)))
        conn.commit()
        conn.close()

    def _update_strategy_mode_db(self, strat_name: str, new_mode: str, params: Dict[str, Any]):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            UPDATE strategies
               SET mode = ?,
                   params = ?
             WHERE name = ?
        ''', (new_mode, json.dumps(params), strat_name))
        conn.commit()
        conn.close()