# components/backtesting_module/exceptions.py

class BacktestError(Exception):
    """Base exception for backtesting errors"""
    pass

class DataError(BacktestError):
    """Exception for data-related errors"""
    pass

class StrategyError(BacktestError):
    """Exception for strategy-related errors"""
    pass

class OptimizationError(BacktestError):
    """Exception for optimization-related errors"""
    pass
