# File: components/live_trading_module/live_trading_manager.py

import logging
import threading
import time
import sqlite3
from datetime import datetime, timedelta
import pytz

from components.data_management_module.config import UnifiedConfigLoader, config
from components.backtesting_module.strategy_adapters import StrategyAdapter
from components.trading_execution_engine.execution_engine import ExecutionEngine
from components.trading_execution_engine.trade_signal import TradeSignal
from .alpaca_store_streamer import AlpacaStoreStreamer
from .zeromq_price_streamer import ZeroMQPriceStreamer
from .live_trading_db import LiveTradingDB

DB_PATH = config.project_root / 'data' / 'backtesting_results.db' 
logger = logging.getLogger(__name__)

# File: components/live_trading_module/live_trading_manager.py

class Bar:
    """
    Minimal bar class with full OHLCV fields.
    The aggregator or streamer will produce this bar with:
     - symbol
     - open, high, low, close
     - volume
     - timestamp
    """

    def __init__(self, symbol, open_p, high_p, low_p, close_p, volume, timestamp):
        self.symbol = symbol
        self.open = open_p
        self.high = high_p
        self.low = low_p
        self.close = close_p
        self.volume = volume
        self.timestamp = timestamp

# File: components/live_trading_module/live_trading_manager.py

class SimpleAggregator:
    """
    Minimal aggregator that groups bars to produce a higher timeframe OHLCV bar.
    If timeframe=5 => we group 5 bars of 1Min => produce a single bar:
       open = 1st bar's open
       high = max of all bars' highs
       low  = min of all bars' lows
       close= last bar's close
       volume = sum of all bars' volumes
       timestamp = last bar's timestamp
    If timeframe=1 => pass them as is (i.e. aggregator just returns the same bar).
    """

    def __init__(self, target_interval=5):
        self.target_interval = target_interval
        # dictionary symbol -> list of partial bars
        self.cache = {}

    def process(self, bar_1m):
        """
        Accept a 1Min bar, and accumulate it in the cache.
        If we reach 'target_interval' bars, we merge them to produce one aggregated bar.
        Returns that new bar if formed, else None.
        """

        symbol = bar_1m.symbol
        if symbol not in self.cache:
            self.cache[symbol] = []

        # Append the new bar
        self.cache[symbol].append(bar_1m)

        # If we have enough bars to form a higher timeframe
        if len(self.cache[symbol]) >= self.target_interval:
            bars = self.cache[symbol]
            # Merge logic
            merged_open = bars[0].open
            merged_high = max(b.high for b in bars)
            merged_low  = min(b.low  for b in bars)
            merged_close = bars[-1].close
            merged_volume = sum(b.volume for b in bars)
            merged_timestamp = bars[-1].timestamp

            # Clear the cache for next cycle
            self.cache[symbol] = []

            # Return the new aggregated bar
            return Bar(
                symbol,
                merged_open,
                merged_high,
                merged_low,
                merged_close,
                merged_volume,
                merged_timestamp
            )

        # If not enough bars yet, return None
        return None


    def _detect_gap(self, bar_1m_list):
        """
        Example utility to detect if the last two bars are more than
        2 minutes apart. Returns True if there's a big gap.
        """
        if len(bar_1m_list) < 2:
            return False
        # e.g., naive difference in seconds
        t1 = bar_1m_list[-1].timestamp
        t2 = bar_1m_list[-2].timestamp
        gap = abs((t1 - t2).total_seconds())
        # If >120 seconds => gap
        return gap > 120


class LiveTradingManager:
    """
    SPRINT 3 + Enhanced:
    - Attempts to connect to AlpacaStoreStreamer if use_alpaca_store = True.
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

        # From code2: additional attributes for aggregator & strategies
        self.live_strategies = []
        self.execution_engine = None
        self.aggregator = None

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

    def _setup_execution_engine(self):
        """
        From code2: sets up the ExecutionEngine if not present.
        """
        if self.execution_engine is None:
            self.execution_engine = ExecutionEngine()
            self.execution_engine.start()
            logger.info("Execution engine started from LiveTradingManager")

    def _load_live_strategies(self):
        """
        Load strategies from DB where mode='live', create the instance, store in self.live_strategies
        (From code2)
        """
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        rows = cur.execute("""
            SELECT name, timeframe
            FROM strategies
            WHERE mode='live'
        """).fetchall()
        conn.close()

        strategies = []
        for (strat_name, timeframe) in rows:
            # get the actual class from StrategyAdapter
            if strat_name in StrategyAdapter.STRATEGIES:
                strat_cls = StrategyAdapter.STRATEGIES[strat_name]
                strat_obj = strat_cls()  # or pass params if needed
                # store timeframe
                setattr(strat_obj, 'live_timeframe', timeframe or '1Min')
                strategies.append(strat_obj)
        self.live_strategies = strategies
        logger.info(f"Loaded {len(strategies)} live strategies")

def _on_bar(self, bar):
    """
    Called when a final bar is available (aggregated or direct).
    Original extended fallback and logs are still here.
    """
    # Out-of-order fallback
    if not hasattr(self, '_last_bar_time'):
        self._last_bar_time = None
    if self._last_bar_time and bar.timestamp < self._last_bar_time:
        self.logger.warning(
            f"[on_bar fallback] Out-of-order bar => discarding. "
            f"Bar time={bar.timestamp}, last_bar_time={self._last_bar_time}"
        )
        return
    self._last_bar_time = bar.timestamp

    # Possibly log the bar for debugging
    self.logger.debug(f"[on_bar] {bar}")

    # If you have 'enabled' or 'paused' flags on strategies, keep them:
    for strategy in self.live_strategies:
        if getattr(strategy, 'enabled', True) is False:
            self.logger.debug(f"Skipping disabled strategy: {strategy.__class__.__name__}")
            continue

        signal = strategy.on_bar(bar)
        if signal:
            self.logger.info(f"Strategy {strategy.__class__.__name__} => trade {signal}")
            if self.execution_engine:
                self.execution_engine.add_trade_signal(signal)

    # Store the entire bar in DB with all fields:
    self.db.save_market_data_point(
        symbol=bar.symbol,
        timestamp=bar.timestamp,
        o=bar.open,
        h=bar.high,
        l=bar.low,
        c=bar.close,
        v=bar.volume
    )



    def _on_market_data(self, symbol, timestamp, o, h, l, c, v):
        """
        From code1: Save to live_trading_data.db, potentially run live strategy logic.
        """
        # Save to live_trading_data.db
        self.db.save_market_data_point(symbol, timestamp, o, h, l, c, v)
        # Potential extension point: a direct on_bar–style callback if needed.

    def _fetch_missed_data(self):
        """
        From code1: Attempt to find the last known timestamp from DB for each symbol,
        then fetch from that timestamp until now, so we fill in any data gap
        that might have occurred while we were offline.
        (Pseudo code, placeholder approach).
        """
        now = datetime.now(pytz.timezone('America/New_York'))
        for sym in self.symbols:
            last_ts = self.db.get_last_market_timestamp(sym)
            if last_ts:
                delta = now - last_ts
                if delta > timedelta(minutes=1):
                    # For demonstration, we just log that we'd fetch missed data
                    self.logger.info(f"Would fetch missed data for {sym} from {last_ts} to {now}")
                else:
                    self.logger.debug(f"No significant gap for {sym}, last recorded {last_ts}")
            else:
                self.logger.info(f"No prior timestamp found for {sym}, skipping retroactive fetch")

    # def _start_alpaca_streamer(self):
    #     """
    #     From code1: Start the Alpaca streamer in a background thread,
    #     with a reconnection approach if it fails mid-run.
    #     """
    #     def alpaca_worker():
    #         while self._running:
    #             try:
    #                 self._alpaca_streamer = AlpacaStoreStreamer(self.symbols, self._on_market_data)
    #                 self._alpaca_streamer.start()
    #                 self.logger.warning("Alpaca streamer ended or raised. Attempting reconnection after 15s.")
    #                 time.sleep(15)
    #             except Exception as e:
    #                 self.logger.error(f"Alpaca streamer exception: {e}. Retrying in 15s...")
    #                 time.sleep(15)
    #                 if not self._running:
    #                     break

    #     self._alpaca_thread = threading.Thread(target=alpaca_worker, daemon=True)
    #     self._alpaca_thread.start()
    #     self.logger.info("Alpaca streamer thread started.")
    
    
    def _start_alpaca_stream_aggregator(self, timeframe):
        """
        Subscribe to 1Min bars => aggregator => final timeframe bars.
        We'll create partial bars from the incoming data (which might be from AlpacaStoreStreamer),
        then pass them to self.aggregator.process().
        If process() returns a merged bar, we call self._on_bar(merged_bar).
        """
        def handle_1min_bar(bar_data):
            # bar_data fields might be: bar_data.symbol, bar_data.open[0], bar_data.high[0], etc.
            symbol = bar_data.symbol
            # note that bar_data usually is a Backtrader-like object, so fields might be an array
            # we pick index [0] for the current data
            open_p = bar_data.open[0]
            high_p = bar_data.high[0]
            low_p  = bar_data.low[0]
            close_p= bar_data.close[0]
            volume_p = bar_data.volume[0]
            timestamp = bar_data.datetime[0]

            bar_obj = Bar(
                symbol,
                open_p,
                high_p,
                low_p,
                close_p,
                volume_p,
                timestamp
            )

            # aggregator merges partial bars to produce final higher timeframe bar
            merged = self.aggregator.process(bar_obj)
            if merged:
                self._on_bar(merged)

        self.logger.info(f"Alpaca aggregator stream init, real=1Min, user-timeframe={timeframe}")
        self.streamer = AlpacaStoreStreamer(
            symbols=self.symbols,
            timeframe='1Min',  # aggregator merges into 5
            on_bar_callback=handle_1min_bar
        )
        self.streamer.start()




    def _start_zeromq_fallback(self):
        """
        From code1: Use ZeroMQPriceStreamer in a background thread with auto reconnection.
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

    def _start_alpaca_stream(self, timeframe):
        """
        From code2: streaming function that receives raw bars, 
        optionally passes them to aggregator, and then calls _on_bar().
        Note this differs from _start_alpaca_streamer() above in approach.
        """
        symbols = ['AAPL']  # Hard-coded example; in real usage, unify strategy symbols.

        self.logger.info(f"Starting AlpacaStoreStreamer with timeframe={timeframe} for {symbols}")
        
    def _handle_incoming_bar(self, bar):
        """
        Called when a new bar arrives from the aggregator or direct Alpaca stream.
        bar is assumed to have: bar.symbol, bar.close, bar.timestamp, etc.

        We pass it to each live strategy that has matching symbol(s). Then if we get
        a TradeSignal, we forward it to the execution_engine.
        """
        try:
            # If aggregator is used, 'bar' might be a merged timeframe bar.
            # If direct, it's just the same 1Min or real timeframe bar.

            self.logger.debug(f"Received bar for {bar.symbol} at {bar.timestamp} close={bar.close}")

            # For each strategy in live mode:
            for strategy in self.live_strategies:
                # If the strategy is configured for this symbol, or if it doesn't matter:
                # (In some designs, we store strategy.tickers or rely on symbol check)
                # Example pseudo:
                if (not hasattr(strategy, 'tickers')) or (bar.symbol in strategy.tickers):
                    trade_signal = strategy.on_bar(bar)
                    if trade_signal:
                        self.logger.info(f"Strategy {strategy.__class__.__name__} produced signal: {trade_signal}")
                        if self.execution_engine:
                            self.execution_engine.add_trade_signal(trade_signal)
        except Exception as e:
            self.logger.error(f"Error in _handle_incoming_bar: {e}")


        # def handle_incoming_bar(bar_data):
        #     # This is the raw 1Min bar. If aggregator is set, pass it. Otherwise direct:
        #     bar_obj = Bar(bar_data.symbol, bar_data.close[0], bar_data.datetime[0])
        #     if self.aggregator:
        #         new_bar = self.aggregator.process(bar_obj)
        #         if new_bar:
        #             self._on_bar(new_bar)
        #     else:
        #         self._on_bar(bar_obj)

        # self.streamer = AlpacaStoreStreamer(
        #     symbols=symbols,
        #     timeframe=timeframe,
        #     on_bar_callback=handle_incoming_bar
        # )
        # self.streamer.start()

    # def start(self, force_live=False):
    #     """
    #     Unified start() that merges code1's fallback logic, data fetch, 
    #     plus code2's aggregator & strategy setup.
    #     If force_live=True, we forcibly mark this strategy as live in the DB
    #     even if it wasn't before. Otherwise, if auto_resume is True or if 
    #     the user calls start() manually, we proceed.
    #     """
    #     # From code1
    #     if not force_live and not self.auto_resume:
    #         self.logger.info(
    #             f"Strategy '{self.strategy_name}' is not flagged as live. "
    #             f"Call start(force_live=True) if you want to forcibly make it live."
    #         )
    #         return

    #     self.db.set_strategy_live(self.strategy_name, True)
    #     self._running = True
    #     self.logger.info(f"Starting LiveTradingManager for {self.strategy_name}, use_alpaca={self.use_alpaca}")

    #     # From code2: set up execution engine and load live strategies
    #     self._setup_execution_engine()
    #     self._load_live_strategies()

    #     # Attempt to fill data gap if any (from code1)
    #     self._fetch_missed_data()

    #     # Check aggregator usage from code2
    #     aggregator_enabled = config.enable_aggregator()
    #     if aggregator_enabled:
    #         self.aggregator = SimpleAggregator(target_interval=5)
    #         # For aggregator usage, we call code2's _start_alpaca_stream() if Alpaca is enabled
    #         # but still keep code1 fallback logic if needed.
    #         if self.use_alpaca:
    #             self.logger.info(f"Trying aggregator-based AlpacaStoreStreamer for '{self.strategy_name}'...")
    #             try:
    #                 self._start_alpaca_stream('1Min')
    #             except Exception as e:
    #                 self.logger.warning(f"AlpacaStore failed: {str(e)}, falling back to ZeroMQ")
    #                 self._start_zeromq_fallback()
    #         else:
    #             self.logger.info(f"Alpaca store not enabled for '{self.strategy_name}'. Using ZeroMQ fallback directly.")
    #             self._start_zeromq_fallback()
    #     else:
    #         # If aggregator not enabled, run code1’s original fallback approach:
    #         if self.use_alpaca:
    #             self.logger.info(f"Trying AlpacaStoreStreamer first for '{self.strategy_name}'...")
    #             try:
    #                 self._start_alpaca_streamer()
    #             except Exception as e:
    #                 self.logger.warning(f"AlpacaStore failed: {str(e)}, falling back to ZeroMQ")
    #                 self._start_zeromq_fallback()
    #         else:
    #             self.logger.info(f"Alpaca store not enabled for '{self.strategy_name}'. Using ZeroMQ fallback directly.")
    #             self._start_zeromq_fallback()
    
    def start(self, force_live=False):
        """
        Start the LiveTradingManager for the given strategy in 'live' mode if forced
        or if the DB says it was previously live. 

        Steps:
        1) Mark the DB 'is_live'.
        2) Load & start the execution engine, load live strategies from DB.
        3) Attempt to fetch missed data from last timestamp until now.
        4) If aggregator is enabled, subscribe to aggregator-based bars. 
            Else, run the fallback approach. 
        5) If any errors occur, do reconnection attempts or log warnings.

        Logs:
        - We log aggregator creation, fallback usage, subscription steps, etc.
        """

        # Check if we need to forcibly set live
        if not force_live and not self.auto_resume:
            self.logger.info(
                f"{self.strategy_name} not flagged as live. "
                "Call start(force_live=True) if you want to forcibly make it live."
            )
            return

        # Step 1: mark DB is_live
        self.db.set_strategy_live(self.strategy_name, True)
        self._running = True

        # Some docstring says we might store the timeframe in self._timeframe
        # for logs:
        self.logger.info(f"[start] {self.strategy_name} => timeframe={self._timeframe} => aggregator={config.enable_aggregator()} => use_alpaca={self.use_alpaca}")

        # Step 2: set up execution engine, load strategies
        self._setup_execution_engine()
        self._load_live_strategies()

        # Step 3: attempt to fetch missed data 
        self._fetch_missed_data()

        # Step 4: aggregator logic
        aggregator_enabled = config.enable_aggregator()
        if aggregator_enabled:
            # Possibly map timeframe => aggregator chunk size
            t_map = {'1Min': 1, '5Min': 5, '15Min': 15, '1Hour': 60, '1Day': 999999}
            chunk_count = t_map.get(self._timeframe, 1)
            # create aggregator
            self.aggregator = SimpleAggregator(chunk_count)

            self.logger.info(
                f"Aggregator enabled => aggregator chunk={chunk_count}, now starting streamer"
            )

            # if we have Alpaca
            if self.use_alpaca:
                try:
                    self._start_alpaca_stream_aggregator(self._timeframe)
                except Exception as e:
                    self.logger.warning(f"Aggregator-based Alpaca stream failed => fallback ZeroMQ. Error: {e}")
                    self._start_zeromq_fallback()
            else:
                self.logger.info("Aggregator => using ZeroMQ fallback")
                self._start_zeromq_fallback()

        else:
            # aggregator not enabled => direct approach
            self.logger.info("No aggregator => direct streaming approach")
            if self.use_alpaca:
                try:
                    self._start_alpaca_streamer()
                except Exception as e:
                    self.logger.warning(f"Alpaca streamer error => fallback ZeroMQ: {e}")
                    self._start_zeromq_fallback()
            else:
                self.logger.info("No aggregator & no alpaca => ZeroMQ fallback.")
                self._start_zeromq_fallback()

        # Step 5: we log final success
        self.logger.debug("[start] done setting up live streaming. Now running in background.")



    def stop(self):
        """
        Gracefully stop the LiveTradingManager for this strategy.

        Steps:
        1) Mark DB 'is_live=False' for this strategy.
        2) Set self._running = False so threads can exit.
        3) If aggregator-based streamer is running, stop it.
        4) If ZeroMQ fallback is running, stop that as well.
        5) If any Alpaca background threads exist, join them.
        6) Log final status updates.

        This ensures no leftover streaming threads remain after user stops the strategy.
        """

        # Step 1: Mark DB
        self.logger.info(f"Stopping LiveTradingManager for {self.strategy_name}")
        self._running = False
        self.db.set_strategy_live(self.strategy_name, False)

        # Step 2: If aggregator-based streamer 
        if hasattr(self, 'streamer') and self.streamer:
            self.logger.debug("Stopping aggregator-based streamer now.")
            try:
                self.streamer.stop()
            except Exception as e:
                self.logger.warning(f"Error stopping aggregator streamer: {e}")
            self.logger.debug("Aggregator streamer stopped.")

        # Step 3: ZeroMQ fallback
        if self.zeromq_streamer:
            self.logger.debug("Stopping ZeroMQ fallback streamer.")
            self.zeromq_streamer.stop()
            self.logger.debug("ZeroMQ fallback streamer stopped.")

        # Step 4: If we have a dedicated ZeroMQ thread
        if self._zeromq_thread and self._zeromq_thread.is_alive():
            self.logger.info("Waiting for ZeroMQ fallback thread to finish.")
            self._zeromq_thread.join(timeout=5)
            if self._zeromq_thread.is_alive():
                self.logger.warning("ZeroMQ fallback thread did not terminate cleanly.")
            else:
                self.logger.debug("ZeroMQ fallback thread joined successfully.")

        # Step 5: If we had an Alpaca streamer thread
        if hasattr(self, '_alpaca_thread') and self._alpaca_thread and self._alpaca_thread.is_alive():
            self.logger.info("Waiting for Alpaca thread to finish.")
            self._alpaca_thread.join(timeout=5)
            if self._alpaca_thread.is_alive():
                self.logger.warning("Alpaca thread did not terminate properly.")
            else:
                self.logger.debug("Alpaca thread joined successfully.")

        # Step 6: Log final
        self.logger.info(f"Successfully stopped LiveTradingManager for {self.strategy_name}")


    def reload_live_strategies(self):
        """
        From code2: Re-query the DB, find new or removed strategies, etc.
        For demonstration, we'll just do a naive approach: stop, re-load, start again.
        """
        self.stop()
        self.start(force_live=True)  # forcing live to keep it consistent with code1 logic
