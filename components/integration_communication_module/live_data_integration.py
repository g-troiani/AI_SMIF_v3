import threading
import queue
import json
import time
from datetime import datetime
import backtrader as bt
import websocket

class AlpacaWebSocketClient:
    """
    Connects to Alpaca's data streaming API to receive real-time bars for a given symbol.
    """
    def __init__(self, api_key, api_secret, symbol, endpoint="wss://stream.data.alpaca.markets/v2/iex"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.symbol = symbol
        self.endpoint = endpoint
        self.ws = None
        self.thread = None
        self.data_queue = queue.Queue()
        self.connected = False
        self.authenticated = False

    def _on_open(self, ws):
        # Send auth message
        auth_msg = {
            "action": "auth",
            "key": self.api_key,
            "secret": self.api_secret
        }
        ws.send(json.dumps(auth_msg))
        print("Auth message sent. Waiting for authentication response...")

    def _on_message(self, ws, message):
        msg = json.loads(message)
        for m in msg:
            T = m.get('T')
            
            if T == 'error':
                code = m.get('code')
                err_msg = m.get('msg', 'Unknown error')
                print(f"WebSocket Error: code={code}, message={err_msg}")
                self.ws.close()
                return
            
            if T == 'success':
                # Check for authentication success
                if m.get('msg') == 'authenticated':
                    self.authenticated = True
                    print("Successfully authenticated.")
                    # Subscribe to bars now
                    sub_msg = {
                        "action": "subscribe",
                        "bars": [self.symbol]
                    }
                    ws.send(json.dumps(sub_msg))
                    self.connected = True
                    print(f"Subscribed to {self.symbol} bars.")

            if T == 'subscription':
                print(f"Subscription message: {m}")

            if T == 'b' and m.get('S') == self.symbol:
                bar = {
                    'open': m['o'],
                    'high': m['h'],
                    'low': m['l'],
                    'close': m['c'],
                    'volume': m['v'],
                    'timestamp': m['t']
                }
                self.data_queue.put(bar)

    def _on_error(self, ws, error):
        print("WebSocket Error:", error)

    def _on_close(self, ws, close_status_code, close_msg):
        self.connected = False
        print(f"WebSocket closed: code={close_status_code}, message={close_msg}")

    def start(self):
        self.ws = websocket.WebSocketApp(
            self.endpoint,
            on_message=self._on_message,
            on_open=self._on_open,
            on_error=self._on_error,
            on_close=self._on_close
        )
        self.thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.thread.start()

        # Wait for auth and subscription
        for _ in range(10):
            if self.connected and self.authenticated:
                break
            time.sleep(1)
        if not (self.connected and self.authenticated):
            print("Unable to authenticate or subscribe to data. Check your API keys or subscription.")
            self.stop()
            raise RuntimeError("WebSocket authentication/subscription failed.")

    def stop(self):
        if self.ws:
            self.ws.close()
        if self.thread and self.thread.is_alive():
            self.thread.join()

    def get_queue(self):
        return self.data_queue

class AlpacaLiveDataFeed(bt.feed.DataBase):
    """
    Custom Backtrader DataFeed for live data from Alpaca via a queue.
    """

    def __init__(self, data_queue):
        super().__init__()
        self.data_queue = data_queue
        self.first_bar = True
        self.live = True  # Mark this data feed as live

    def _load(self):
        # Try to get a bar within a short timeout (e.g., 2 seconds)
        # If no bar arrives, return False (no new data but feed still alive)
        try:
            bar = self.data_queue.get(timeout=2)
        except queue.Empty:
            # No bar arrived in 2 seconds. Return False to indicate
            # no data now, but we’re still live and waiting for future bars.
            return False

        # If we got here, we have a bar
        dt = datetime.fromisoformat(bar['timestamp'].replace("Z", "+00:00"))
        self.lines.datetime[0] = bt.date2num(dt)
        self.lines.open[0] = bar['open']
        self.lines.high[0] = bar['high']
        self.lines.low[0] = bar['low']
        self.lines.close[0] = bar['close']
        self.lines.volume[0] = bar['volume']
        self.lines.openinterest[0] = 0

        if self.first_bar:
            print("Received first bar, live data started.")
            self.first_bar = False

        return True  # Indicate we loaded a new bar


def setup_live_data_cerebro(api_key, api_secret, symbol, strategy, strategy_params=None):
    """
    Sets up Backtrader to run a live strategy using Alpaca's WebSocket data feed.
    """
    if strategy_params is None:
        strategy_params = {}

    # Start the WebSocket client
    ws_client = AlpacaWebSocketClient(api_key, api_secret, symbol)
    ws_client.start()
    data_queue = ws_client.get_queue()

    # Create Backtrader Cerebro
    cerebro = bt.Cerebro()

    # Disable runonce optimization so we process bars as they come
    cerebro.run(runonce=False)

    # Create and add the live data feed
    data_feed = AlpacaLiveDataFeed(data_queue=data_queue)
    data_feed._name = symbol
    data_feed.live = True
    cerebro.adddata(data_feed)

    # Add the user-defined strategy
    cerebro.addstrategy(strategy, **strategy_params)

    return cerebro, ws_client
