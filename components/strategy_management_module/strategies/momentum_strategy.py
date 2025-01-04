import logging
import pandas as pd
from datetime import datetime
from components.strategy_management_module.strategies.strategy_base import StrategyBase
from components.trading_execution_engine.trade_signal import TradeSignal

logger = logging.getLogger(__name__)

class MomentumStrategy(StrategyBase):
    """Simple Momentum Strategy Implementation for backtest & live usage."""

    default_params = {
        'lookback_period': 20,
        'threshold': 0,         # e.g. 0 => zero% threshold
        'stop_loss': 0.0,       # optional
        'take_profit': 0.0      # optional
    }

    def __init__(self, params=None):
        if params is None:
            params = self.default_params
        super().__init__(params)

        self.lookback = self.params['lookback_period']
        self.threshold = self.params['threshold']

        # Rolling arrays for incremental logic
        self.prices = []
        self.stop_loss_pct = self.params.get('stop_loss', 0.0)
        self.take_profit_pct = self.params.get('take_profit', 0.0)

    def validate_params(self):
        lookback = self.params['lookback_period']
        threshold = self.params['threshold']
        if not isinstance(lookback, int) or lookback <= 0:
            raise ValueError("Momentum lookback_period must be a positive integer")
        if not isinstance(threshold, (int, float)):
            raise ValueError("threshold must be a numeric value")

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Original backtest logic:
        momentum = (close / close_n_bars_ago) - 1
        if momentum > threshold => buy, else => sell
        """
        momentum = data['close'].pct_change(periods=self.params['lookback_period'])

        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0.0
        signals.loc[momentum > self.threshold, 'signal'] = 1.0
        signals['positions'] = signals['signal'].diff().fillna(0)
        return signals

    def on_bar(self, bar):
        """
        Real-time incremental momentum logic:
        - Keep last N closes
        - Compare current close to old_price from N bars ago
        - If (close/old_price - 1) > threshold => BUY, else SELL
        """
        close_price = bar.close
        self.prices.append(close_price)
        if len(self.prices) > self.lookback + 1:
            self.prices.pop(0)

        if len(self.prices) < self.lookback + 1:
            return None

        old_price = self.prices[0]
        momentum_val = (close_price / old_price) - 1.0

        if momentum_val > self.threshold:
            # e.g. a BUY signal
            return TradeSignal(
                ticker=bar.symbol,
                signal_type='BUY',
                quantity=1.0,
                strategy_id='MOMENTUM_LIVE',
                timestamp=bar.timestamp,
                price=close_price
            )
        else:
            # e.g. a SELL signal
            return TradeSignal(
                ticker=bar.symbol,
                signal_type='SELL',
                quantity=1.0,
                strategy_id='MOMENTUM_LIVE',
                timestamp=bar.timestamp,
                price=close_price
            )
