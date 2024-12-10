# File: components/backtesting_module/formatters.py
# Type: py

class ResultFormatter:
    """
    Formats backtest results for consistent presentation.
    """
    
    @staticmethod
    def format_metrics(metrics: dict) -> dict:
        """
        Formats performance metrics with proper rounding and labels.
        """
        return {
            'Total Return': f"{metrics['Total Return']*100:.2f}%",
            'Sharpe Ratio': f"{metrics['Sharpe Ratio']:.2f}" if metrics['Sharpe Ratio'] is not None else 'N/A',
            'Max Drawdown': f"{metrics['Max Drawdown']:.2f}%",
            'Final Value': f"${metrics['Final Portfolio Value']:,.2f}"
        }
    
    @staticmethod
    def format_optimization_results(results: list) -> list:
        """
        Formats optimization results for display.
        """
        formatted_results = []
        for result in results:
            sr = result['sharpe_ratio']
            formatted_results.append({
                'Parameters': result['params'],
                'Sharpe Ratio': f"{sr:.2f}" if sr is not None else 'N/A',
                'Total Return': f"{result['total_return']*100:.2f}%",
                'Max Drawdown': f"{result['max_drawdown']:.2f}%"
            })
        return formatted_results
