# components/data_management_module/utils.py

def append_ticker_to_csv(ticker_symbol, tickers_file_path):
    """Append a new ticker to the tickers.csv file if it doesn't already exist."""
    try:
        with open(tickers_file_path, 'r+') as f:
            tickers = [line.strip() for line in f.readlines()]
            if ticker_symbol in tickers:
                print(f"Ticker {ticker_symbol} already exists in {tickers_file_path}")
                return False  # Indicate that the ticker was not added
            f.write(f"{ticker_symbol}\n")
            print(f"Ticker {ticker_symbol} added to {tickers_file_path}")
            return True  # Indicate that the ticker was successfully added
    except Exception as e:
        print(f"Error appending ticker to CSV: {str(e)}")
        return False
