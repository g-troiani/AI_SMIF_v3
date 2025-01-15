import logging
import pandas as pd
import numpy as np
from datetime import datetime
from components.strategy_management_module.strategies.strategy_base import StrategyBase
from components.trading_execution_engine.trade_signal import TradeSignal

logger = logging.getLogger(__name__)

class MovingAverageCrossoverStrategy(StrategyBase):
    """Moving Average Crossover Strategy Implementation for backtest & live usage."""

    default_params = {
        'short_window': 40,
        'long_window': 100,
        'stop_loss': 0.0,
        'take_profit': 0.0
    }

    def __init__(self, params=None):
        if params is None:
            params = self.default_params
        super().__init__(params)

        self.short_window = self.params['short_window']
        self.long_window = self.params['long_window']

        self.short_prices = []
        self.long_prices = []

        # If the system design uses stop_loss / take_profit in real-time
        self.stop_loss_pct = self.params.get('stop_loss', 0.0)
        self.take_profit_pct = self.params.get('take_profit', 0.0)

    def validate_params(self) -> None:
        short_window = self.params['short_window']
        long_window = self.params['long_window']
        if not all(isinstance(x, int) and x > 0 for x in [short_window, long_window]):
            raise ValueError("Windows must be positive integers")
        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Original backtest logic:
        short SMA crosses above long => buy, else => sell
        """
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0.0

        signals['short_mavg'] = data['close'].rolling(
            window=self.params['short_window'], 
            min_periods=1
        ).mean()
        signals['long_mavg'] = data['close'].rolling(
            window=self.params['long_window'], 
            min_periods=1
        ).mean()

        signals.loc[signals['short_mavg'] > signals['long_mavg'], 'signal'] = 1.0
        signals['positions'] = signals['signal'].diff().fillna(0)

        return signals

    def on_bar(self, bar):
        """
        Real-time incremental short/long moving average logic:
        - Keep last X closes for short period, last Y for long
        - If short_avg > long_avg => BUY, else => SELL
        """
        close_price = bar.close
        self.short_prices.append(close_price)
        self.long_prices.append(close_price)

        if len(self.short_prices) > self.short_window:
            self.short_prices.pop(0)
        if len(self.long_prices) > self.long_window:
            self.long_prices.pop(0)

        if len(self.short_prices) < self.short_window or len(self.long_prices) < self.long_window:
            return None

        short_avg = np.mean(self.short_prices)
        long_avg = np.mean(self.long_prices)

        if short_avg > long_avg:
            # e.g. a BUY signal
            return TradeSignal(
                ticker=bar.symbol,
                signal_type='BUY',
                quantity=1.0,
                strategy_id='MA_CROSS_LIVE',
                timestamp=bar.timestamp,
                price=close_price
            )
        elif short_avg < long_avg:
            # e.g. a SELL signal
            return TradeSignal(
                ticker=bar.symbol,
                signal_type='SELL',
                quantity=1.0,
                strategy_id='MA_CROSS_LIVE',
                timestamp=bar.timestamp,
                price=close_price
            )

        return None
