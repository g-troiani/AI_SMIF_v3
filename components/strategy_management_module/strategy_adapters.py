# # File: components/backtesting_module/backtrader/strategy_adapters.py
# # Type: py

# File: components/strategy_management_module/strategy_adapter.py

import logging
import pandas as pd
from datetime import datetime
import os
import sqlite3
import json

#
# ----- 1) The Backtrader Strategies from old "backtesting_module/backtrader/strategy_adapters.py"
#


import backtrader as bt

class BaseStrategyWithSLTP(bt.Strategy):
    """
    Adds optional stop_loss/take_profit to derived strategies.
    """
    params = (
        ('stop_loss', 0.0),
        ('take_profit', 0.0),
    )

    def __init__(self):
        self.entry_price = None

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
            elif order.issell():
                self.entry_price = None

    def check_sl_tp(self):
        if self.position and self.entry_price:
            current_price = self.data.close[0]
            pct_change = (current_price - self.entry_price) / self.entry_price * 100.0
            # Check stop loss
            if self.params.stop_loss and pct_change <= -abs(self.params.stop_loss):
                self.close()
            # Check take profit
            elif self.params.take_profit and pct_change >= abs(self.params.take_profit):
                self.close()


class MovingAverageCrossoverStrategy(bt.Strategy):
    """Moving Average Crossover Strategy Implementation"""
    params = (
        ('short_window', 10),
        ('long_window', 20),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        self.short_ma = bt.indicators.SMA(self.data.close, period=self.params.short_window)
        self.long_ma = bt.indicators.SMA(self.data.close, period=self.params.long_window)
        self.crossover = bt.indicators.CrossOver(self.short_ma, self.long_ma)

    def next(self):
        if self.crossover > 0 and not self.position:
            entry_price = self.data.close[0]
            if self.params.stop_loss is not None and self.params.take_profit is not None:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.crossover < 0 and self.position:
            self.sell()


class RSIStrategy(bt.Strategy):
    """RSI Strategy Implementation"""
    params = (
        ('rsi_period', 14),
        ('overbought', 70),
        ('oversold', 30),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)

    def next(self):
        if self.rsi < self.params.oversold and not self.position:
            entry_price = self.data.close[0]
            if self.params.stop_loss is not None and self.params.take_profit is not None:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.rsi > self.params.overbought and self.position:
            self.sell()


class MACDStrategy(bt.Strategy):
    """MACD Strategy Implementation"""
    params = (
        ('fast_period', 12),
        ('slow_period', 26),
        ('signal_period', 9),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.fast_period,
            period_me2=self.params.slow_period,
            period_signal=self.params.signal_period
        )

    def next(self):
        if self.macd.macd > self.macd.signal and not self.position:
            entry_price = self.data.close[0]
            if self.params.stop_loss is not None and self.params.take_profit is not None:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.macd.macd < self.macd.signal and self.position:
            self.sell()


class BollingerBandsStrategy(bt.Strategy):
    """Bollinger Bands Strategy Implementation"""
    params = (
        ('period', 20),
        ('devfactor', 2),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        self.boll = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.period,
            devfactor=self.params.devfactor
        )

    def next(self):
        if self.data.close[0] < self.boll.lines.bot[0] and not self.position:
            entry_price = self.data.close[0]
            if self.params.stop_loss is not None and self.params.take_profit is not None:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.data.close[0] > self.boll.lines.top[0] and self.position:
            self.sell()


class MomentumStrategy(bt.Strategy):
    """Simple Momentum Strategy Implementation"""
    params = (
        ('momentum_period', 10),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        self.momentum = bt.indicators.MomentumOscillator(
            self.data.close,
            period=self.params.momentum_period
        )

    def next(self):
        if self.momentum[0] > 0 and not self.position:
            entry_price = self.data.close[0]
            if self.params.stop_loss is not None and self.params.take_profit is not None:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.momentum[0] < 0 and self.position:
            self.sell()


#
# ----- 2) A minimal "Pure Python" strategy example
#

class PythonSmaStrategy:
    """
    Example 'pure Python' strategy that accumulates data per symbol and
    triggers signals based on a short/long SMA crossing.
    """
    def __init__(self, execution_engine):
        self.execution_engine = execution_engine
        self.dataframes = {}  # {symbol: pd.DataFrame}

    def on_new_bar(self, symbol, timestamp, o, h, l, c, v):
        import math
        if symbol not in self.dataframes:
            self.dataframes[symbol] = pd.DataFrame(columns=['timestamp','open','high','low','close','volume'])

        df = self.dataframes[symbol]
        df.loc[len(df)] = [timestamp, o, h, l, c, v]

        if len(df) < 15:
            return  # not enough data

        closes = df['close']
        short_sma = closes.rolling(5).mean().iloc[-1]
        long_sma  = closes.rolling(15).mean().iloc[-1]

        # Example logic: if short_sma > long_sma => BUY, else SELL
        from trading_execution_engine.trade_signal import TradeSignal
        from datetime import datetime

        if short_sma > long_sma:
            signal = TradeSignal(
                ticker=symbol,
                signal_type='BUY',
                quantity=1.0,
                strategy_id='python_sma',
                timestamp=datetime.utcnow(),
                order_type='market'  # example
            )
            self.execution_engine.add_trade_signal(signal)
        else:
            signal = TradeSignal(
                ticker=symbol,
                signal_type='SELL',
                quantity=1.0,
                strategy_id='python_sma',
                timestamp=datetime.utcnow(),
                order_type='market'
            )
            self.execution_engine.add_trade_signal(signal)

class VolumeToggleStrategy(bt.Strategy):
    """Volume-based toggle strategy. If volume exceeds a threshold, it toggles a position."""

    params = (
        ('volume_threshold', 100),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        """Initialize indicators or any flags if needed."""
        pass

    def next(self):
        """Runs on each new bar."""
        current_volume = self.data.volume[0]
        # Simple toggle logic:
        if current_volume > self.params.volume_threshold:
            if not self.position:
                # If no position, open one (buy or bracket).
                entry_price = self.data.close[0]
                if self.params.stop_loss is not None and self.params.take_profit is not None:
                    stop_price = entry_price * (1.0 - self.params.stop_loss)
                    limit_price = entry_price * (1.0 + self.params.take_profit)
                    self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
                else:
                    self.buy()
            else:
                # If already in a position, close it (sell).
                self.sell()

# ...

class StrategyAdapter:
    """
    Strategy adapter that maps strategy names to their implementations.
    """
    STRATEGIES = {
        'MovingAverageCrossover': MovingAverageCrossoverStrategy,
        'RSI': RSIStrategy,
        'MACD': MACDStrategy,
        'BollingerBands': BollingerBandsStrategy,
        'Momentum': MomentumStrategy,
        'VolumeToggleStrategy': VolumeToggleStrategy,
    }

    @staticmethod
    def get_strategy(name):
        if name not in StrategyAdapter.STRATEGIES:
            raise ValueError(
                f"Strategy '{name}' not found. "
                f"Available strategies: {list(StrategyAdapter.STRATEGIES.keys())}"
            )
        return StrategyAdapter.STRATEGIES[name]


#
# ----- 3) A minimal "Backtrader Manager" example
#

class MinimalBTStrategy(bt.Strategy):
    """
    Simple example for cross-over in real-time or backtest, uses the ExecutionEngine to place signals.
    """
    params = (('execution_engine', None),)

    def __init__(self):
        self.ma_short = bt.indicators.SMA(self.data.close, period=5)
        self.ma_long  = bt.indicators.SMA(self.data.close, period=15)
        self.crossover = bt.indicators.CrossOver(self.ma_short, self.ma_long)

    def next(self):
        if self.crossover > 0:
            # buy signal
            from trading_execution_engine.trade_signal import TradeSignal
            signal = TradeSignal(
                ticker=self.data._name,
                signal_type='BUY',
                quantity=1,
                strategy_id='bt_sma',
                timestamp=datetime.utcnow()
            )
            self.p.execution_engine.add_trade_signal(signal)
        elif self.crossover < 0:
            # sell signal
            from trading_execution_engine.trade_signal import TradeSignal
            signal = TradeSignal(
                ticker=self.data._name,
                signal_type='SELL',
                quantity=1,
                strategy_id='bt_sma',
                timestamp=datetime.utcnow()
            )
            self.p.execution_engine.add_trade_signal(signal)


class BacktraderManager:
    """
    Minimal approach to feed new bars to a Cerebro instance and run.
    In real usage, you'd define a custom live feed or full backtest.
    """
    def __init__(self, execution_engine):
        self.logger = logging.getLogger("BacktraderManager")
        self.execution_engine = execution_engine
        self.cerebro = bt.Cerebro()
        self.symbol_datafeeds = {}
        # add the minimal BT strategy
        self.cerebro.addstrategy(MinimalBTStrategy, execution_engine=self.execution_engine)

    def on_new_bar(self, symbol, timestamp, o, h, l, c, v):
        # If the datafeed for 'symbol' doesn't exist, create it
        if symbol not in self.symbol_datafeeds:
            data = bt.feeds.PandasData(dataname=None, name=symbol)
            self.cerebro.adddata(data, name=symbol)
            self.symbol_datafeeds[symbol] = data

        # We won't do real injection code here, but in practice we'd update the feed
        # Then we forcibly run the next iteration:
        self.cerebro.runstop()
        self.cerebro.run(runonce=False, stdstats=False, optreturn=False)


#
# ----- 4) The unified StrategyAdapter
# 
# This final class is the "unifier" that chooses:
#  - A "Pure Python" approach, or
#  - A "Backtrader" approach,
#  - or references the dictionary of known backtester strategies if needed.
#

class StrategyAdapter:
    """
    If we want to unify in a single file:
    1) We can choose a 'pure_python' or 'backtrader' approach for live usage.
    2) We also keep a dictionary of classes for typical backtests (like MACD, RSI, etc.).
    """

    # This dictionary helps if we want to do direct: StrategyAdapter.STRATEGIES['RSI'] in backtest
    STRATEGIES = {
        'MovingAverageCrossover': MovingAverageCrossoverStrategy,
        'RSI': RSIStrategy,
        'MACD': MACDStrategy,
        'BollingerBands': BollingerBandsStrategy,
        'Momentum': MomentumStrategy
    }

    @staticmethod
    def get_strategy(name):
        if name not in StrategyAdapter.STRATEGIES:
            raise ValueError(
                f"Strategy '{name}' not found. "
                f"Available: {list(StrategyAdapter.STRATEGIES.keys())}"
            )
        return StrategyAdapter.STRATEGIES[name]

    def __init__(self, approach='backtrader', execution_engine=None):
        """
        approach = 'backtrader' or 'pure_python'
        If 'backtrader', we use BacktraderManager to feed bars to a minimal BT strategy
        If 'pure_python', we use PythonSmaStrategy
        """
        self.logger = logging.getLogger("StrategyAdapter")
        self.approach = approach
        self.execution_engine = execution_engine

        if approach == 'backtrader':
            self.impl = BacktraderManager(self.execution_engine)
        else:
            self.impl = PythonSmaStrategy(self.execution_engine)

    def on_new_bar(self, symbol, timestamp, o, h, l, c, v):
        self.impl.on_new_bar(symbol, timestamp, o, h, l, c, v)

