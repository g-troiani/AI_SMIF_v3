# File: installed_backtrader.py

import backtrader as bt
import yfinance as yf
from datetime import datetime
import pandas as pd

def get_stock_data(symbol, start_date, end_date):
    print(f"Downloading data for {symbol}...")
    # Download data
    data = yf.download(symbol, start=start_date, end=end_date, progress=False)
    
    print("\nRaw data head:")
    print(data.head())
    
    # Reset index and clean up the data structure
    data = data.reset_index()
    
    # Convert the datetime column to string format
    data['Date'] = pd.to_datetime(data['Date']).dt.strftime('%Y-%m-%d')
    
    # Ensure we have simple column names without multi-level structure
    data.columns = [str(col).replace(' ', '') for col in data.columns]
    
    # Save to CSV with clean structure
    csv_file = f'{symbol}_clean.csv'
    data.to_csv(csv_file, index=False)
    
    # Debug print - verify the saved file
    print(f"\nFirst few lines of saved CSV file {csv_file}:")
    with open(csv_file, 'r') as f:
        for i, line in enumerate(f):
            if i < 5:
                print(line.strip())
    
    return csv_file

class TestStrategy(bt.Strategy):
    def next(self):
        pass

def run_backtest(csv_file, start_date, end_date):
    print("\nInitializing Backtrader...")
    cerebro = bt.Cerebro()
    cerebro.addstrategy(TestStrategy)
    
    # Create data feed with explicit parameters
    data_feed = bt.feeds.GenericCSVData(
        dataname=csv_file,
        fromdate=start_date,
        todate=end_date,
        nullvalue=0.0,
        dtformat='%Y-%m-%d',
        datetime=0,      # Date column
        open=1,          # Open price column
        high=2,          # High price column
        low=3,           # Low price column
        close=4,         # Close price column
        volume=5,        # Volume column
        adjclose=6,      # Adjusted Close column
        headers=True     # Skip the header row
    )
    
    cerebro.adddata(data_feed)
    
    print("\nRunning backtest...")
    cerebro.run()
    
   # print("\nPlotting results...")
   # cerebro.plot()

def verify_csv_format(filename):
    print(f"\nVerifying CSV file format for {filename}:")
    df = pd.read_csv(filename)
    print("\nDataFrame info:")
    print(df.info())
    print("\nFirst few rows:")
    print(df.head())
    return df

if __name__ == '__main__':
    # Set parameters
    SYMBOL = 'AAPL'
    START_DATE = '2020-01-01'
    END_DATE = '2020-12-31'
    
    # Convert string dates to datetime objects for Backtrader
    start_date = datetime.strptime(START_DATE, '%Y-%m-%d')
    end_date = datetime.strptime(END_DATE, '%Y-%m-%d')
    
    try:
        # Get and prepare the data
        csv_file = get_stock_data(SYMBOL, START_DATE, END_DATE)
        
        # Verify the CSV format
        print("\nVerifying data format:")
        df = verify_csv_format(csv_file)
        
        # Run the backtest
        run_backtest(csv_file, start_date, end_date)
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()