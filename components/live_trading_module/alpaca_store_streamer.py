# File: components/live_trading_module/alpaca_store_streamer.py

import logging
import alpaca_trade_api as tradeapi
import threading
import time

logger = logging.getLogger("AlpacaStoreStreamer")

class BarData:
    def __init__(self, symbol, close, datetime):
        self.symbol = symbol
        self.close = [close]  # to mimic backtrader bar structure
        self.datetime = [datetime]

class AlpacaStoreStreamer:
    """
    Connects to Alpaca's real-time data feed at a chosen timeframe. 
    If an error occurs mid-run, it calls on_error_callback or tries reconnect.
    """

    def __init__(self, symbols, timeframe, on_bar_callback, on_error_callback=None):
        self.logger = logger
        self.symbols = symbols
        self.timeframe = timeframe
        self.on_bar_callback = on_bar_callback
        self.on_error_callback = on_error_callback
        self._running = False
        self.stream = None
        self._thread = None
        self._reconnection_attempts = 0
        self._max_reconnection_attempts = 5
        self._reconnect_delay = 5

    def start(self):
        self.logger.info(f"Starting AlpacaStoreStreamer with timeframe={self.timeframe} for symbols={self.symbols}")
        self._running = True
        self._start_stream()

    def _start_stream(self):
        try:
            self.stream = tradeapi.Stream(
                key_id='...',  # replaced by env
                secret_key='...', 
                base_url='https://paper-api.alpaca.markets',
                data_feed='sip'
            )
            for symbol in self.symbols:
                self.stream.subscribe_bars(self._handle_incoming_bar, symbol)

            self._thread = threading.Thread(target=self._run_stream, daemon=True)
            self._thread.start()
        except Exception as e:
            self.logger.error(f"Alpaca streamer exception at start: {e}")
            self._try_reconnect(e)

    def _run_stream(self):
        try:
            self.logger.info("Alpaca streamer thread running")
            self.stream.run()
        except Exception as e:
            self.logger.error(f"Alpaca streamer runtime exception: {e}")
            if self._running:
                self._try_reconnect(e)

    def _handle_incoming_bar(self, bar):
        if not self._running:
            return
        # create a BarData object
        bar_data = BarData(
            symbol=bar.symbol,
            close=bar.close,
            datetime=bar.timestamp
        )
        self.on_bar_callback(bar_data)

    def _try_reconnect(self, exc):
        self._reconnection_attempts += 1
        if self._reconnection_attempts > self._max_reconnection_attempts:
            self.logger.error("Max reconnection attempts reached. Giving up.")
            if self.on_error_callback:
                self.on_error_callback(exc)
            return
        self.logger.warning(f"Attempting to reconnect in {self._reconnect_delay}s (attempt {self._reconnection_attempts})")
        time.sleep(self._reconnect_delay)
        if not self._running:
            return
        self._start_stream()

    def stop(self):
        self.logger.info("Stopping AlpacaStoreStreamer")
        self._running = False
        if self.stream:
            try:
                self.stream.close()
            except Exception:
                pass
        if self._thread and self._thread.is_alive():
            self._thread.join()
        self.logger.info("AlpacaStoreStreamer stopped")
