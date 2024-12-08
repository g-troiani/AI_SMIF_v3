# File: components/strategy_management_module/strategies/momentum_strategy.py
from components.strategy_management_module.strategies.strategy_base import StrategyBase
import pandas as pd

class MomentumStrategy(StrategyBase):
    """Simple Momentum Strategy."""

    default_params = {
        'lookback_period': 20,
        'threshold': 0
    }

    def __init__(self, params=None):
        """Initialize strategy with parameters."""
        if params is None:
            params = self.default_params
        super().__init__(params)

    def validate_params(self):
        """Validate strategy parameters."""
        lookback_period = self.params.get('lookback_period')
        threshold = self.params.get('threshold')

        if not isinstance(lookback_period, int) or lookback_period <= 0:
            raise ValueError("lookback_period must be a positive integer")
        if not isinstance(threshold, (int, float)):
            raise ValueError("threshold must be a number")

    def generate_signals(self, data):
        """Generate trading signals."""
        momentum = data['close'].pct_change(periods=self.params['lookback_period'])
        
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0.0
        signals['signal'] = (momentum > self.params['threshold']).astype(float)
        signals['positions'] = signals['signal'].diff()
        
        return signals