# components/live_trading_module/alpaca_store_streamer.py

import time
import logging

class AlpacaStoreStreamerMock:
    """
    Sprint 3:
    Mock streamer to simulate AlpacaStore.
    For demonstration, let's say it always raises an exception to force fallback.
    In a real scenario, this would connect to Alpaca Live Stream.
    """
    def __init__(self, symbols):
        self.logger = logging.getLogger("AlpacaStoreStreamerMock")
        self.symbols = symbols
        self._running = False

    def start(self):
        self.logger.info("Attempting to start AlpacaStoreStreamerMock...")
        time.sleep(2)
        # Simulate failure
        raise RuntimeError("AlpacaStore connection failed")

    def stop(self):
        if self._running:
            self._running = False
            self.logger.info("Stopped AlpacaStoreStreamerMock")
