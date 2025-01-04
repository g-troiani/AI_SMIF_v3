from datetime import datetime
import pandas as pd
from components.strategy_management_module.strategies.strategy_base import StrategyBase
from components.trading_execution_engine.trade_signal import TradeSignal

class VolumeToggleStrategy(StrategyBase):
    """
    A simple 'toggle' strategy:
      - If bar.volume > 100 and we have no position => BUY 1 share.
      - The next time bar.volume > 100 (and we already have a position) => SELL 1 share.
      - Repeats indefinitely, toggling each time volume>100.
    """

    default_params = {}

    def __init__(self, params=None):
        if params is None:
            params = self.default_params
        super().__init__(params)

        # Track whether we currently hold 1 share or not
        self.in_position = False

    def validate_params(self):
        """
        Minimal or no parameter checks. 
        Could add checks for custom fields if needed.
        """
        pass

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        If you are using this in a typical 'backtest' mode that expects 
        a whole-data approach, you can generate signals for each row.

        For example:
          1) Create a 'signal' column defaulted to 0.0
          2) Each time volume > 100 => flip the signal from +1 (BUY) to -1 (SELL).
        But for now, we illustrate just a skeleton approach.
        """
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0.0
        # Example logic: toggling an 'in_position' boolean row by row
        in_pos = False
        for i in range(len(data)):
            if data['volume'].iloc[i] > 100:
                if not in_pos:
                    # Set to +1 => buy
                    signals['signal'].iloc[i] = 1.0
                    in_pos = True
                else:
                    # Switch to -1 => sell
                    signals['signal'].iloc[i] = -1.0
                    in_pos = False

        # signals['positions'] = signals['signal'].diff()  # optional
        return signals

    def on_bar(self, bar):
        """
        Called in a real-time or streaming context for each new bar.

        If bar.volume > 100 => we toggle:
         - If not in_position => produce a 'BUY' signal
         - Else if in_position => produce a 'SELL' signal
        """
        if bar.volume > 100:
            if not self.in_position:
                # BUY
                self.in_position = True
                return TradeSignal(
                    ticker=bar.symbol,
                    signal_type='BUY',
                    quantity=1.0,
                    strategy_id='VOLUME_TOGGLE_STRAT',
                    timestamp=bar.timestamp,
                    price=bar.close,
                    order_type='market'   # or 'limit', 'stop', etc.
                )
            else:
                # SELL
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

        # If volume not > 100 or no toggle, return None => no new trade
        return None
