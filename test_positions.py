# test_positions.py

import requests
import json
from datetime import datetime
import os

def test_positions_api():
    """Test the positions API endpoint with real Alpaca data"""
    
    # 1. First test direct Alpaca API
    print("\n=== Testing Direct Alpaca API ===")
    alpaca_url = "https://paper-api.alpaca.markets/v2/positions"
    alpaca_headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": os.getenv('APCA_API_KEY_ID'),
        "APCA-API-SECRET-KEY": os.getenv('APCA_API_SECRET_KEY')
    }
    
    try:
        alpaca_response = requests.get(alpaca_url, headers=alpaca_headers)
        alpaca_response.raise_for_status()
        alpaca_positions = alpaca_response.json()
        print(f"\nAlpaca API Response Status: {alpaca_response.status_code}")
        print(f"Number of positions: {len(alpaca_positions)}")
        
        if len(alpaca_positions) > 0:
            print("\nSample Position from Alpaca:")
            print(json.dumps(alpaca_positions[0], indent=2))
    except Exception as e:
        print(f"Error accessing Alpaca API: {str(e)}")
        return
    
    # 2. Test our Flask API endpoint
    print("\n=== Testing Our Flask API Endpoint ===")
    flask_url = "http://localhost:5000/api/positions"
    
    try:
        flask_response = requests.get(flask_url)
        flask_response.raise_for_status()
        flask_data = flask_response.json()
        
        print(f"\nFlask API Response Status: {flask_response.status_code}")
        print(f"Success: {flask_data.get('success', False)}")
        
        positions = flask_data.get('positions', [])
        print(f"Number of positions: {len(positions)}")
        
        if len(positions) > 0:
            print("\nSample Position from our API:")
            print(json.dumps(positions[0], indent=2))
            
            # 3. Validate data format
            print("\n=== Validating Data Format ===")
            required_fields = [
                'symbol', 'qty', 'avgEntryPrice', 'marketValue',
                'currentPrice', 'unrealizedPL', 'unrealizedPLPercent'
            ]
            
            missing_fields = [field for field in required_fields if field not in positions[0]]
            if missing_fields:
                print(f"Warning: Missing fields: {missing_fields}")
            else:
                print("All required fields present")
            
            # 4. Compare with Alpaca data
            print("\n=== Comparing with Alpaca Data ===")
            flask_symbols = set(pos['symbol'] for pos in positions)
            alpaca_symbols = set(pos['symbol'] for pos in alpaca_positions)
            
            if flask_symbols == alpaca_symbols:
                print("Position symbols match between Alpaca and our API")
            else:
                print("Warning: Symbol mismatch!")
                print(f"Only in Alpaca: {alpaca_symbols - flask_symbols}")
                print(f"Only in our API: {flask_symbols - alpaca_symbols}")
                
            # 5. Performance check
            for position in positions:
                try:
                    symbol = position['symbol']
                    alpaca_position = next(pos for pos in alpaca_positions if pos['symbol'] == symbol)
                    
                    # Compare key values
                    qty_match = float(alpaca_position['qty']) == float(position['qty'])
                    price_match = abs(float(alpaca_position['current_price']) - float(position['currentPrice'])) < 0.01
                    
                    if not (qty_match and price_match):
                        print(f"\nWarning: Data mismatch for {symbol}:")
                        print(f"Qty match: {qty_match}")
                        print(f"Price match: {price_match}")
                except Exception as e:
                    print(f"Error comparing position for {symbol}: {str(e)}")
                    
    except Exception as e:
        print(f"Error accessing Flask API: {str(e)}")
        return
        
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    print(f"Starting positions API test at {datetime.now()}")
    test_positions_api()