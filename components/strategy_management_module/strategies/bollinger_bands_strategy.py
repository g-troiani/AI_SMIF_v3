# File: components/strategy_management_module/strategies/bollinger_bands_strategy.py
from components.strategy_management_module.strategies.strategy_base import StrategyBase
import pandas as pd

class BollingerBandsStrategy(StrategyBase):
    """Bollinger Bands Strategy."""

    default_params = {
        'window': 20,
        'num_std': 2
    }

    def __init__(self, params=None):
        """Initialize strategy with parameters."""
        if params is None:
            params = self.default_params
        super().__init__(params)

    def validate_params(self):
        """Validate strategy parameters."""
        window = self.params.get('window')
        num_std = self.params.get('num_std')

        if not isinstance(window, int) or window <= 0:
            raise ValueError("window must be a positive integer")
        if not isinstance(num_std, (int, float)) or num_std <= 0:
            raise ValueError("num_std must be a positive number")

    def generate_signals(self, data):
        """Generate trading signals."""
        rolling_mean = data['close'].rolling(window=self.params['window']).mean()
        rolling_std = data['close'].rolling(window=self.params['window']).std()
        
        upper_band = rolling_mean + (rolling_std * self.params['num_std'])
        lower_band = rolling_mean - (rolling_std * self.params['num_std'])
        
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0.0
        signals['signal'] = ((data['close'] <= lower_band).astype(float) - 
                           (data['close'] >= upper_band).astype(float))
        signals['positions'] = signals['signal'].diff()
        
        return signals