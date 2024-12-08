# test_dashboard_metrics.py

import requests
import os
from datetime import datetime

def test_alpaca_metrics():
    """Test fetching dashboard metrics directly from Alpaca"""
    
    # Base URL for paper trading
    base_url = "https://paper-api.alpaca.markets"
    
    # Headers with API credentials
    headers = {
        "APCA-API-KEY-ID": os.getenv('APCA_API_KEY_ID'),
        "APCA-API-SECRET-KEY": os.getenv('APCA_API_SECRET_KEY'),
        "accept": "application/json"
    }
    
    print(f"\n=== Testing Alpaca Metrics at {datetime.now()} ===\n")
    
    try:
        # 1. Test Account Info
        print("1. Testing Account Information:")
        account_response = requests.get(f"{base_url}/v2/account", headers=headers)
        account_response.raise_for_status()
        account = account_response.json()
        
        # Calculate metrics
        equity = float(account['equity'])
        cash = float(account['cash'])
        today_pl = float(account['equity']) - float(account['last_equity'])
        today_return = (today_pl / float(account['last_equity'])) * 100 if float(account['last_equity']) != 0 else 0
        
        print(f"Account Balance: ${equity:,.2f}")
        print(f"Cash Available: ${cash:,.2f}")
        print(f"Today's P/L: ${today_pl:,.2f}")
        print(f"Today's Return: {today_return:.2f}%")
        
        # 2. Test our Flask endpoint
        print("\n2. Testing Flask Dashboard Endpoint:")
        flask_response = requests.get("http://localhost:5000/api/dashboard-data")
        flask_response.raise_for_status()
        flask_data = flask_response.json()
        
        if flask_data.get('success'):
            data = flask_data['data']
            print("\nFlask Endpoint Results:")
            print(f"Account Balance: ${data['account_balance']:,.2f}")
            print(f"Cash Available: ${data['cash_available']:,.2f}")
            print(f"Today's P/L: ${data['today_pl']:,.2f}")
            print(f"Today's Return: {data['today_return']:.2f}%")
            
            # 3. Verify data consistency
            print("\n3. Verifying Data Consistency:")
            print(f"Account Balance matches: {abs(data['account_balance'] - equity) < 0.01}")
            print(f"Cash Available matches: {abs(data['cash_available'] - cash) < 0.01}")
            print(f"Today's P/L matches: {abs(data['today_pl'] - today_pl) < 0.01}")
            print(f"Today's Return matches: {abs(data['today_return'] - today_return) < 0.01}")
        else:
            print(f"Flask endpoint error: {flask_data.get('message')}")
            
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {str(e)}")
    except Exception as e:
        print(f"General Error: {str(e)}")

if __name__ == "__main__":
    if not os.getenv('APCA_API_KEY_ID') or not os.getenv('APCA_API_SECRET_KEY'):
        print("Error: Alpaca API credentials not found in environment variables")
        print("Please set APCA_API_KEY_ID and APCA_API_SECRET_KEY")
        exit(1)
        
    test_alpaca_metrics()