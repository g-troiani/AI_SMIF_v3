# File: components/strategy_management_module/strategies/backtrader/strategy_base.py
# Type: py

import backtrader as bt

class MyBaseStrategy(bt.Strategy):
    params = ()

    def __init__(self):
        pass

    def next(self):
        pass