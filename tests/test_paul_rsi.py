import pandas as pd
import backtrader as bt
import sqlite3
from datetime import datetime
from components.backtesting_module.backtrader.strategies import PAUL_RSIStrategy  

class PAUL_RSIStrategyTest:
    def __init__(self, datafile, fromdate=None, todate=None):
        self.datafile = datafile
        self.fromdate = fromdate
        self.todate = todate

    def run(self):
        # Connect to the SQLite database
        conn = sqlite3.connect(self.datafile)
        try:
            # Query the historical_data table
            df = pd.read_sql_query("SELECT * FROM historical_data", conn)
        finally:
            conn.close()

        # Convert timestamp column to datetime and use it as the index
        df['datetime'] = pd.to_datetime(df['timestamp'])
        df.set_index('datetime', inplace=True)

        # Optional: Filter by ticker if multiple symbols exist and you need only one
        # df = df[df['ticker_symbol'] == 'SPY']  # Example filter

        # If date range filtering is required:
        if self.fromdate:
            df = df[df.index >= pd.to_datetime(self.fromdate)]
        if self.todate:
            df = df[df.index <= pd.to_datetime(self.todate)]

        # Create Backtrader data feed
        data = bt.feeds.PandasData(
            dataname=df,
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            datetime=None  # Since index is already datetime
        )

        cerebro = bt.Cerebro()
        cerebro.addstrategy(PAUL_RSIStrategy)
        cerebro.adddata(data)
        cerebro.broker.set_cash(100000)  # Set starting cash as needed

        # Run the backtest
        results = cerebro.run()
        cerebro.plot()

if __name__ == "__main__":
    # Update the path to your actual database file
    db_file = "data/market_data.db"
    tester = PAUL_RSIStrategyTest(datafile=db_file, fromdate="2020-12-10", todate="2024-12-11")
    tester.run()
