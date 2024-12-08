# components/backtesting_module/strategies.py

import backtrader as bt

class MovingAverageCrossoverStrategy(bt.Strategy):
    params = (
        ('short_window', 10),
        ('long_window', 20),
    )

    def __init__(self):
        self.short_ma = bt.indicators.SMA(
            self.data.close, period=self.params.short_window
        )
        self.long_ma = bt.indicators.SMA(
            self.data.close, period=self.params.long_window
        )
        self.crossover = bt.indicators.CrossOver(self.short_ma, self.long_ma)

    def next(self):
        if self.crossover > 0:
            self.buy()
        elif self.crossover < 0:
            self.sell()

class RSIStrategy(bt.Strategy):
    params = (
        ('rsi_period', 14),
        ('overbought', 70),
        ('oversold', 30),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(
            self.data.close, period=self.params.rsi_period
        )

    def next(self):
        if self.rsi < self.params.oversold and not self.position:
            self.buy()
        elif self.rsi > self.params.overbought and self.position:
            self.sell()

class MACDStrategy(bt.Strategy):
    params = (
        ('fast_period', 12),
        ('slow_period', 26),
        ('signal_period', 9),
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
            self.buy()
        elif self.macd.macd < self.macd.signal and self.position:
            self.sell()

class BollingerBandsStrategy(bt.Strategy):
    params = (
        ('period', 20),
        ('devfactor', 2),
    )

    def __init__(self):
        self.boll = bt.indicators.BollingerBands(
            self.data.close, period=self.params.period, devfactor=self.params.devfactor
        )

    def next(self):
        if self.data.close < self.boll.lines.bot and not self.position:
            self.buy()
        elif self.data.close > self.boll.lines.top and self.position:
            self.sell()

class MomentumStrategy(bt.Strategy):
    params = (
        ('momentum_period', 10),
    )

    def __init__(self):
        self.momentum = bt.indicators.MomentumOscillator(
            self.data.close, period=self.params.momentum_period
        )

    def next(self):
        if self.momentum > 0 and not self.position:
            self.buy()
        elif self.momentum < 0 and self.position:
            self.sell()