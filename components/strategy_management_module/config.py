# File: components/strategy_management_module/config.py
"""
Changes:
- Added configuration constants for strategies
- Added type hints and docstring
"""
"""
Configuration settings for the Strategy Management Module
"""
# Default settings for strategies
STRATEGY_SETTINGS = {
    'default_allocation': 5000,
    'max_active_strategies': 5,
    'validation_thresholds': {
        'min_sharpe_ratio': 0.5,
        'max_drawdown': -0.2
    }
}