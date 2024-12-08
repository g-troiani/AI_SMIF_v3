# components/backtesting_module/benchmark_strategy.py

import backtrader as bt

class BenchmarkStrategy(bt.Strategy):
    """
    Simple buy and hold strategy for benchmark comparison.
    """
    
    def __init__(self):
        self.data_close = self.datas[0].close
        self.bought = False
        
    def next(self):
        if not self.bought:
            self.buy()
            self.bought = True