# components/backtesting_module/config.py

class BacktestConfig:
    """Configuration for backtesting module"""
    
    # Database settings
    DB_PATH = 'data/backtest_results.db'
    
    # Backtest settings
    INITIAL_CASH = 100000.0
    DEFAULT_COMMISSION = 0.001
    BENCHMARK_TICKER = 'SPY'
    
    # Data settings
    DEFAULT_TIMEFRAME = '1Day'
    MIN_DATA_POINTS = 100
    
    # Resource limits
    MAX_OPTIMIZATION_COMBINATIONS = 100
    CPU_THRESHOLD = 80
    MEMORY_THRESHOLD = 80