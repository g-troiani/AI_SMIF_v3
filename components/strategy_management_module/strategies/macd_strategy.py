# File: components/strategy_management_module/strategies/macd_strategy.py
# Type: py

import logging
import pandas as pd
from datetime import datetime
from components.strategy_management_module.strategies.strategy_base import StrategyBase
from components.trading_execution_engine.trade_signal import TradeSignal

logger = logging.getLogger(__name__)

class MACDStrategy(StrategyBase):
    """
    MACD Strategy Implementation for both backtest and live usage.
    Now with optional stop_loss / take_profit usage in on_bar.
    """

    default_params = {
        'fast_period': 12,
        'slow_period': 26,
        'signal_period': 9,
        'stop_loss': 0.0,     # newly added
        'take_profit': 0.0    # newly added
    }

    def __init__(self, params=None):
        if params is None:
            params = self.default_params
        super().__init__(params)
        # For live usage, store rolling states:
        self.ema_fast = 0.0
        self.ema_slow = 0.0
        self.signal_line = 0.0
        self.fast_k = 2 / (self.params['fast_period'] + 1)
        self.slow_k = 2 / (self.params['slow_period'] + 1)
        self.sig_k = 2 / (self.params['signal_period'] + 1)

        # We'll track a "position" approach:
        self._entry_price = None
        self._position_size = 0.0

    def validate_params(self):
        fast_period = self.params['fast_period']
        slow_period = self.params['slow_period']
        signal_period = self.params['signal_period']
        if not all(isinstance(x, int) and x > 0 for x in [fast_period, slow_period, signal_period]):
            raise ValueError("MACD periods must be positive integers")
        if fast_period >= slow_period:
            raise ValueError("fast_period must be < slow_period")

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Original backtest logic, using typical MACD calculations.
        """
        exp1 = data['close'].ewm(span=self.params['fast_period'], adjust=False).mean()
        exp2 = data['close'].ewm(span=self.params['slow_period'], adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=self.params['signal_period'], adjust=False).mean()

        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0.0
        signals['signal'] = (macd_line > signal_line).astype(float)
        signals['positions'] = signals['signal'].diff()
        return signals

    def on_bar(self, bar):
        """
        Real-time incremental approach. 
        We'll do the incremental EMA, then check if SL/TP triggered, then produce a BUY/SELL if needed.
        """
        close_price = bar.close
        if self.ema_fast == 0.0:
            # first bar
            self.ema_fast = close_price
            self.ema_slow = close_price
            self.signal_line = 0.0
            return None

        # update EMAs
        self.ema_fast = (close_price - self.ema_fast)*self.fast_k + self.ema_fast
        self.ema_slow = (close_price - self.ema_slow)*self.slow_k + self.ema_slow
        macd_line = self.ema_fast - self.ema_slow
        if self.signal_line == 0.0:
            self.signal_line = macd_line
        else:
            self.signal_line = (macd_line - self.signal_line)*self.sig_k + self.signal_line

        # 1) Check if stop-loss or take-profit triggered:
        exit_signal = self.check_sl_tp(bar, self._position_size)
        if exit_signal:
            # reset after exit
            self._entry_price = None
            self._position_size = 0.0
            return exit_signal

        # 2) If no SL/TP triggered, do the usual MACD logic
        if macd_line > self.signal_line:
            # we want to be long => if we're flat or short => BUY:
            if self._position_size <= 0:
                self._position_size = 1.0
                self._entry_price = close_price
                return TradeSignal(
                    ticker=bar.symbol,
                    signal_type='BUY',
                    quantity=1.0,
                    strategy_id='MACD_LIVE',
                    timestamp=bar.timestamp
                )
        else:
            # macd_line < self.signal_line => we want to be out or short => for simplicity, we just exit if long
            if self._position_size > 0:
                # exit the long
                self._position_size = 0.0
                self._entry_price = None
                return TradeSignal(
                    ticker=bar.symbol,
                    signal_type='SELL',
                    quantity=1.0,
                    strategy_id='MACD_LIVE',
                    timestamp=bar.timestamp
                )
        return None
