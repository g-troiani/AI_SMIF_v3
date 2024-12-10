# File: components/strategy_management_module/strategies/backtrader/example_usage.py


import backtrader as bt
import pandas as pd

# Example: Using the MovingAverageCrossoverStrategy
cerebro = bt.Cerebro()

# Load your data into a Pandas DataFrame 'my_pandas_df' with at least ['open','high','low','close','volume']
data = bt.feeds.PandasData(dataname=my_pandas_df)

cerebro.adddata(data)

# Add one of the strategies, for example MACDStrategy
cerebro.addstrategy(MACDStrategy, fast_period=12, slow_period=26, signal_period=9)

cerebro.broker.setcash(10000)
cerebro.broker.setcommission(commission=0.001)

results = cerebro.run()
cerebro.plot()
