# File: generate_modeling_data.py

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import os

# ---------------------
# CONFIGURATION
# ---------------------

MARKET_DB_PATH = 'data/market_data.db'
MODELING_DB_PATH = 'data/modeling_data.db'
WINDOW = 14  # rolling window size for features

# Optional: Path to external features CSV, e.g. inflation data
# This CSV should have a "date" column and one or more feature columns.
# Date should be parsable into a datetime, and presumably daily frequency.
EXTERNAL_DATA_CSV = 'data/external_features.csv'  # Update or comment if not available.

# ---------------------
# LOAD EXTERNAL DATA (Optional)
# ---------------------

external_data = None
if os.path.exists(EXTERNAL_DATA_CSV):
    external_data = pd.read_csv(EXTERNAL_DATA_CSV)
    # Ensure 'date' is in datetime format and set as index if appropriate
    if 'date' in external_data.columns:
        external_data['date'] = pd.to_datetime(external_data['date'])
        external_data.set_index('date', inplace=True)
    else:
        print("No 'date' column found in external data. External features won't be merged.")
        external_data = None

# ---------------------
# CREATE MODELING DB SCHEMA
# ---------------------

# We will create a table `modeling_data` with the following columns:
# ticker_symbol, timestamp, open, high, low, close, volume,
# return, vol, mom, sma, rolling_min, rolling_max, diff_close,
# plus any external features.

# Connect to the modeling database
conn_modeling = sqlite3.connect(MODELING_DB_PATH)
cur_modeling = conn_modeling.cursor()

# Drop table if it exists (optional)
cur_modeling.execute("DROP TABLE IF EXISTS modeling_data;")

# Build the schema dynamically. We'll have a base schema plus columns for external data if available.
base_schema = """
    CREATE TABLE modeling_data (
        ticker_symbol TEXT,
        timestamp DATETIME,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER,
        return REAL,
        vol REAL,
        mom REAL,
        sma REAL,
        rolling_min REAL,
        rolling_max REAL,
        diff_close REAL
"""

if external_data is not None:
    # Add external columns dynamically
    for col in external_data.columns:
        # Skip the index if it ended up in the columns for some reason
        if col == 'date':
            continue
        # We'll store external features as REAL for numeric and TEXT otherwise
        # Attempt conversion: if column is numeric, use REAL; else TEXT
        if pd.api.types.is_numeric_dtype(external_data[col]):
            base_schema += f", {col} REAL"
        else:
            base_schema += f", {col} TEXT"

base_schema += ", PRIMARY KEY (ticker_symbol, timestamp)) WITHOUT ROWID;"

cur_modeling.execute(base_schema)
conn_modeling.commit()

# ---------------------
# EXTRACT DATA FROM MARKET_DATA.DB
# ---------------------

conn_market = sqlite3.connect(MARKET_DB_PATH)

# Get tickers
tickers_df = pd.read_sql_query("SELECT symbol FROM tickers;", conn_market)
tickers = tickers_df['symbol'].tolist()

for ticker in tickers:
    print(f"Processing {ticker}...")
    
    # Get historical data for this ticker
    query = f"""
        SELECT ticker_symbol, timestamp, open, high, low, close, volume
        FROM historical_data
        WHERE ticker_symbol = '{ticker}'
        ORDER BY timestamp ASC
    """
    data = pd.read_sql_query(query, conn_market, parse_dates=['timestamp'])
    if data.empty:
        print(f"No data for {ticker}, skipping.")
        continue
    
    data.set_index('timestamp', inplace=True)
    
    # ---------------------
    # FEATURE ENGINEERING
    # ---------------------
    
    # For returns, we use log returns of close prices:
    data['return'] = np.log(data['close'] / data['close'].shift(1))
    
    # Rolling volatility (std of returns over WINDOW)
    data['vol'] = data['return'].rolling(WINDOW).std()
    
    # Momentum (sign of rolling mean of returns)
    data['mom'] = np.sign(data['return'].rolling(WINDOW).mean())
    
    # Simple Moving Average (SMA) of close
    data['sma'] = data['close'].rolling(WINDOW).mean()
    
    # Rolling minimum and maximum of close
    data['rolling_min'] = data['close'].rolling(WINDOW).min()
    data['rolling_max'] = data['close'].rolling(WINDOW).max()
    
    # Differencing close price
    data['diff_close'] = data['close'].diff()
    
    # Drop rows with NaN due to rolling calculations
    data.dropna(inplace=True)
    
    # ---------------------
    # MERGE EXTERNAL DATA (Optional)
    # ---------------------
    # We'll merge on date (day-level). If external_data is daily and data is min-level, we might need to align.
    # We assume external_data is daily and data could be intraday. We'll merge by date only.
    if external_data is not None:
        # Extract just the date from the timestamp
        # Align external data by date. For intraday data, external features are same for that entire date.
        data['date'] = data.index.date
        # Convert data['date'] back to datetime to align with external_data's index
        data['date'] = pd.to_datetime(data['date'])
        
        # Join external features by date
        data = data.merge(external_data, how='left', left_on='date', right_index=True)
        data.drop(columns=['date'], inplace=True)
    
    # ---------------------
    # WRITE TO MODELING DB
    # ---------------------
    
    # Add back the ticker_symbol as a column
    data['ticker_symbol'] = ticker
    # Move it from index to columns
    data.reset_index(inplace=True)
    
    # Insert into modeling_data
    # We'll use Pandas to_sql for convenience
    # If external_data columns have text/numeric mixture, all handled by pandas
    data.to_sql('modeling_data', conn_modeling, if_exists='append', index=False)

print("All done. The modeling_data.db is ready.")

# Close connections
conn_market.close()
conn_modeling.close()
