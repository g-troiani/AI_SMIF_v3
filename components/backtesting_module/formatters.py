# File: components/backtesting_module/formatters.py
# Type: py

class ResultFormatter:
    """
    Formats backtest results for consistent presentation.
    Now updated to handle old/new metric keys so the UI won't break 
    if metrics come from different tables or code versions.
    """
    
    @staticmethod
    def format_metrics(metrics: dict) -> dict:
        """
        Formats performance metrics with proper rounding and labels.
        We handle fallback keys so that if the dictionary has:
         - "Total Return" or "total_return"
         - "Sharpe Ratio" or "sharpe_ratio"
         - "Max Drawdown" or "max_drawdown"
         - "Final Portfolio Value" or "final_value"
        ...we won't break. The UI sees a consistent output.
        """
        def fallback_value(m: dict, old_key: str, new_key: str, default=0.0):
            """
            If old_key is present, return m[old_key].
            Else if new_key is present, return m[new_key].
            Else return default.
            """
            if old_key in m:
                return m[old_key]
            elif new_key in m:
                return m[new_key]
            else:
                return default

        # Retrieve each metric (some may be None or 0.0 if missing)
        total_ret = fallback_value(metrics, 'Total Return', 'total_return', 0.0)
        sharpe_val = fallback_value(metrics, 'Sharpe Ratio', 'sharpe_ratio', None)
        max_dd = fallback_value(metrics, 'Max Drawdown', 'max_drawdown', 0.0)
        final_val = fallback_value(metrics, 'Final Portfolio Value', 'final_value', 0.0)

        # Format them for display
        return {
            'Total Return': f"{total_ret * 100:.2f}%",
            'Sharpe Ratio': f"{sharpe_val:.2f}" if sharpe_val is not None else 'N/A',
            'Max Drawdown': f"{max_dd:.2f}%",
            'Final Value': f"${final_val:,.2f}"
        }
    
    @staticmethod
    def format_optimization_results(results: list) -> list:
        """
        Formats optimization results for display.
        Also includes fallback logic to handle potential 
        old/new keys (like 'total_return' vs 'Total Return', etc.).
        """
        formatted_results = []
        for result in results:
            # Sharpe ratio might be 'sharpe_ratio' or 'Sharpe Ratio'
            sr = result.get('sharpe_ratio', result.get('Sharpe Ratio', None))

            # total return might be 'total_return' or 'Total Return'
            tot_ret = result.get('total_return', result.get('Total Return', 0.0))

            # max drawdown might be 'max_drawdown' or 'Max Drawdown'
            max_dd = result.get('max_drawdown', result.get('Max Drawdown', 0.0))

            formatted_results.append({
                'Parameters': result.get('params', {}),
                'Sharpe Ratio': f"{sr:.2f}" if sr is not None else 'N/A',
                'Total Return': f"{tot_ret * 100:.2f}%",
                'Max Drawdown': f"{max_dd:.2f}%"
            })
        return formatted_results
