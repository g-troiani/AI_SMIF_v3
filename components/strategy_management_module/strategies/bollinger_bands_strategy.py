# File: components/strategy_management_module/strategies/bollinger_bands_strategy.py
# Type: py

import logging
import pandas as pd
from datetime import datetime
from components.strategy_management_module.strategies.strategy_base import StrategyBase
from components.trading_execution_engine.trade_signal import TradeSignal

logger = logging.getLogger(__name__)

class BollingerBandsStrategy(StrategyBase):
    """Bollinger Bands with optional stop_loss/take_profit in on_bar."""

    default_params = {
        'period': 20,
        'devfactor': 2,
        'stop_loss': 0.0,
        'take_profit': 0.0
    }

    def __init__(self, params=None):
        if params is None:
            params = self.default_params
        super().__init__(params)
        self.prices = []
        self.period = self.params['period']
        self.devfactor = self.params['devfactor']
        # track position:
        self._entry_price = None
        self._position_size = 0.0

    def validate_params(self):
        period = self.params['period']
        devfactor = self.params['devfactor']
        if not (isinstance(period, int) and period > 0):
            raise ValueError("Bollinger period must be positive int")
        if not (isinstance(devfactor, (int, float)) and devfactor > 0):
            raise ValueError("Bollinger devfactor must be positive")

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Typical Bollinger logic for backtest.
        """
        rolling_mean = data['close'].rolling(self.period).mean()
        rolling_std = data['close'].rolling(self.period).std()
        upper = rolling_mean + self.devfactor * rolling_std
        lower = rolling_mean - self.devfactor * rolling_std

        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0.0
        signals.loc[data['close']<lower, 'signal'] = 1.0
        signals.loc[data['close']>upper, 'signal'] = -1.0
        signals['positions'] = signals['signal'].diff()
        return signals

    def on_bar(self, bar):
        close_price = bar.close
        self.prices.append(close_price)
        if len(self.prices) > self.period:
            self.prices.pop(0)

        if len(self.prices) < self.period:
            return None

        # 1) see if we should exit due to SL/TP
        exit_signal = self.check_sl_tp(bar, self._position_size)
        if exit_signal:
            self._entry_price = None
            self._position_size = 0.0
            return exit_signal

        # 2) do Bollinger logic
        rolling_mean = pd.Series(self.prices).mean()
        rolling_std = pd.Series(self.prices).std()
        upper = rolling_mean + self.devfactor*rolling_std
        lower = rolling_mean - self.devfactor*rolling_std

        if close_price < lower and self._position_size <= 0:
            self._position_size = 1.0
            self._entry_price = close_price
            return TradeSignal(
                ticker=bar.symbol,
                signal_type='BUY',
                quantity=1.0,
                strategy_id='BOLL_LIVE',
                timestamp=bar.timestamp
            )
        elif close_price > upper and self._position_size > 0:
            # exit
            self._entry_price = None
            self._position_size = 0.0
            return TradeSignal(
                ticker=bar.symbol,
                signal_type='SELL',
                quantity=1.0,
                strategy_id='BOLL_LIVE',
                timestamp=bar.timestamp
            )
        return None
