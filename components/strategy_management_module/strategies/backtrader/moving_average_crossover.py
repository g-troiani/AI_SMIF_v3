# File: components/strategy_management_module/strategies/backtrader/moving_average_crossover.py
# Type: py

import backtrader as bt

class MovingAverageCrossoverStrategy(bt.Strategy):
    params = (
        ('short_window', 40),
        ('long_window', 100),
    )

    def __init__(self):
        self.short_sma = bt.ind.SMA(self.data.close, period=self.p.short_window)
        self.long_sma = bt.ind.SMA(self.data.close, period=self.p.long_window)

    def next(self):
        if not self.position and self.short_sma[0] > self.long_sma[0]:
            self.buy()
        elif self.position and self.short_sma[0] < self.long_sma[0]:
            self.close()
