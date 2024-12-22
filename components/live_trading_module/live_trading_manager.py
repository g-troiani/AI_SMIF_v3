# components/live_trading_module/live_trading_manager.py

import logging
import threading
from datetime import datetime
import pytz

from components.data_management_module.config import UnifiedConfigLoader, config
from .alpaca_store_streamer import AlpacaStoreStreamerMock
from .zeromq_price_streamer import ZeroMQPriceStreamer
from .live_trading_db import LiveTradingDB

class LiveTradingManager:
    """
    SPRINT 3:
    Attempts to connect to AlpacaStoreStreamerMock if use_alpaca_store = True.
    If it fails, fallback to ZeroMQPriceStreamer.

    Also saves incoming market data to live_trading_data.db via LiveTradingDB.
    """

    def __init__(self, strategy_name):
        self.logger = logging.getLogger('LiveTradingManager')
        self.strategy_name = strategy_name
        self.use_alpaca = UnifiedConfigLoader.use_alpaca_store()
        self.symbols = self._load_symbols()  # In a real scenario, strategies have defined symbols
        self.db = LiveTradingDB()
        self._running = False

    def _load_symbols(self):
        # For demonstration, let's pick all tickers from global config or just one
        tickers_file = config.get('DEFAULT', 'tickers_file')
        with open(tickers_file, 'r') as f:
            symbols = [line.strip() for line in f if line.strip()]
        return symbols

    def start(self):
        self._running = True
        if self.use_alpaca:
            self.logger.info(f"LiveTradingManager for {self.strategy_name}: Trying AlpacaStoreStreamerMock first...")
            try:
                alpaca_streamer = AlpacaStoreStreamerMock(self.symbols)
                alpaca_streamer.start()
                # If no exception, we got alpaca feed running (in real scenario)
                # Let's say in mock it always fails, so we never reach here.
            except Exception as e:
                self.logger.warning(f"AlpacaStore failed: {str(e)}, falling back to ZeroMQ")
                self._start_zeromq_fallback()
        else:
            self.logger.info(f"LiveTradingManager for {self.strategy_name}: Alpaca store not enabled. Using ZeroMQ fallback directly.")
            self._start_zeromq_fallback()

    def _start_zeromq_fallback(self):
        # Use ZeroMQPriceStreamer
        topic = config.get('DEFAULT', 'zeromq_topic')
        port = config.get('DEFAULT', 'zeromq_port')
        self.zeromq_streamer = ZeroMQPriceStreamer(topic, port)
        self.thread = threading.Thread(target=self.zeromq_streamer.start, args=(self._on_market_data,), daemon=True)
        self.thread.start()
        self.logger.info(f"LiveTradingManager for {self.strategy_name}: ZeroMQ fallback live data started")


    def _on_market_data(self, symbol, timestamp, o, h, l, c, v):
        # Save to live_trading_data.db
        self.db.save_market_data_point(symbol, timestamp, o, h, l, c, v)
        # In real scenario, also run live strategy logic here (not implemented)
        # Additional logic for live strategy would go here
        # Could add logs for each data point, but that might be too verbose. Let's trust this minimal logging.

    def stop(self):
        self._running = False
        if hasattr(self, 'zeromq_streamer'):
            self.zeromq_streamer.stop()
        self.logger.info(f"LiveTradingManager for {self.strategy_name} stopped")

