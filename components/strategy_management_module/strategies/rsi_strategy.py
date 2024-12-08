# File: components/strategy_management_module/strategies/rsi_strategy.py
from components.strategy_management_module.strategies.strategy_base import StrategyBase
import pandas as pd

class RSIStrategy(StrategyBase):
    """Relative Strength Index (RSI) Strategy."""

    default_params = {
        'period': 14,
        'overbought': 70,
        'oversold': 30
    }

    def __init__(self, params=None):
        """Initialize strategy with parameters."""
        if params is None:
            params = self.default_params
        super().__init__(params)

    def validate_params(self):
        """Validate strategy parameters."""
        period = self.params.get('period')
        overbought = self.params.get('overbought')
        oversold = self.params.get('oversold')

        if not isinstance(period, int) or period <= 0:
            raise ValueError("period must be a positive integer")
        if not (0 < oversold < overbought < 100):
            raise ValueError("Invalid overbought/oversold levels")

    def generate_signals(self, data):
        """Generate trading signals."""
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        
        avg_gain = gain.rolling(window=self.params['period'], 
                              min_periods=1).mean()
        avg_loss = loss.rolling(window=self.params['period'], 
                              min_periods=1).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0.0
        signals.loc[rsi > self.params['overbought'], 'signal'] = -1.0  # Fixed chained assignment
        signals.loc[rsi < self.params['oversold'], 'signal'] = 1.0     # Fixed chained assignment
        signals['positions'] = signals['signal'].diff()

        return signals