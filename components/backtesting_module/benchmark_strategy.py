# File: components/backtesting_module/benchmark_strategy.py
# Type: py

import backtrader as bt

class BenchmarkStrategy(bt.Strategy):
    """
    Simple buy and hold strategy for benchmark comparison.
    Now updated with optional stop_loss and take_profit.
    """
    params = (
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        self.bought = False

    def next(self):
        if not self.bought:
            entry_price = self.data.close[0]
            # If both stop_loss and take_profit are set, use buy_bracket
            if self.params.stop_loss is not None and self.params.take_profit is not None:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
            self.bought = True
