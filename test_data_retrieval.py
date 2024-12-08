import os
import pandas as pd
from datetime import datetime

# Setup
if not os.path.exists('data'):
    os.makedirs('data')

# Create test tickers file
pd.DataFrame({'ticker': ['AAPL']}).to_csv('data/tickers.csv', index=False)

# Test basic data loading
try:
    print("Testing data loading...")
    df = pd.read_csv('data/tickers.csv')
    print("\nLoaded tickers:")
    print(df)
    
    print("\nTesting date handling...")
    current_date = datetime.now()
    print(f"Current date: {current_date}")
    
    print("\nBasic functionality test completed successfully!")

except Exception as e:
    print(f"Error during testing: {e}")
    import traceback
    print(traceback.format_exc())

finally:
    # Cleanup test files if needed
    if os.path.exists('data/tickers.csv'):
        os.remove('data/tickers.csv')