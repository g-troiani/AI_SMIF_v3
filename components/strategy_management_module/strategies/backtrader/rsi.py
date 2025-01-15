# File: components/strategy_management_module/strategies/backtrader/rsi.py
# Type: py

import backtrader as bt

class RSIStrategy(bt.Strategy):
    params = (
        ('period', 14),
        ('overbought', 70),
        ('oversold', 30),
    )

    def __init__(self):
        self.rsi = bt.ind.RSI(self.data.close, period=self.p.period)

    def next(self):
        if not self.position and self.rsi[0] < self.p.oversold:
            self.buy()
        elif self.position and self.rsi[0] > self.p.overbought:
            self.close()