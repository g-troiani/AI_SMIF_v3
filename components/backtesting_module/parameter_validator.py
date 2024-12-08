# components/backtesting_module/parameter_validator.py

import logging
from typing import Dict, Any, List

# components/backtesting_module/parameter_validator.py

class ParameterValidator:
    """
    Validates strategy parameters and enforces optimization limits
    """
    # Default parameter ranges aligned with documentation
    DEFAULT_RANGES = {
        'MovingAverageCrossover': {
            'short_window': {'min': 5, 'max': 15, 'step': 1},  # Documentation specifies smaller range
            'long_window': {'min': 10, 'max': 20, 'step': 1}   # Documentation specifies smaller range
        },
        'RSIStrategy': {
            'rsi_period': {'min': 5, 'max': 30, 'step': 5},
            'oversold': {'min': 20, 'max': 40, 'step': 5},
            'overbought': {'min': 60, 'max': 80, 'step': 5}
        },
        'MACDStrategy': {
            'fast_period': {'min': 12, 'max': 16, 'step': 1},
            'slow_period': {'min': 26, 'max': 30, 'step': 1},
            'signal_period': {'min': 9, 'max': 12, 'step': 1}
        },
        'BollingerBandsStrategy': {
            'window': {'min': 20, 'max': 30, 'step': 5},
            'num_std': {'min': 2, 'max': 3, 'step': 0.5}
        }
    }
       
    @staticmethod
    def validate_parameters(strategy_name: str, params: Dict[str, Any]) -> bool:
        """
        Validates that parameters are within acceptable ranges
        """
        if strategy_name not in ParameterValidator.DEFAULT_RANGES:
            logging.warning(f"No validation rules for strategy: {strategy_name}")
            return True
            
        ranges = ParameterValidator.DEFAULT_RANGES[strategy_name]
        for param, value in params.items():
            if param in ranges:
                if value < ranges[param]['min'] or value > ranges[param]['max']:
                    raise ValueError(
                        f"Parameter {param} value {value} outside valid range "
                        f"({ranges[param]['min']}-{ranges[param]['max']})"
                    )
        return True

    @staticmethod
    def generate_grid_parameters(strategy_name: str) -> Dict[str, List[float]]:
        """
        Generates parameter combinations for grid search within safe limits
        """
        if strategy_name not in ParameterValidator.DEFAULT_RANGES:
            raise ValueError(f"No grid search parameters defined for {strategy_name}")
            
        ranges = ParameterValidator.DEFAULT_RANGES[strategy_name]
        grid_params = {}
        
        for param, range_info in ranges.items():
            values = list(range(
                range_info['min'],
                range_info['max'] + range_info['step'],
                range_info['step']
            ))
            grid_params[param] = values
            
        return grid_params
