# File: components/backtesting_module/backtrader/strategy_adapters.py
# Type: py

import backtrader as bt


from .strategies import (
    MovingAverageCrossoverStrategy,
    RSIStrategy,
    MACDStrategy,
    BollingerBandsStrategy,
    MomentumStrategy,
    PAUL_RSIStrategy,
)


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
            if self.params.stop_loss and self.params.take_profit and self.params.stop_loss > 0 and self.params.take_profit > 0:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.crossover < 0 and self.position:
            self.close()

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
            if self.params.stop_loss and self.params.take_profit and self.params.stop_loss > 0 and self.params.take_profit > 0:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.rsi > self.params.overbought and self.position:
            self.close()

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
            if self.params.stop_loss and self.params.take_profit and self.params.stop_loss > 0 and self.params.take_profit > 0:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.macd.macd < self.macd.signal and self.position:
            self.close()

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
            if self.params.stop_loss and self.params.take_profit and self.params.stop_loss > 0 and self.params.take_profit > 0:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.data.close[0] > self.boll.lines.top[0] and self.position:
            self.close()

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
            if self.params.stop_loss and self.params.take_profit and self.params.stop_loss > 0 and self.params.take_profit > 0:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.momentum[0] < 0 and self.position:
            self.close()

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
        'PAUL_RSIStrategy': PAUL_RSIStrategy,
    }

    @staticmethod
    def get_strategy(name):
        if name not in StrategyAdapter.STRATEGIES:
            raise ValueError(
                f"Strategy '{name}' not found. "
                f"Available strategies: {list(StrategyAdapter.STRATEGIES.keys())}"
            )
        return StrategyAdapter.STRATEGIES[name]
