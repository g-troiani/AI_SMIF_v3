import os
import requests
import json

# Set up your Alpaca API credentials as environment variables before running:
# export APCA_API_KEY_ID="your_key_id"
# export APCA_API_SECRET_KEY="your_secret_key"

headers = {
    "APCA-API-KEY-ID": os.getenv('APCA_API_KEY_ID', ''),
    "APCA-API-SECRET-KEY": os.getenv('APCA_API_SECRET_KEY', ''),
    "accept": "application/json"
}

try:
    url = "https://data.alpaca.markets/v2/stocks/GLD/snapshot?feed=sip"
    print("Requesting URL:", url)
    response = requests.get(url, headers=headers)
    print("Status Code:", response.status_code)
    print("Response Headers:", response.headers)
    print("Raw Response Content:", response.text)
    response.raise_for_status()

    data = response.json()
    print("Parsed JSON:", json.dumps(data, indent=2))
    snapshot = data.get('snapshot', {})
    print("Snapshot Data:", json.dumps(snapshot, indent=2))

    latest_trade = snapshot.get('latestTrade', {})
    daily_bar = snapshot.get('dailyBar', {})

    print("Latest Trade:", json.dumps(latest_trade, indent=2))
    print("Daily Bar:", json.dumps(daily_bar, indent=2))

    # Use either the latest trade price or the daily bar close price directly.
    # No fallback to zero.
    current_price = latest_trade.get('p') if 'p' in latest_trade else daily_bar.get('c')

    print("Current Price of GLD:", current_price)

except requests.exceptions.RequestException as e:
    print("Error fetching data:", e)
