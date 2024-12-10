# File: components/strategy_management_module/strategies/backtrader/bollinger_bands.py
# Type: py

import backtrader as bt

class BollingerBandsStrategy(bt.Strategy):
    params = (
        ('window', 20),
        ('num_std', 2.0),
    )

    def __init__(self):
        self.bbands = bt.ind.BollingerBands(self.data.close, period=self.p.window, devfactor=self.p.num_std)

    def next(self):
        if not self.position and self.data.close[0] < self.bbands.lines.bot[0]:
            self.buy()
        elif self.position and self.data.close[0] > self.bbands.lines.top[0]:
            self.close()