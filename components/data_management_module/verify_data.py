import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import pytz

def verify_data():
    # Connect to the database
    conn = sqlite3.connect('data/data.db')
    
    # Check tables
    print("\nTables in database:")
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
    print(tables)
    
    # Check tickers
    print("\nTickers in database:")
    tickers = pd.read_sql_query("SELECT * FROM tickers;", conn)
    print(tickers)
    
    # For each ticker, check the latest data
    for ticker in tickers['symbol']:
        print(f"\nLatest data for {ticker}:")
        query = f"""
        SELECT * FROM historical_data 
        WHERE ticker_symbol = '{ticker}' 
        ORDER BY timestamp DESC 
        LIMIT 5;
        """
        latest_data = pd.read_sql_query(query, conn)
        print(latest_data)
        
        # Check data frequency
        print(f"\nData frequency check for {ticker} (last 24 hours):")
        query = f"""
        SELECT COUNT(*) as count, 
               strftime('%Y-%m-%d %H', timestamp) as hour
        FROM historical_data 
        WHERE ticker_symbol = '{ticker}'
        AND timestamp > datetime('now', '-1 day')
        GROUP BY hour
        ORDER BY hour DESC;
        """
        frequency = pd.read_sql_query(query, conn)
        print(frequency)
    
    conn.close()

if __name__ == "__main__":
    verify_data()