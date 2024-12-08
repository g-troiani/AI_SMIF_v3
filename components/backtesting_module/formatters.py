# components/backtesting_module/formatters.py

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
            'Sharpe Ratio': f"{metrics['Sharpe Ratio']:.2f}",
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
            formatted_results.append({
                'Parameters': result['params'],
                'Sharpe Ratio': f"{result['sharpe_ratio']:.2f}",
                'Total Return': f"{result['total_return']*100:.2f}%",
                'Max Drawdown': f"{result['max_drawdown']:.2f}%"
            })
        return formatted_results