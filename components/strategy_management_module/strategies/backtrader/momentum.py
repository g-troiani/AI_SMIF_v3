# File: components/strategy_management_module/strategies/backtrader/momentum.py
# Type: py

import backtrader as bt

class MomentumStrategy(bt.Strategy):
    params = (
        ('lookback_period', 20),
        ('threshold', 0),
    )

    def __init__(self):
        pass

    def next(self):
        if len(self.data) > self.p.lookback_period:
            past_price = self.data.close[-self.p.lookback_period]
            current_price = self.data.close[0]
            momentum = (current_price / past_price) - 1.0

            if not self.position and momentum > self.p.threshold:
                self.buy()
            elif self.position and momentum <= self.p.threshold:
                self.close()