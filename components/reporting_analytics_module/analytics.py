# components/reporting_analytics_module/analytics.py

import math

def compute_alpha(portfolio_return, benchmark_return):
    """Compute alpha as difference between portfolio return and benchmark return."""
    return portfolio_return - benchmark_return

def compute_beta(daily_returns, benchmark_daily_returns):
    """Compute the beta of the portfolio relative to a benchmark.
    For MVP, assume daily_returns and benchmark_daily_returns are aligned lists.
    """
    if len(daily_returns) != len(benchmark_daily_returns) or len(daily_returns) == 0:
        return 0.0
    covariance = 0.0
    benchmark_variance = 0.0
    mean_portfolio = sum(daily_returns)/len(daily_returns)
    mean_benchmark = sum(benchmark_daily_returns)/len(benchmark_daily_returns)
    for i in range(len(daily_returns)):
        covariance += (daily_returns[i] - mean_portfolio)*(benchmark_daily_returns[i] - mean_benchmark)
        benchmark_variance += (benchmark_daily_returns[i] - mean_benchmark)**2
    if benchmark_variance == 0:
        return 0.0
    return covariance / benchmark_variance

def compute_sharpe_ratio(returns, risk_free_rate=0.0):
    """Compute the Sharpe ratio given a series of returns."""
    if not returns:
        return 0.0
    avg_return = sum(returns) / len(returns)
    std_deviation = math.sqrt(sum((r - avg_return)**2 for r in returns) / len(returns))
    if std_deviation == 0:
        return 0.0
    # Assuming daily returns and ~252 trading days in a year
    annualized_return = avg_return * 252
    annualized_std_deviation = std_deviation * math.sqrt(252)
    return (annualized_return - risk_free_rate) / annualized_std_deviation

def compute_sortino_ratio(returns, risk_free_rate=0.0):
    """Compute the Sortino ratio given a series of returns."""
    if not returns:
        return 0.0
    avg_return = sum(returns) / len(returns)
    negative_returns = [r for r in returns if r < 0]
    if not negative_returns:
        return float('inf')
    downside_deviation = math.sqrt(sum(r**2 for r in negative_returns) / len(negative_returns))
    if downside_deviation == 0:
        return float('inf')
    # Assuming daily returns and ~252 trading days in a year
    annualized_return = avg_return * 252
    annualized_downside_deviation = downside_deviation * math.sqrt(252)
    return (annualized_return - risk_free_rate) / annualized_downside_deviation
