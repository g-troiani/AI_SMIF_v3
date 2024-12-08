# components/data_management_module/real_time_data.py

import zmq
import json
import threading
import logging
from datetime import datetime, timedelta
import asyncio
from alpaca_trade_api.stream import Stream
from alpaca_trade_api.common import URL
from .config import config
from .data_access_layer import db_manager, HistoricalData
import pytz

class RealTimeDataStreamer:
    """Handles real-time market data streaming using ZeroMQ for internal distribution"""
    
    def __init__(self, tickers):
        self.logger = self._setup_logging()
        self.tickers = tickers
        
        # Initialize ZeroMQ context and sockets
        self.zmq_context = zmq.Context()
        self.publisher = self.zmq_context.socket(zmq.PUB)
        self.publisher.bind(f"tcp://*:{config.get('DEFAULT', 'zeromq_port')}")
        
        # Initialize Alpaca stream
        self.stream = Stream(
            config.get('api', 'key_id'),
            config.get('api', 'secret_key'),
            base_url=URL(config.get('api', 'base_url')),
            data_feed='sip'
        )
        
        self._running = False
        self._last_prices = {}
        self._last_update = {}
        self._interval = timedelta(minutes=1)

    def _setup_logging(self):
        """Set up logging for the real-time data streamer"""
        logger = logging.getLogger('realtime_data')
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(config.get('DEFAULT', 'log_file'))
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

    async def _is_market_hours(self):
        """Check if current time is within market hours"""
        ny_time = datetime.now(pytz.timezone('America/New_York'))
        market_open = ny_time.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = ny_time.replace(hour=16, minute=0, second=0, microsecond=0)
        return market_open <= ny_time <= market_close

    async def handle_bar(self, bar):
        try:
            if not await self._is_market_hours():
                return

            # Convert bar.timestamp from nanoseconds to datetime
            bar.timestamp = datetime.datetime.fromtimestamp(bar.timestamp / 1e9, tz=pytz.UTC)
            #bar.timestamp = datetime.datetime.fromtimestamp(bar.timestamp / 1e9, tz=pytz.UTC)

            # Get the minute of the timestamp
            minute = bar.timestamp.minute

            # UNCOMMENT THIS TO STORE 5 MINUTE BARS
            # Check if the minute is a multiple of 5
            # if minute % 5 == 0:
            #     # Process the bar
            #     self._store_bar_data(bar)
            #     self._publish_bar_data(bar)
            #     self._last_update[bar.symbol] = bar.timestamp
            #     self._last_prices[bar.symbol] = bar.close
            # else:
            #     # Do not process the bar
            #     pass

        except Exception as e:
            self.logger.error(f"Error processing bar data: {str(e)}")
            
    def update_tickers(self, new_tickers):
        """Update the list of tickers being streamed."""
        try:
            with threading.Lock():
                current_set = set(self.tickers)
                new_set = set(new_tickers)
                
                success = True
                # Track changes to allow rollback if needed
                unsubscribed = set()
                subscribed = set()
                
                # First unsubscribe removed tickers
                for ticker in current_set - new_set:
                    try:
                        self.stream.unsubscribe_bars(ticker)
                        unsubscribed.add(ticker)
                        self.logger.info(f"Unsubscribed from {ticker}")
                    except Exception as e:
                        self.logger.error(f"Failed to unsubscribe {ticker}: {e}")
                        success = False
                        break
                
                # Then subscribe new tickers if unsubscribe was successful
                if success:
                    for ticker in new_set - current_set:
                        try:
                            self.stream.subscribe_bars(self.handle_bar, ticker)
                            subscribed.add(ticker)
                            self.logger.info(f"Subscribed to {ticker}")
                        except Exception as e:
                            self.logger.error(f"Failed to subscribe {ticker}: {e}")
                            success = False
                            break
                
                if not success:
                    # Rollback changes if anything failed
                    self._rollback_changes(subscribed, unsubscribed)
                    return False
                    
                self.tickers = list(new_set)
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating tickers: {e}")
            return False

    def _rollback_changes(self, subscribed, unsubscribed):
        """Rollback any changes made during failed update."""
        for ticker in subscribed:
            try:
                self.stream.unsubscribe_bars(ticker)
            except Exception as e:
                self.logger.error(f"Rollback: Failed to unsubscribe {ticker}: {e}")
                
        for ticker in unsubscribed:
            try:
                self.stream.subscribe_bars(self.handle_bar, ticker)
            except Exception as e:
                self.logger.error(f"Rollback: Failed to resubscribe {ticker}: {e}")

    
    def _store_bar_data(self, bar):
        """Store bar data in the database"""
        try:
            # Save real-time data using db_manager
            db_manager.save_real_time_data(bar)
            # Log confirmation
            self.logger.info(f"Stored real-time data for {bar.symbol} at {bar.timestamp}")
        except Exception as e:
            self.logger.error(f"Failed to store bar data: {str(e)}")


    def _publish_bar_data(self, bar):
        """Publish bar data through ZeroMQ"""
        try:
            message = {
                'symbol': bar.symbol,
                'timestamp': bar.timestamp.isoformat(),
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume
            }

            topic = f"{config.get('DEFAULT', 'zeromq_topic')}.{bar.symbol}"
            self.publisher.send_string(f"{topic} {json.dumps(message)}")
            self.logger.debug(f"Published bar data for {bar.symbol}")

        except Exception as e:
            self.logger.error(f"Failed to publish bar data: {str(e)}")


    def start(self):
        """Start the real-time data streaming"""
        if self._running:
            self.logger.warning("Streamer is already running")
            return

        self._running = True
        self.logger.info("Starting real-time data streaming")
        
        # Subscribe to bars for all tickers
        for ticker in self.tickers:
            self.stream.subscribe_bars(self.handle_bar, ticker)
            self.logger.info(f"Subscribed to bars for {ticker}")

        # Start the stream in a separate thread
        try:
            self.stream_thread = threading.Thread(target=self._run_stream, daemon=True)
            self.stream_thread.start()
        except Exception as e:
            self._running = False
            self.logger.error(f"Stream error: {str(e)}")
            raise
    def _run_stream(self):
        """Run the stream in the event loop"""
        try:
            self.stream.run()
        except Exception as e:
            self._running = False
            self.logger.error(f"Stream encountered an error: {str(e)}")

    def stop(self):
        """Stop the real-time data streaming"""
        if not self._running:
            return

        self._running = False
        try:
            self.stream.stop()
            if hasattr(self, 'stream_thread') and self.stream_thread.is_alive():
                self.stream_thread.join(timeout=5)
            self.publisher.close()
            self.zmq_context.term()
            self.logger.info("Stopped real-time data streaming")
        except Exception as e:
            self.logger.error(f"Error stopping stream: {str(e)}")

    def update_tickers(self, new_tickers):
        """Update the list of tickers to stream."""
        with threading.Lock():
            # Unsubscribe from tickers no longer in the list
            for ticker in set(self.tickers) - set(new_tickers):
                self.stream.unsubscribe_bars(ticker)
                self.logger.info(f"Unsubscribed from bars for {ticker}")

            # Subscribe to new tickers
            for ticker in set(new_tickers) - set(self.tickers):
                self.stream.subscribe_bars(self.handle_bar, ticker)
                self.logger.info(f"Subscribed to bars for {ticker}")

            self.tickers = new_tickers
            print("Tickers updated for streaming.")
