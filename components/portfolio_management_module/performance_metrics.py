# components/portfolio_management_module/performance_metrics.py

import math

def calculate_total_return(initial_value, current_value):
    """Calculate total return as a percentage."""
    if initial_value == 0:
        return 0.0
    return (current_value - initial_value) / initial_value * 100.0

def calculate_daily_returns(value_history):
    """Calculate daily returns from a history of values."""
    daily_returns = []
    for i in range(1, len(value_history)):
        if value_history[i-1] != 0:
            daily_return = (value_history[i] - value_history[i-1]) / value_history[i-1]
        else:
            daily_return = 0.0
        daily_returns.append(daily_return)
    return daily_returns

def calculate_sharpe_ratio(daily_returns, risk_free_rate=0.0):
    """Calculate the Sharpe Ratio based on daily returns."""
    if not daily_returns:
        return 0.0
    mean_return = sum(daily_returns) / len(daily_returns)
    if len(daily_returns) > 1:
        return_std = math.sqrt(sum((r - mean_return) ** 2 for r in daily_returns) / (len(daily_returns) - 1))
    else:
        return_std = 0.0
    if return_std == 0.0:
        return 0.0
    # Sharpe ratio annualized approximation (assuming ~252 trading days)
    sharpe_ratio = (mean_return - risk_free_rate) / return_std * math.sqrt(252)
    return sharpe_ratio

def calculate_max_drawdown(value_history):
    """Calculate the maximum drawdown from a history of portfolio values."""
    if not value_history:
        return 0.0
    peak = value_history[0]
    max_drawdown = 0.0
    for value in value_history:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak if peak != 0 else 0.0
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    return max_drawdown * 100
