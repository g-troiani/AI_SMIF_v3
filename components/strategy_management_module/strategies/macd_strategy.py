# File: components/strategy_management_module/strategies/macd_strategy.py
from components.strategy_management_module.strategies.strategy_base import StrategyBase
import pandas as pd

class MACDStrategy(StrategyBase):
    """Moving Average Convergence Divergence (MACD) Strategy."""

    default_params = {
        'fast_period': 12,
        'slow_period': 26,
        'signal_period': 9
    }

    def __init__(self, params=None):
        """Initialize strategy with parameters."""
        if params is None:
            params = self.default_params
        super().__init__(params)

    def validate_params(self):
        """Validate strategy parameters."""
        fast_period = self.params.get('fast_period')
        slow_period = self.params.get('slow_period')
        signal_period = self.params.get('signal_period')

        if not all(isinstance(x, int) and x > 0 
                  for x in [fast_period, slow_period, signal_period]):
            raise ValueError("All periods must be positive integers")
        if fast_period >= slow_period:
            raise ValueError("fast_period must be less than slow_period")

    def generate_signals(self, data):
        """Generate trading signals."""
        exp1 = data['close'].ewm(span=self.params['fast_period'], 
                                adjust=False).mean()
        exp2 = data['close'].ewm(span=self.params['slow_period'], 
                                adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=self.params['signal_period'], 
                              adjust=False).mean()
        
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0.0
        signals['signal'] = (macd > signal_line).astype(float)
        signals['positions'] = signals['signal'].diff()
        
        return signals