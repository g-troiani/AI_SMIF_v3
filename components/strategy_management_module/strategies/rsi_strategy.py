import logging
import pandas as pd
from datetime import datetime
from components.strategy_management_module.strategies.strategy_base import StrategyBase
from components.trading_execution_engine.trade_signal import TradeSignal

logger = logging.getLogger(__name__)

class RSIStrategy(StrategyBase):
    """RSI Strategy Implementation for backtest & live usage."""

    default_params = {
        'period': 14,
        'overbought': 70,
        'oversold': 30
    }

    def __init__(self, params=None):
        if params is None:
            params = self.default_params
        super().__init__(params)

        # For live usage, keep last N closes for incremental RSI
        self.prices = []
        self.period = self.params['period']
        self.overbought = self.params['overbought']
        self.oversold = self.params['oversold']

        # If the system design calls for stop_loss / take_profit usage:
        # We can store them as well for the on_bar logic if needed.
        self.stop_loss_pct = self.params.get('stop_loss', 0.0)
        self.take_profit_pct = self.params.get('take_profit', 0.0)

    def validate_params(self):
        period = self.params['period']
        overbought = self.params['overbought']
        oversold = self.params['oversold']
        if not isinstance(period, int) or period <= 0:
            raise ValueError("RSI period must be a positive integer")
        if not (0 < oversold < overbought < 100):
            raise ValueError("RSI overbought/oversold must be in (0,100) and oversold < overbought")

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Original backtest logic:
        - Typical RSI across entire dataset: RSI = 100 - 100/(1 + RS)
        - Then buy if RSI < oversold, sell if RSI > overbought
        """
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        avg_gain = gain.rolling(self.params['period']).mean()
        avg_loss = loss.rolling(self.params['period']).mean()

        rs = avg_gain / avg_loss.replace(0, float('inf'))
        rsi = 100 - (100 / (1 + rs))

        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0.0
        signals.loc[rsi > self.params['overbought'], 'signal'] = -1.0
        signals.loc[rsi < self.params['oversold'],  'signal'] =  1.0
        signals['positions'] = signals['signal'].diff().fillna(0)
        return signals

    def on_bar(self, bar):
        """
        Real-time incremental RSI logic:
        - Keep last N closes, compute RSI for new bar
        - If RSI < oversold => BUY signal
        - If RSI > overbought => SELL signal
        - If desired, we can also incorporate any stop_loss / take_profit logic here
        """
        close_price = bar.close
        self.prices.append(close_price)
        if len(self.prices) > self.period + 1:
            self.prices.pop(0)

        # Not enough data yet
        if len(self.prices) < self.period + 1:
            return None

        # Compute RSI for current bar
        deltas = pd.Series(self.prices).diff()
        gains = deltas.where(deltas > 0, 0.0)
        losses = -deltas.where(deltas < 0, 0.0)

        avg_gain = gains.tail(self.period).mean()
        avg_loss = losses.tail(self.period).mean()

        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        # Check RSI-based signals
        if rsi < self.oversold:
            # e.g. generate a BUY TradeSignal
            return TradeSignal(
                ticker=bar.symbol,
                signal_type='BUY',
                quantity=1.0,
                strategy_id='RSI_LIVE',
                timestamp=bar.timestamp,
                price=close_price
            )
        elif rsi > self.overbought:
            # e.g. generate a SELL TradeSignal
            return TradeSignal(
                ticker=bar.symbol,
                signal_type='SELL',
                quantity=1.0,
                strategy_id='RSI_LIVE',
                timestamp=bar.timestamp,
                price=close_price
            )

        return None
