# File: components/strategy_management_module/strategies/backtrader/macd.py
# Type: py

import backtrader as bt

class MACDStrategy(bt.Strategy):
    params = (
        ('fast_period', 12),
        ('slow_period', 26),
        ('signal_period', 9),
    )

    def __init__(self):
        self.macd = bt.ind.MACD(
            self.data.close,
            period_me1=self.p.fast_period,
            period_me2=self.p.slow_period,
            period_signal=self.p.signal_period
        )

    def next(self):
        if self.macd.macd[0] > self.macd.signal[0] and not self.position:
            self.buy()
        elif self.macd.macd[0] < self.macd.signal[0] and self.position:
            self.close()