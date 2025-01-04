# File: components/strategy_management_module/strategies/strategy_base.py
# Type: py

from abc import ABC, abstractmethod
from typing import Dict
import pandas as pd

# We need to import TradeSignal for the stop-loss / take-profit logic:
from components.trading_execution_engine.trade_signal import TradeSignal

class StrategyBase(ABC):
    """Base class for all trading strategies."""

    def __init__(self, params: Dict):
        self.params = params
        self.validate_params()

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Backtest-oriented method that processes an entire DataFrame and returns signals.
        """
        pass

    @abstractmethod
    def validate_params(self) -> None:
        """
        Subclasses must validate param keys and raise ValueError if invalid.
        """
        pass

    # ---------------------------------------------------------------------
    # NEW HELPER: check_sl_tp for stop-loss / take-profit in on_bar usage
    # ---------------------------------------------------------------------
    def check_sl_tp(
        self,
        bar,
        current_position_size: float
    ) -> TradeSignal or None:
        """
        Called in on_bar to see if stop_loss or take_profit triggered an exit.

        :param bar: An object with .close, .symbol, .timestamp
        :param current_position_size: The strategy's currently held size: e.g. +1.0 means long 1.
        :return: A TradeSignal (SELL or BUY) to exit if triggered, otherwise None.
        """

        # Pull user’s stop_loss and take_profit from self.params (0.0 means disabled).
        stop_loss_pct = self.params.get('stop_loss', 0.0)
        take_profit_pct = self.params.get('take_profit', 0.0)

        # If we’re not in a position, skip
        if current_position_size == 0:
            return None

        # Example approach: store an attribute self._entry_price in the actual strategy’s code.
        entry_price = getattr(self, '_entry_price', None)
        if entry_price is None:
            # If we never stored an entry price, can't measure P/L. So skip.
            return None

        # If we are LONG (current_position_size>0), check the % change from entry.
        # If we are SHORT (current_position_size<0), you'd do a separate approach, etc.
        if current_position_size > 0:
            change_pct = (bar.close - entry_price) / entry_price
            # STOP-LOSS
            if stop_loss_pct > 0.0 and (change_pct <= -stop_loss_pct):
                return TradeSignal(
                    ticker=bar.symbol,
                    signal_type='SELL',  # exit from a long
                    quantity=abs(current_position_size),
                    strategy_id='SL_EXIT',
                    timestamp=bar.timestamp
                )
            # TAKE-PROFIT
            if take_profit_pct > 0.0 and (change_pct >= take_profit_pct):
                return TradeSignal(
                    ticker=bar.symbol,
                    signal_type='SELL',
                    quantity=abs(current_position_size),
                    strategy_id='TP_EXIT',
                    timestamp=bar.timestamp
                )

        # For short positions, you would invert the logic here, if your system supports shorting.
        return None
