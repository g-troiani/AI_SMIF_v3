# File: components/strategy_management_module/strategy_manager.py
# Type: py

import logging
from typing import Dict, Any, List

class ParameterValidator:
    """
    Validates strategy parameters and enforces optimization limits
    """
    DEFAULT_RANGES = {
        'MovingAverageCrossover': {
            'short_window': {'min': 5, 'max': 15, 'step': 1},
            'long_window': {'min': 10, 'max': 20, 'step': 1}
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

class StrategyManager:
    """
    Manages strategies, each of which can be in 'live' or 'backtest' mode, 
    and validates their parameters.
    """

    def __init__(self):
        self.logger = logging.getLogger('strategy_manager')
        self.strategies = {}  # { 'strategy_name': {'mode': str, 'params': dict} }
        self.parameter_validator = ParameterValidator()

    def change_strategy_mode(self, strat_name: str, new_mode: str, params: Dict[str, Any] = None):
        """
        Change a strategy's mode and optionally update its parameters.
        
        Args:
            strat_name: Name of the strategy
            new_mode: Either 'live' or 'backtest'
            params: Optional dictionary of strategy parameters to validate
        """
        if new_mode not in ['live', 'backtest']:
            new_mode = 'backtest'

        # Validate parameters if provided
        if params:
            try:
                ParameterValidator.validate_parameters(strat_name, params)
            except ValueError as e:
                self.logger.error(f"Parameter validation failed: {e}")
                return

        # Initialize strategy if it doesn't exist
        if strat_name not in self.strategies:
            self.strategies[strat_name] = {'mode': 'backtest', 'params': params or {}}

        current_mode = self.strategies[strat_name]['mode']
        if current_mode == new_mode:
            self.logger.info(f"Strategy {strat_name} is already in {new_mode} mode.")
            return

        # Update the mode and parameters
        self.strategies[strat_name]['mode'] = new_mode
        if params:
            self.strategies[strat_name]['params'] = params
        
        self.logger.info(f"Changed {strat_name} from {current_mode} to {new_mode}.")