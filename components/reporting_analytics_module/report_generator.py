# components/reporting_analytics_module/report_generator.py

import os
from datetime import datetime
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from .config import REPORT_DIRECTORY, DEFAULT_REPORT_FORMAT
from .analytics import compute_alpha, compute_beta, compute_sharpe_ratio, compute_sortino_ratio
from components.utils.exceptions import ReportGenerationError

class ReportGenerator:
    def __init__(self, portfolio_manager, data_manager):
        self.portfolio_manager = portfolio_manager
        self.data_manager = data_manager
        self.template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        if not os.path.exists(REPORT_DIRECTORY):
            os.makedirs(REPORT_DIRECTORY)

    def generate_strategy_report(self, strategy_id, start_date=None, end_date=None):
        """Generate strategy performance report"""
        try:
            # Get data
            metrics = self.portfolio_manager.get_strategy_metrics(strategy_id)
            if metrics is None:
                metrics = {}  # Ensure metrics is a dictionary
            trades = self._get_strategy_trades(strategy_id)
            risk_metrics = self._compute_risk_metrics(strategy_id)

            # Prepare performance metrics
            performance_metrics = [
                {'label': 'Total Return', 'value': f'{metrics.get("total_return", 0):.2f}', 'unit': '%'},
                {'label': 'Max Drawdown', 'value': f'{metrics.get("max_drawdown", 0):.2f}', 'unit': '%'}
            ]
            # Prepare risk metrics
            risk_metrics_list = []
            if risk_metrics:
                risk_metrics_list = [
                    {'label': 'Alpha', 'value': f'{risk_metrics.get("alpha", 0):.2f}'},
                    {'label': 'Beta', 'value': f'{risk_metrics.get("beta", 0):.2f}'},
                    {'label': 'Sharpe Ratio', 'value': f'{risk_metrics.get("sharpe_ratio", 0):.2f}'},
                    {'label': 'Sortino Ratio', 'value': f'{risk_metrics.get("sortino_ratio", 0):.2f}'}
                ]

            # Prepare template data
            template_data = {
                'title': f'Strategy Performance Report - {strategy_id}',
                'metrics': metrics,
                'performance_metrics': performance_metrics,
                'risk_metrics': risk_metrics_list,
                'trades': trades,
                'alpha': risk_metrics.get('alpha', 0),
                'beta': risk_metrics.get('beta', 0)
            }

            # Generate report
            template = self.env.get_template('report_template.html')
            report_content = template.render(**template_data)

            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = os.path.join(REPORT_DIRECTORY, f"strategy_{strategy_id}_report_{timestamp}.html")
            with open(report_path, 'w') as f:
                f.write(report_content)

            return report_path

        except Exception as e:
            raise ReportGenerationError(f"Error generating report: {str(e)}")

    def generate_portfolio_report(self):
        """Generate portfolio performance report"""
        try:
            metrics = self.portfolio_manager.get_portfolio_metrics()
            if metrics is None:
                metrics = {}
            strategy_summaries = self._get_strategy_summaries()
            risk_metrics = self._compute_portfolio_risk_metrics()

            performance_metrics = [
                {'label': 'Total Return', 'value': f'{metrics.get("total_return", 0):.2f}', 'unit': '%'},
                {'label': 'Max Drawdown', 'value': f'{metrics.get("max_drawdown", 0):.2f}', 'unit': '%'}
            ]
            risk_metrics_list = []
            if risk_metrics:
                risk_metrics_list = [
                    {'label': 'Alpha', 'value': f'{risk_metrics.get("alpha", 0):.2f}'},
                    {'label': 'Beta', 'value': f'{risk_metrics.get("beta", 0):.2f}'},
                    {'label': 'Sharpe Ratio', 'value': f'{risk_metrics.get("sharpe_ratio", 0):.2f}'},
                    {'label': 'Sortino Ratio', 'value': f'{risk_metrics.get("sortino_ratio", 0):.2f}'}
                ]

            # Prepare template data
            template_data = {
                'title': 'Portfolio Performance Report',
                'metrics': metrics,
                'performance_metrics': performance_metrics,
                'risk_metrics': risk_metrics_list,
                'strategies': strategy_summaries,
                'trades': None,  # Add trades as None to prevent UndefinedError
                'alpha': risk_metrics.get('alpha', 0),
                'beta': risk_metrics.get('beta', 0)
            }

            # Generate report
            template = self.env.get_template('report_template.html')
            report_content = template.render(**template_data)

            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = os.path.join(REPORT_DIRECTORY, f"portfolio_report_{timestamp}.html")
            with open(report_path, 'w') as f:
                f.write(report_content)

            return report_path

        except Exception as e:
            raise ReportGenerationError(f"Error generating portfolio report: {str(e)}")

    def _get_strategy_trades(self, strategy_id):
        """Get formatted trade history"""
        trades = self.portfolio_manager.get_strategy_trades(strategy_id)
        return pd.DataFrame(trades) if trades else pd.DataFrame()

    def _compute_risk_metrics(self, strategy_id):
        """Compute risk metrics for a strategy"""
        values = self.portfolio_manager.strategy_value_history.get(strategy_id, [])
        daily_returns = self._compute_daily_returns(values)
        if not daily_returns:
            return {}
        benchmark_data = self.data_manager.get_benchmark_data(len(daily_returns))
        if not isinstance(benchmark_data, dict) or 'returns' not in benchmark_data:
            benchmark_data = {'returns': [0]*len(daily_returns)}

        alpha = compute_alpha(sum(daily_returns), sum(benchmark_data['returns']))
        beta = compute_beta(daily_returns, benchmark_data['returns'])
        sharpe = compute_sharpe_ratio(daily_returns)
        sortino = compute_sortino_ratio(daily_returns)
        return {
            'alpha': alpha,
            'beta': beta,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino
        }

    def _compute_portfolio_risk_metrics(self):
        """Compute risk metrics for the entire portfolio"""
        # Combine values from all strategies
        all_values = []
        for values in self.portfolio_manager.strategy_value_history.values():
            if not all_values:
                all_values = values[:]
            else:
                all_values = [sum(x) for x in zip(all_values, values)]
        daily_returns = self._compute_daily_returns(all_values)
        if not daily_returns:
            return {}
        benchmark_data = self.data_manager.get_benchmark_data(len(daily_returns))
        if not isinstance(benchmark_data, dict) or 'returns' not in benchmark_data:
            benchmark_data = {'returns': [0]*len(daily_returns)}

        alpha = compute_alpha(sum(daily_returns), sum(benchmark_data['returns']))
        beta = compute_beta(daily_returns, benchmark_data['returns'])
        sharpe = compute_sharpe_ratio(daily_returns)
        sortino = compute_sortino_ratio(daily_returns)
        return {
            'alpha': alpha,
            'beta': beta,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino
        }

    def _get_strategy_summaries(self):
        """Get summary metrics for all strategies"""
        summaries = []
        for strategy_id in self.portfolio_manager.strategy_allocations.keys():
            metrics = self.portfolio_manager.get_strategy_metrics(strategy_id)
            if metrics is None:
                metrics = {}
            allocation = self.portfolio_manager.get_strategy_allocation(strategy_id)
            total_capital = self.portfolio_manager.get_total_capital()
            if total_capital == 0:
                allocation_percent = 0
            else:
                allocation_percent = (allocation / total_capital) * 100

            summaries.append({
                'id': strategy_id,
                'return': metrics.get('total_return', 0),
                'allocation': allocation_percent
            })
        return summaries

    @staticmethod
    def _compute_daily_returns(values):
        """Compute daily returns from value history"""
        if len(values) < 2:
            return []
        returns = []
        for i in range(1, len(values)):
            if values[i-1] != 0:
                returns.append((values[i] - values[i-1]) / values[i-1])
            else:
                returns.append(0)
        return returns
