# File: tests/test_strategy_management_module.py

import unittest
import sys
import os
import json
import pandas as pd
from datetime import datetime, timedelta
import tempfile

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from components.strategy_management_module.strategy_manager import StrategyManager
from components.strategy_management_module.strategies.moving_average_crossover import MovingAverageCrossoverStrategy
from components.strategy_management_module.strategies.rsi_strategy import RSIStrategy
from components.strategy_management_module.strategies.macd_strategy import MACDStrategy

class TestStrategyManagementModule(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        # Use temporary file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'test_strategies.json')
        self.manager = StrategyManager(config_file=self.config_file)
        
        # Create sample market data for testing signals
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        self.test_data = pd.DataFrame({
            'close': range(100),
            'open': range(100),
            'high': range(100),
            'low': range(100),
            'volume': [1000] * 100
        }, index=dates)

    def test_strategy_manager_initialization(self):
        """Test StrategyManager initialization."""
        self.assertIsInstance(self.manager, StrategyManager)
        self.assertEqual(self.manager.strategies, {})

    def test_add_valid_strategies(self):
        """Test adding valid strategies with correct parameters."""
        test_cases = [
            ('moving_average_crossover', {'short_window': 50, 'long_window': 200}),
            ('rsi_strategy', {'period': 14, 'overbought': 70, 'oversold': 30}),
            ('macd_strategy', {'fast_period': 12, 'slow_period': 26, 'signal_period': 9})
        ]

        for strategy_name, params in test_cases:
            with self.subTest(strategy=strategy_name):
                success = self.manager.add_strategy(strategy_name, params)
                self.assertTrue(success, f"Failed to add strategy: {strategy_name}")
                
                strategy = self.manager.get_strategy(strategy_name)
                self.assertIsNotNone(strategy, f"Strategy {strategy_name} was not properly added")
                self.assertEqual(strategy.params, params)

    def test_invalid_strategy_handling(self):
        """Test handling of invalid strategy additions."""
        test_cases = [
            ('non_existent_strategy', {}, ImportError),
            ('moving_average_crossover', {'short_window': -10, 'long_window': 100}, ValueError),
            ('rsi_strategy', {'period': 0, 'overbought': 70, 'oversold': 30}, ValueError),
        ]

        for strategy_name, params, expected_error in test_cases:
            with self.subTest(strategy=strategy_name):
                self.assertFalse(self.manager.add_strategy(strategy_name, params))

    def test_strategy_signal_generation(self):
        """Test signal generation for each strategy."""
        strategies = {
            'moving_average_crossover': {'short_window': 5, 'long_window': 10},
            'rsi_strategy': {'period': 14, 'overbought': 70, 'oversold': 30},
            'macd_strategy': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}
        }

        for strategy_name, params in strategies.items():
            with self.subTest(strategy=strategy_name):
                success = self.manager.add_strategy(strategy_name, params)
                self.assertTrue(success, f"Failed to add strategy: {strategy_name}")
                
                strategy = self.manager.get_strategy(strategy_name)
                self.assertIsNotNone(strategy, f"Strategy {strategy_name} was not properly added")
                
                signals = strategy.generate_signals(self.test_data)
                self.assertIsInstance(signals, pd.DataFrame)
                self.assertTrue('signal' in signals.columns)
                self.assertTrue('positions' in signals.columns)

    def test_strategy_persistence(self):
        """Test saving and loading of strategy configurations."""
        # Add a strategy
        params = {'short_window': 50, 'long_window': 200}
        self.manager.add_strategy('moving_average_crossover', params)
        
        # Create new manager instance to test loading
        new_manager = StrategyManager(config_file=self.config_file)
        
        # Verify strategy was loaded
        strategy = new_manager.get_strategy('moving_average_crossover')
        self.assertIsNotNone(strategy)
        self.assertEqual(strategy.params, params)

    def test_strategy_listing(self):
        """Test listing available strategies."""
        strategies = {
            'moving_average_crossover': {'short_window': 50, 'long_window': 200},
            'rsi_strategy': {'period': 14, 'overbought': 70, 'oversold': 30}
        }
        
        for name, params in strategies.items():
            success = self.manager.add_strategy(name, params)
            self.assertTrue(success, f"Failed to add strategy: {name}")
        
        available_strategies = self.manager.list_strategies()
        self.assertEqual(set(available_strategies), set(strategies.keys()))

    def test_remove_strategy(self):
        """Test removing a strategy."""
        strategy_name = 'moving_average_crossover'
        params = {'short_window': 50, 'long_window': 200}
        
        # Add and then remove strategy
        self.manager.add_strategy(strategy_name, params)
        self.assertTrue(self.manager.remove_strategy(strategy_name))
        
        # Verify strategy was removed
        self.assertIsNone(self.manager.get_strategy(strategy_name))

    def tearDown(self):
        """Clean up test environment after each test."""
        import shutil
        shutil.rmtree(self.temp_dir)

if __name__ == '__main__':
    unittest.main()