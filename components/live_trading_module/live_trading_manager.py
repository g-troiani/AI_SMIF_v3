# File: components/live_trading_module/live_trading_manager.py

import logging
import threading
import time
from datetime import datetime, timedelta
import pytz

from components.data_management_module.config import UnifiedConfigLoader, config
from .alpaca_store_streamer import AlpacaStoreStreamerMock
from .zeromq_price_streamer import ZeroMQPriceStreamer
from .live_trading_db import LiveTradingDB

class LiveTradingManager:
    """
    SPRINT 3 + Enhanced:
    - Attempts to connect to AlpacaStoreStreamerMock if use_alpaca_store = True.
    - If it fails, fallback to ZeroMQPriceStreamer.
    - Saves incoming market data to live_trading_data.db via LiveTradingDB.
    - Persists live strategy status across restarts.
    - Includes basic reconnection logic for both Alpaca and ZeroMQ fallback.
    - Tries to fill data gaps by checking last timestamp from DB and fetching the missed range.
      (For demonstration, we add minimal approach; in practice you'd define the method more robustly).
    """

    def __init__(self, strategy_name):
        self.logger = logging.getLogger('LiveTradingManager')
        self.strategy_name = strategy_name

        self.use_alpaca = UnifiedConfigLoader.use_alpaca_store()
        self.symbols = self._load_symbols()  # In a real scenario, strategies have defined symbols
        self.db = LiveTradingDB()

        self._running = False
        self._alpaca_streamer = None
        self.zeromq_streamer = None
        self._zeromq_thread = None

        # Check if this strategy was live previously (persisted in DB).
        # If so, we set up a small flag so we automatically resume if not forcibly stopped.
        was_live = self.db.is_strategy_live(self.strategy_name)
        if was_live:
            self.logger.info(f"Strategy '{self.strategy_name}' was previously LIVE. Will auto-resume.")
        else:
            self.logger.info(f"Strategy '{self.strategy_name}' not marked as live in DB. "
                             f"You can start() it manually or set is_live=1 in DB.")

        self.auto_resume = was_live  # If True, we will auto-start on init.

    def _load_symbols(self):
        """
        For demonstration, let's pick all tickers from global config or just one.
        """
        tickers_file = config.get('DEFAULT', 'tickers_file')
        with open(tickers_file, 'r') as f:
            symbols = [line.strip() for line in f if line.strip()]
        return symbols

    def start(self, force_live=False):
        """
        Start the live trading manager.
        If force_live=True, we forcibly mark this strategy as live in the DB even if it wasn't before.
        Otherwise, if auto_resume is True or if the user calls start() manually, we proceed.
        """
        if not force_live and not self.auto_resume:
            self.logger.info(f"Strategy '{self.strategy_name}' is not flagged as live. "
                             f"Call start(force_live=True) if you want to forcibly make it live.")
            return

        # Mark in DB that this strategy is live, so after restarts we remain live.
        self.db.set_strategy_live(self.strategy_name, True)

        self._running = True
        self.logger.info(f"Starting LiveTradingManager for {self.strategy_name}, use_alpaca={self.use_alpaca}")

        # Attempt to fill data gap if any
        self._fetch_missed_data()

        if self.use_alpaca:
            self.logger.info(f"Trying AlpacaStoreStreamerMock first for '{self.strategy_name}'...")
            try:
                self._start_alpaca_streamer()
            except Exception as e:
                self.logger.warning(f"AlpacaStore failed: {str(e)}, falling back to ZeroMQ")
                self._start_zeromq_fallback()
        else:
            self.logger.info(f"Alpaca store not enabled for '{self.strategy_name}'. Using ZeroMQ fallback directly.")
            self._start_zeromq_fallback()

    def _start_alpaca_streamer(self):
        """
        Start the Alpaca streamer in a background thread (mock for now),
        with a reconnection approach if it fails mid-run.
        """
        # We'll define a local worker method that tries to connect until success or stop.
        def alpaca_worker():
            while self._running:
                try:
                    self._alpaca_streamer = AlpacaStoreStreamerMock(self.symbols, self._on_market_data)
                    self._alpaca_streamer.start()
                    # If it returns, it means it ended or raised. We can break or re-try.
                    self.logger.warning("Alpaca streamer ended or raised. Attempting reconnection after 15s.")
                    time.sleep(15)  # Wait, then re-try if still self._running
                except Exception as e:
                    self.logger.error(f"Alpaca streamer exception: {e}. Retrying in 15s...")
                    time.sleep(15)
                    # If we fail repeatedly, we might fallback. But let's keep it indefinite for demonstration.
                    # If you want an actual fallback after X tries, you can implement that logic.
                    if not self._running:
                        break

        # Start background thread
        self._alpaca_thread = threading.Thread(target=alpaca_worker, daemon=True)
        self._alpaca_thread.start()
        self.logger.info("Alpaca streamer thread started.")

    def _start_zeromq_fallback(self):
        """
        Use ZeroMQPriceStreamer in a background thread with auto reconnection
        if it fails. 
        """
        topic = config.get('DEFAULT', 'zeromq_topic')
        port = config.get('DEFAULT', 'zeromq_port')
        self.logger.info(f"Using ZeroMQ fallback for '{self.strategy_name}', topic={topic}, port={port}")

        def zeromq_worker():
            while self._running:
                try:
                    self.zeromq_streamer = ZeroMQPriceStreamer(topic, port)
                    self.zeromq_streamer.start(self._on_market_data)
                    self.logger.warning("ZeroMQ streamer ended or raised. Attempting reconnection after 10s.")
                    time.sleep(10)
                except Exception as e:
                    self.logger.error(f"ZeroMQ streamer exception: {e}. Retrying in 10s...")
                    time.sleep(10)
                    if not self._running:
                        break

        self._zeromq_thread = threading.Thread(target=zeromq_worker, daemon=True)
        self._zeromq_thread.start()
        self.logger.info(f"ZeroMQ fallback streaming started for '{self.strategy_name}'")

    def _on_market_data(self, symbol, timestamp, o, h, l, c, v):
        # Save to live_trading_data.db
        self.db.save_market_data_point(symbol, timestamp, o, h, l, c, v)

        # Potentially, also run live strategy logic here (not implemented).
        # Example:
        #   if self.my_strategy:
        #       self.my_strategy.on_bar(symbol, timestamp, o, h, l, c, v)

    def _fetch_missed_data(self):
        """
        Attempt to find the last known timestamp from DB for each symbol,
        then fetch from that timestamp until now, so we fill in any data gap
        that might have occurred while we were offline.
        (Pseudo code, a placeholder approach - you can implement real logic 
         if you have an API to fetch back data.)
        """
        # For each symbol, look up last timestamp from DB:
        now = datetime.now(pytz.timezone('America/New_York'))
        for sym in self.symbols:
            last_ts = self.db.get_last_market_timestamp(sym)  # Suppose we have a DB function
            if last_ts:
                delta = now - last_ts
                if delta > timedelta(minutes=1):
                    # we pretend to fetch historical bars from last_ts to now
                    # store them in DB (just logging for demonstration)
                    self.logger.info(f"Would fetch missed data for {sym} from {last_ts} to {now}")
                    # E.g. call data fetch function from data_manager or something
                else:
                    self.logger.debug(f"No significant gap for {sym}, last recorded {last_ts}")
            else:
                self.logger.info(f"No prior timestamp found for {sym}, skipping retroactive fetch")

    def stop(self):
        """
        Gracefully stop streaming and mark strategy as not live in the DB.
        """
        self._running = False
        self.db.set_strategy_live(self.strategy_name, False)
        # If we had an Alpaca streamer thread:
        if hasattr(self, '_alpaca_streamer') and self._alpaca_streamer is not None:
            self._alpaca_streamer.stop()
        if hasattr(self, '_alpaca_thread') and self._alpaca_thread and self._alpaca_thread.is_alive():
            self.logger.info("Waiting for Alpaca thread to finish...")
            self._alpaca_thread.join(timeout=5)

        if self.zeromq_streamer:
            self.zeromq_streamer.stop()
        if self._zeromq_thread and self._zeromq_thread.is_alive():
            self.logger.info("Waiting for ZeroMQ fallback thread to finish...")
            self._zeromq_thread.join(timeout=5)

        self.logger.info(f"LiveTradingManager for {self.strategy_name} fully stopped.")
