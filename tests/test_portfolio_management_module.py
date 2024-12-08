# tests/test_portfolio_management_module.py

import unittest
import os
import sys
from datetime import datetime

# Add parent directory to Python path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create default config directory and file if needed
config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
config_file = os.path.join(config_dir, 'config.ini')
if not os.path.exists(config_dir):
    os.makedirs(config_dir)
if not os.path.exists(config_file):
    with open(config_file, 'w') as f:
        f.write("[PORTFOLIO]\nDEFAULT_ALLOCATION_PER_STRATEGY=5000\n")

from components.portfolio_management_module.portfolio_manager import PortfolioManager

class TestPortfolioManagement(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.portfolio_manager = PortfolioManager()

    def test_initial_portfolio_state(self):
        """Test initial portfolio state and default values."""
        self.test_strategy_id = 'test_strategy'
        self.portfolio_manager.allocate_capital_to_strategies([self.test_strategy_id])
        
        self.assertEqual(len(self.portfolio_manager.strategy_allocations), 1)
        self.assertEqual(self.portfolio_manager.strategy_allocations[self.test_strategy_id], 5000)
        self.assertEqual(len(self.portfolio_manager.strategy_positions), 0)
        self.assertEqual(len(self.portfolio_manager.strategy_value_history), 0)
        self.assertEqual(len(self.portfolio_manager.strategy_metrics), 0)

    def test_strategy_allocation_edge_cases(self):
        """Test allocation behavior with edge cases."""
        # Reset portfolio manager to ensure clean state
        self.portfolio_manager = PortfolioManager()
        
        # Test empty strategy list
        allocations = self.portfolio_manager.allocate_capital_to_strategies([])
        self.assertEqual(len(allocations), 0)

        # Test single strategy
        allocations = self.portfolio_manager.allocate_capital_to_strategies(['strategy1'])
        self.assertEqual(allocations['strategy1'], 5000)

        # Test maximum strategies (assuming 100k total capital and 5k per strategy)
        max_strategies = [f'strategy{i}' for i in range(20)]
        allocations = self.portfolio_manager.allocate_capital_to_strategies(max_strategies)
        self.assertEqual(len(allocations), 20)
        self.assertLessEqual(sum(allocations.values()), 100000)

        # Test allocation adjustment with too many strategies
        many_strategies = [f'strategy{i}' for i in range(30)]
        allocations = self.portfolio_manager.allocate_capital_to_strategies(many_strategies)
        self.assertLess(allocations['strategy0'], 5000)  # Should be adjusted down
        self.assertAlmostEqual(sum(allocations.values()), 100000, places=2)

    def test_trade_lifecycle_comprehensive(self):
        """Test complete trade lifecycle with multiple trades."""
        # Reset portfolio manager
        self.portfolio_manager = PortfolioManager()
        
        strategy_id = 'strategy1'
        self.portfolio_manager.allocate_capital_to_strategies([strategy_id])
        
        # Test basic trade sequence
        trades = [
            {'ticker': 'AAPL', 'action': 'BUY', 'quantity': 10, 'price': 150},
            {'ticker': 'MSFT', 'action': 'BUY', 'quantity': 5, 'price': 200},
            {'ticker': 'AAPL', 'action': 'SELL', 'quantity': 5, 'price': 160},
        ]

        expected_capital = 5000  # Initial allocation
        positions = {}

        for trade in trades:
            # Calculate position change
            position_change = trade['quantity']
            if trade['action'] == 'SELL':
                position_change = -position_change

            # Calculate trade value and update expected capital
            trade_value = trade['price'] * trade['quantity']
            if trade['action'] == 'BUY':
                if trade_value > expected_capital:
                    continue  # Skip trade if not enough capital
                expected_capital -= trade_value
            else:
                expected_capital += trade_value

            # Execute trade
            self.portfolio_manager.update_allocation_after_trade(
                strategy_id,
                trade['action'],
                trade['price'],
                trade['quantity']
            )

            self.portfolio_manager.record_trade(
                strategy_id,
                trade['ticker'],
                position_change,
                trade['price']
            )

            # Update and verify positions
            if trade['ticker'] not in positions:
                positions[trade['ticker']] = 0
            positions[trade['ticker']] += position_change

            actual_positions = self.portfolio_manager.get_total_exposure()
            for ticker, qty in positions.items():
                if qty == 0:
                    self.assertNotIn(ticker, actual_positions)
                else:
                    self.assertEqual(actual_positions.get(ticker), qty)

            # Verify allocation
            actual_allocation = self.portfolio_manager.get_strategy_allocation(strategy_id)
            self.assertAlmostEqual(
                actual_allocation,
                expected_capital,
                places=2,
                msg=f"Capital mismatch after {trade['action']} {trade['quantity']} {trade['ticker']}"
            )

    def test_performance_metrics_detailed(self):
        """Test performance calculations with various scenarios."""
        strategy_id = 'strategy1'

        scenarios = [
            {
                'name': 'Steady growth',
                'values': [1000, 1100, 1200, 1300],
                'expected_return': 30.0,
                'expected_drawdown': 0.0
            },
            {
                'name': 'Volatile growth',
                'values': [1000, 1200, 1100, 1300],
                'expected_return': 30.0,
                'expected_drawdown': 8.33
            },
            {
                'name': 'Decline',
                'values': [1000, 950, 900, 850],
                'expected_return': -15.0,
                'expected_drawdown': 15.0
            }
        ]

        for scenario in scenarios:
            self.portfolio_manager.strategy_value_history = {}
            
            for value in scenario['values']:
                self.portfolio_manager.update_strategy_value(strategy_id, value)
            
            self.portfolio_manager.calculate_strategy_performance(strategy_id)
            metrics = self.portfolio_manager.get_strategy_metrics(strategy_id)
            
            self.assertAlmostEqual(
                metrics['total_return'],
                scenario['expected_return'],
                places=1,
                msg=f"Total return failed for {scenario['name']}"
            )
            self.assertAlmostEqual(
                metrics['max_drawdown'],
                scenario['expected_drawdown'],
                places=1,
                msg=f"Max drawdown failed for {scenario['name']}"
            )
            self.assertIsInstance(
                metrics['sharpe_ratio'],
                float,
                msg=f"Sharpe ratio not calculated for {scenario['name']}"
            )

    def test_order_quantity_calculation(self):
        """Test order quantity calculations with various scenarios."""
        strategy_id = 'strategy1'
        self.portfolio_manager.allocate_capital_to_strategies([strategy_id])

        test_cases = [
            {
                'price': 100,
                'direction': 'BUY',
                'existing': 0,
                'expected': 50,
                'description': 'Normal buy'
            },
            {
                'price': 0,
                'direction': 'BUY',
                'existing': 0,
                'expected': 0,
                'description': 'Zero price'
            },
            {
                'price': 6000,
                'direction': 'BUY',
                'existing': 0,
                'expected': 0,
                'description': 'Price exceeds allocation'
            },
            {
                'price': 100,
                'direction': 'SELL',
                'existing': 10,
                'expected': 10,
                'description': 'Normal sell'
            },
            {
                'price': 100,
                'direction': 'INVALID',
                'existing': 0,
                'expected': 0,
                'description': 'Invalid direction'
            }
        ]

        for case in test_cases:
            quantity = self.portfolio_manager.calculate_order_quantity(
                strategy_id,
                case['price'],
                case['direction'],
                case['existing']
            )
            self.assertEqual(
                quantity,
                case['expected'],
                f"Failed for case: {case['description']}"
            )

    def test_risk_metrics_and_alerts(self):
        """Test risk metrics and alert generation for various scenarios."""
        strategy_id = 'strategy1'

        risk_scenarios = [
            {
                'name': 'Low risk',
                'values': [1000, 990, 1010],
                'expected_alerts': 0
            },
            {
                'name': 'Medium drawdown',
                'values': [1000, 900, 850],
                'expected_alerts': 0
            },
            {
                'name': 'Severe drawdown',
                'values': [1000, 750, 700],
                'expected_alerts': 1
            }
        ]

        for scenario in risk_scenarios:
            self.portfolio_manager.strategy_value_history = {}
            for value in scenario['values']:
                self.portfolio_manager.update_strategy_value(strategy_id, value)
            
            alerts = self.portfolio_manager.check_portfolio_for_alerts()
            drawdown_alerts = [a for a in alerts if 'drawdown' in a.lower()]
            
            self.assertEqual(
                len(drawdown_alerts),
                scenario['expected_alerts'],
                f"Alert check failed for {scenario['name']}"
            )

    def test_portfolio_level_calculations(self):
        """Test calculations across multiple strategies."""
        strategies = ['strategy1', 'strategy2']
        self.portfolio_manager.allocate_capital_to_strategies(strategies)

        values = {
            'strategy1': [1000, 1100, 1200],  # +20%
            'strategy2': [1000, 950, 1100]    # +10%
        }

        for strategy_id, strategy_values in values.items():
            for value in strategy_values:
                self.portfolio_manager.update_strategy_value(strategy_id, value)

        portfolio_metrics = self.portfolio_manager.get_portfolio_metrics()

        self.assertIsNotNone(portfolio_metrics)
        expected_return = ((2300 - 2000) / 2000) * 100  # 15% combined return
        self.assertAlmostEqual(portfolio_metrics['total_return'], expected_return, places=1)
        
        required_metrics = ['total_return', 'sharpe_ratio', 'max_drawdown']
        for metric in required_metrics:
            self.assertIn(metric, portfolio_metrics)

if __name__ == '__main__':
    unittest.main()