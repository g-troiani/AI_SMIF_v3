# components/backtesting_module/utils.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def validate_backtest_data(data):
    """
    Validates that data meets minimum requirements for backtesting.
    """
    if data is None or len(data) < BacktestConfig.MIN_DATA_POINTS:
        raise DataError(f"Insufficient data points. Minimum required: {BacktestConfig.MIN_DATA_POINTS}")
    
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        raise DataError(f"Missing required columns: {missing_columns}")

def calculate_statistics(returns):
    """
    Calculates additional performance statistics.
    """
    stats = {
        'total_return': (returns + 1).prod() - 1,
        'annual_return': (returns + 1).prod() ** (252/len(returns)) - 1,
        'volatility': returns.std() * np.sqrt(252),
        'max_drawdown': calculate_max_drawdown(returns),
        'win_rate': (returns > 0).mean()
    }
    return stats

def calculate_max_drawdown(returns):
    """
    Calculates maximum drawdown from returns series.
    """
    cum_returns = (1 + returns).cumprod()
    rolling_max = cum_returns.expanding(min_periods=1).max()
    drawdowns = cum_returns/rolling_max - 1
    return drawdowns.min()