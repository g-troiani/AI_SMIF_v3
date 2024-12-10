# tests/test_reporting_analytics_module.py

import unittest
import os
import sys
from unittest.mock import Mock
from datetime import datetime

# Add parent directory to Python path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.reporting_analytics_module.analytics import (
    compute_alpha, compute_beta, compute_sharpe_ratio, compute_sortino_ratio
)
from components.reporting_analytics_module.report_generator import ReportGenerator

class TestReportingAnalytics(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_portfolio_manager = Mock()
        self.mock_data_manager = Mock()

        # Set up common test data
        self.test_strategy_id = 'test_strategy'
        self.test_daily_values = [1000, 1020, 990, 1015, 1040]  # Example daily portfolio values
        self.test_trades = [
            {'timestamp': '2024-01-01', 'ticker': 'AAPL', 'action': 'BUY', 'quantity': 100, 'price': 150},
            {'timestamp': '2024-01-02', 'ticker': 'AAPL', 'action': 'SELL', 'quantity': 50, 'price': 155},
        ]

        # Configure mock portfolio manager
        self.mock_portfolio_manager.get_strategy_metrics.return_value = {
            'total_return': 15.5,
            'max_drawdown': 8.3,
            'sharpe_ratio': 1.2
        }
        self.mock_portfolio_manager.get_portfolio_metrics.return_value = {
            'total_return': 20.5,
            'max_drawdown': 12.3
        }
        self.mock_portfolio_manager.get_strategy_trades.return_value = self.test_trades
        self.mock_portfolio_manager.strategy_value_history = {
            self.test_strategy_id: self.test_daily_values
        }
        self.mock_portfolio_manager.strategy_allocations = {
            'strategy1': 5000,
            'strategy2': 5000
        }
        self.mock_portfolio_manager.get_strategy_allocation.return_value = 5000
        self.mock_portfolio_manager.get_total_capital.return_value = 10000

        # Configure mock data manager
        self.mock_data_manager.get_benchmark_data.return_value = {
            'prices': [100, 101, 99, 102, 103],
            'returns': [0.01, -0.0198, 0.0303, 0.0098]
        }

        # Create report generator instance
        self.report_generator = ReportGenerator(self.mock_portfolio_manager, self.mock_data_manager)

    def test_analytics_calculations(self):
        """Test core analytics calculations."""
        # Test alpha calculation
        portfolio_return = 0.15
        benchmark_return = 0.10
        expected_alpha = 0.05
        self.assertAlmostEqual(
            compute_alpha(portfolio_return, benchmark_return),
            expected_alpha,
            places=2,
            msg="Alpha calculation failed"
        )

        # Test beta calculation
        portfolio_returns = [0.01, 0.02, -0.01, 0.015]
        benchmark_returns = [0.005, 0.015, -0.005, 0.01]
        beta = compute_beta(portfolio_returns, benchmark_returns)
        self.assertTrue(
            0 <= beta <= 2,
            msg="Beta calculation produced unrealistic value"
        )

        # Test Sharpe ratio
        returns = [0.01, 0.02, -0.01, 0.015]
        sharpe = compute_sharpe_ratio(returns)
        self.assertTrue(
            isinstance(sharpe, float),
            msg="Sharpe ratio calculation failed"
        )

        # Test Sortino ratio
        sortino = compute_sortino_ratio(returns)
        self.assertTrue(
            isinstance(sortino, float),
            msg="Sortino ratio calculation failed"
        )

    def test_report_generation_strategy(self):
        """Test strategy report generation."""
        # Generate report
        try:
            report_path = self.report_generator.generate_strategy_report(self.test_strategy_id)

            # Verify report was created
            self.assertTrue(
                os.path.exists(report_path),
                msg="Strategy report file not created"
            )

            # Verify report content
            with open(report_path, 'r') as f:
                content = f.read()
                self.assertIn(self.test_strategy_id, content)
                self.assertIn("15.50%", content)  # Total return (updated)
                self.assertIn("8.30%", content)   # Max drawdown (updated)

            # Clean up
            os.remove(report_path)

        except Exception as e:
            self.fail(f"Report generation failed with error: {str(e)}")

    def test_report_generation_portfolio(self):
        """Test portfolio report generation."""
        # Generate report
        try:
            report_path = self.report_generator.generate_portfolio_report()

            # Verify report was created
            self.assertTrue(
                os.path.exists(report_path),
                msg="Portfolio report file not created"
            )

            # Verify report content
            with open(report_path, 'r') as f:
                content = f.read()
                self.assertIn("Portfolio Performance Report", content)
                self.assertIn("20.50%", content)  # Total return (updated)
                self.assertIn("12.30%", content)  # Max drawdown (updated)

            # Clean up
            os.remove(report_path)

        except Exception as e:
            self.fail(f"Portfolio report generation failed with error: {str(e)}")

    def test_report_data_validation(self):
        """Test report generation with invalid data."""
        # Test with empty data
        self.mock_portfolio_manager.get_strategy_metrics.return_value = {}
        self.mock_portfolio_manager.get_strategy_trades.return_value = []

        # Should handle empty data gracefully
        try:
            report_path = self.report_generator.generate_strategy_report(self.test_strategy_id)
            self.assertTrue(
                os.path.exists(report_path),
                msg="Report should be generated even with empty data"
            )
            os.remove(report_path)
        except Exception as e:
            self.fail(f"Report generation with empty data failed: {str(e)}")

        # Test with None values
        self.mock_portfolio_manager.get_strategy_metrics.return_value = None
        try:
            report_path = self.report_generator.generate_strategy_report(self.test_strategy_id)
            self.assertTrue(
                os.path.exists(report_path),
                msg="Report should handle None values gracefully"
            )
            os.remove(report_path)
        except Exception as e:
            self.fail(f"Report generation with None values failed: {str(e)}")

    def test_report_formats(self):
        """Test report formatting and styling."""
        report_path = self.report_generator.generate_strategy_report(self.test_strategy_id)

        # Verify HTML structure
        with open(report_path, 'r') as f:
            content = f.read()
            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("<html>", content)
            self.assertIn("<head>", content)
            self.assertIn("<body>", content)
            self.assertIn("</html>", content)

        # Clean up
        os.remove(report_path)

    def test_risk_metrics_calculation(self):
        """Test calculation of risk metrics in reports."""
        # Set up test data
        returns = [0.01, 0.02, -0.015, 0.025, -0.01]
        benchmark_returns = [0.005, 0.015, -0.01, 0.02, -0.005]

        # Test beta calculation with known data
        beta = compute_beta(returns, benchmark_returns)
        self.assertTrue(
            isinstance(beta, float),
            msg="Beta calculation should return float"
        )

        # Test Sharpe ratio with known data
        sharpe = compute_sharpe_ratio(returns)
        self.assertTrue(
            isinstance(sharpe, float),
            msg="Sharpe ratio calculation should return float"
        )

        # Test alpha calculation with known data
        portfolio_return = sum(returns)
        benchmark_return = sum(benchmark_returns)
        alpha = compute_alpha(portfolio_return, benchmark_return)
        self.assertTrue(
            isinstance(alpha, float),
            msg="Alpha calculation should return float"
        )

if __name__ == '__main__':
    unittest.main()
