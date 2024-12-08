# tests/test_risk_management_module.py

# tests/test_risk_management_module.py

import unittest
import os
import sys
from unittest.mock import Mock, patch
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
        f.write("[RISK]\nDEFAULT_STOP_LOSS_PERCENT=10\nDEFAULT_TAKE_PROFIT_PERCENT=20\nMAX_DRAW_DOWN_PERCENT=20\n")

from components.risk_management_module.risk_manager import RiskManager
from components.risk_management_module.stop_loss_handler import StopLossHandler
from components.risk_management_module.emergency_liquidation import EmergencyLiquidation

class TestRiskManagement(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create mocks for dependencies
        self.mock_portfolio_manager = Mock()
        self.mock_trading_engine = Mock()
        self.mock_data_manager = Mock()
        
        # Set up common portfolio state for testing
        self.mock_portfolio_manager.get_total_capital.return_value = 100000
        self.mock_portfolio_manager.get_current_holdings.return_value = {
            'strategy1': 50000,
            'strategy2': 50000
        }
        
        # Initialize risk manager with mocked dependencies
        self.risk_manager = RiskManager(self.mock_portfolio_manager, self.mock_trading_engine)
        self.risk_manager.data_manager = self.mock_data_manager

    def tearDown(self):
        """Clean up after each test."""
        # Reset all mocks
        self.mock_portfolio_manager.reset_mock()
        self.mock_trading_engine.reset_mock()
        self.mock_data_manager.reset_mock()
    
    def test_risk_config_defaults(self):
        """Test risk management configuration and defaults."""
        handler = StopLossHandler()
        self.assertEqual(handler.stop_loss_percent, 10)
        self.assertEqual(handler.take_profit_percent, 20)
        
        handler.set_stop_loss(15)
        handler.set_take_profit(25)
        self.assertEqual(handler.stop_loss_percent, 15)
        self.assertEqual(handler.take_profit_percent, 25)

    def test_strategy_risk_validation(self):
        """Test strategy validation against risk criteria."""
        good_performance = {
            'total_return': 15.0,
            'sharpe_ratio': 1.5,
            'max_drawdown': 12.0
        }
        self.assertTrue(self.risk_manager.validate_strategy('strategy1', good_performance))
        
        poor_returns = {
            'total_return': -5.0,
            'sharpe_ratio': 1.5,
            'max_drawdown': 12.0
        }
        self.assertFalse(self.risk_manager.validate_strategy('strategy2', poor_returns))
        
        high_risk = {
            'total_return': 15.0,
            'sharpe_ratio': 0.5,
            'max_drawdown': 12.0
        }
        self.assertFalse(self.risk_manager.validate_strategy('strategy3', high_risk))

    def test_position_risk_monitoring(self):
        """Test continuous risk monitoring of positions."""
        # Reset mock first
        self.mock_trading_engine.reset_mock()
        
        # Set up a single test position
        test_positions = {
            'strategy1': {'AAPL': 100}
        }
        self.mock_portfolio_manager.strategy_positions = test_positions
        
        # Test normal price (no trigger)
        self.mock_data_manager.get_current_price.return_value = 95  # 5% drop
        with patch.object(self.risk_manager, '_get_average_purchase_price') as mock_price:
            mock_price.return_value = 100
            self.risk_manager.monitor_positions()
            self.assertEqual(self.mock_trading_engine.place_order.call_count, 0)
        
        # Reset mocks
        self.mock_trading_engine.reset_mock()
        self.mock_data_manager.reset_mock()
        
        # Test stop-loss trigger
        self.mock_data_manager.get_current_price.return_value = 85  # 15% drop
        self.mock_portfolio_manager.strategy_positions = {'strategy1': {'AAPL': 100}}
        
        with patch.object(self.risk_manager, '_get_average_purchase_price') as mock_price:
            mock_price.return_value = 100
            self.risk_manager.monitor_positions()
            
            self.mock_trading_engine.place_order.assert_called_once_with(
                'strategy1', 'AAPL', 'SELL', 100
            )

    def test_risk_based_trade_control(self):
        """Test risk-based trade control and limitations."""
        self.risk_manager.approved_strategies['strategy1'] = True
        
        self.assertTrue(
            self.risk_manager.enforce_risk_controls_on_trades(
                'strategy1', 'AAPL', 'BUY', 100
            )
        )
        
        self.assertFalse(
            self.risk_manager.enforce_risk_controls_on_trades(
                'strategy2', 'AAPL', 'BUY', 100
            )
        )

    def test_emergency_risk_handling(self):
        """Test emergency risk handling procedures."""
        test_positions = {
            'strategy1': {'AAPL': 100, 'GOOGL': 50},
            'strategy2': {'MSFT': 200}
        }
        self.mock_portfolio_manager.strategy_positions = test_positions
        
        self.risk_manager.panic_button_pressed()
        
        self.assertEqual(self.mock_trading_engine.place_order.call_count, 3)
        order_calls = self.mock_trading_engine.place_order.call_args_list
        self.assertEqual(len(order_calls), 3)

    def test_market_condition_monitoring(self):
        """Test monitoring and response to market conditions."""
        self.mock_portfolio_manager.get_portfolio_metrics.return_value = {
            'max_drawdown': 15.0
        }
        self.risk_manager.handle_extreme_market_conditions()
        
        self.mock_portfolio_manager.get_portfolio_metrics.return_value = {
            'max_drawdown': 25.0
        }
        self.risk_manager.handle_extreme_market_conditions()

    def test_integrated_risk_management(self):
        """Test risk management integration with trading and portfolio components."""
        strategy_id = 'strategy1'
        self.risk_manager.approved_strategies[strategy_id] = True
        
        self.mock_portfolio_manager.strategy_positions = {
            strategy_id: {'AAPL': 100}
        }
        self.mock_portfolio_manager.get_strategy_allocation.return_value = 50000
        
        self.assertTrue(
            self.risk_manager.enforce_risk_controls_on_trades(
                strategy_id, 'AAPL', 'BUY', 50
            )
        )
        
        self.mock_trading_engine.reset_mock()
        self.mock_data_manager.get_current_price.return_value = 80
        with patch.object(self.risk_manager, '_get_average_purchase_price', return_value=100):
            self.risk_manager.monitor_positions()
            self.mock_trading_engine.place_order.assert_called_once()

if __name__ == '__main__':
    unittest.main()