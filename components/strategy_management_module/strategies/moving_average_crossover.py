# File: components/strategy_management_module/strategies/moving_average_crossover.py
"""
Changes:
- Added proper type hints
- Improved validation
- Added logging
- Added signal generation error handling
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict
from .strategy_base import StrategyBase

class MovingAverageCrossoverStrategy(StrategyBase):
    """Moving Average Crossover trading strategy."""

    default_params = {
        'short_window': 40,
        'long_window': 100
    }

    def __init__(self, params: Dict = None):
        self.logger = logging.getLogger(__name__)
        super().__init__(params or self.default_params)

    def validate_params(self) -> None:
        """Validate strategy parameters."""
        short_window = self.params.get('short_window')
        long_window = self.params.get('long_window')

        if not all(isinstance(x, int) and x > 0 
                  for x in [short_window, long_window]):
            raise ValueError("Windows must be positive integers")
        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals based on moving average crossover."""
        try:
            signals = pd.DataFrame(index=data.index)
            signals['signal'] = 0.0

            # Calculate moving averages
            signals['short_mavg'] = data['close'].rolling(
                window=self.params['short_window'], 
                min_periods=1).mean()
            signals['long_mavg'] = data['close'].rolling(
                window=self.params['long_window'], 
                min_periods=1).mean()

            # Generate signals using loc to avoid chained assignment warning
            signals.loc[signals.index, 'signal'] = np.where(
                signals['short_mavg'] > signals['long_mavg'], 1.0, 0.0)
            signals['positions'] = signals['signal'].diff()

            return signals
        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")
            raise