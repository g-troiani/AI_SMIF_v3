from datetime import datetime
import pandas as pd
from components.strategy_management_module.strategies.strategy_base import StrategyBase
from components.trading_execution_engine.trade_signal import TradeSignal

class VolumeToggleStrategy(StrategyBase):
    """
    A simple 'toggle' strategy:
      - If bar.volume > self.params['volume_threshold'] (defaults to 100) and we have no position => BUY 1 share.
      - The next time volume > threshold (and we already have a position) => SELL 1 share.
      - Repeats indefinitely, toggling each time the volume is above the threshold.
    """

    default_params = {
        'volume_threshold': 100  # Default threshold if not supplied
    }

    def __init__(self, params=None):
        if params is None:
            params = self.default_params
        super().__init__(params)

        # Track whether we currently hold 1 share or not
        self.in_position = False

    def validate_params(self):
        """
        Minimal or no parameter checks, but we confirm that volume_threshold is numeric.
        """
        threshold = self.params.get('volume_threshold', 100)
        if not isinstance(threshold, (int, float)) or threshold < 0:
            raise ValueError("volume_threshold must be a non-negative number")

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        For a backtest approach: toggling an 'in_position' boolean row by row,
        switching from +1 to -1 each time volume exceeds the threshold.
        """
        threshold = self.params.get('volume_threshold', 100)
        signals = pd.DataFrame(index=data.index, columns=['signal'])
        signals['signal'] = 0.0

        in_pos = False
        for i in range(len(data)):
            if data['volume'].iloc[i] > threshold:
                if not in_pos:
                    # Mark a BUY signal
                    signals['signal'].iloc[i] = 1.0
                    in_pos = True
                else:
                    # Mark a SELL signal
                    signals['signal'].iloc[i] = -1.0
                    in_pos = False

        return signals

    def on_bar(self, bar):
        """
        Called in a real-time or streaming context for each new bar.
        If bar.volume > threshold => we toggle a position.

        Returns a TradeSignal if an action is taken, otherwise None.
        """
        threshold = self.params.get('volume_threshold', 100)

        if bar.volume > threshold:
            # Toggle
            if not self.in_position:
                self.in_position = True
                return TradeSignal(
                    ticker=bar.symbol,
                    signal_type='BUY',
                    quantity=1.0,
                    strategy_id='VOLUME_TOGGLE_STRAT',
                    timestamp=bar.timestamp,
                    price=bar.close,    # Example: use bar.close as reference
                    order_type='market'
                )
            else:
                self.in_position = False
                return TradeSignal(
                    ticker=bar.symbol,
                    signal_type='SELL',
                    quantity=1.0,
                    strategy_id='VOLUME_TOGGLE_STRAT',
                    timestamp=bar.timestamp,
                    price=bar.close,
                    order_type='market'
                )

        # If volume <= threshold, do nothing
        return None
