# File: components/data_management_module/alpaca_api.py
#
# Unified Alpaca API code combining synchronous (first snippet) and
# asynchronous (second snippet) functionalities into one module.
#
# Classes:
#  - AlpacaAPIClient (synchronous)
#  - AlpacaAPIClientAsync (asynchronous)

import logging
import time
import requests
from datetime import datetime, timedelta
import pandas as pd
import pytz
from alpaca_trade_api.rest import REST, TimeFrame, TimeFrameUnit
from .config import config  # For synchronous usage

import aiohttp
import asyncio
# For the new asynchronous class:
from .config import CONFIG  # The unified config dictionary (as in old async code)


class AlpacaAPIClient:
    """
    Synchronous client for interacting with Alpaca's REST API 
    (original first snippet from data_management_module).
    """

    def __init__(self):
        self.logger = self._setup_logging()
        self.base_url = config.get('api', 'base_url')
        self.headers = {
            'APCA-API-KEY-ID': config.get('api', 'key_id'),
            'APCA-API-SECRET-KEY': config.get('api', 'secret_key')
        }
        # Instantiate the REST API client
        self.api = REST(
            key_id=config.get('api', 'key_id'),
            secret_key=config.get('api', 'secret_key'),
            base_url=config.get('api', 'base_url')
        )
        # Rate limiting settings
        self.retry_count = config.get_int('api', 'rate_limit_retry_attempts')
        self.retry_delay = config.get_int('api', 'rate_limit_retry_wait')
        self.rate_limit_delay = config.get_float('api', 'rate_limit_delay')
        self._last_request_time = 0

        # Add chunk size for data fetching
        self.chunk_size = 15  # Number of days per chunk

    def _setup_logging(self):
        """Set up logging for the API client"""
        logger = logging.getLogger('alpaca_api')
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(config.get('DEFAULT', 'log_file'))
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

    def _respect_rate_limit(self):
        """Implement rate limiting to avoid API throttling"""
        now = time.time()
        time_since_last = now - self._last_request_time
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def fetch_historical_data(self, ticker, start_date, end_date, timeframe='1Min'):
        """
        Fetch historical data with proper formatting, chunked if needed.
        Synchronous approach used mostly by data ingestion code.
        """
        self.logger.info(
            f"# SPRINT 6: Fetching historical data for {ticker} from {start_date} to {end_date}, timeframe={timeframe}"
        )
        all_data = []
        current_date = start_date
        chunk_count = 0

        while current_date < end_date:
            chunk_end = min(current_date + timedelta(days=self.chunk_size), end_date)
            chunk_count += 1
            print(f"CRITICAL DEBUG: Fetching chunk {chunk_count}: {current_date} to {chunk_end}")
            chunk_data = self._fetch_data_chunk(ticker, current_date, chunk_end, timeframe)

            if not chunk_data.empty:
                print(f"CRITICAL DEBUG: Retrieved {len(chunk_data)} records in chunk {chunk_count}")
                all_data.append(chunk_data)
            else:
                print(f"CRITICAL DEBUG: No data retrieved in chunk {chunk_count}")

            current_date = chunk_end + timedelta(seconds=1)  # Avoid overlapping

        if all_data:
            final_data = pd.concat(all_data)
        else:
            final_data = pd.DataFrame()

        print(f"CRITICAL DEBUG: Final data shape={final_data.shape}, columns={final_data.columns.tolist()}")
        if not final_data.empty:
            earliest_date = final_data.index.min()
            latest_date = final_data.index.max()
            print(f"CRITICAL DEBUG: Data ranges from {earliest_date} to {latest_date}")

        return final_data

    def _fetch_data_chunk(self, ticker, start_date, end_date, timeframe):
        """
        Internal method used by fetch_historical_data to retrieve chunked bars.
        """
        for attempt in range(self.retry_count):
            try:
                self._respect_rate_limit()

                # TimeFrame mapping
                timeframe_map = {
                    '1Min': TimeFrame(1, TimeFrameUnit.Minute),
                    '5Min': TimeFrame(5, TimeFrameUnit.Minute),
                    '15Min': TimeFrame(15, TimeFrameUnit.Minute),
                    '1Hour': TimeFrame(1, TimeFrameUnit.Hour),
                    '1Day': TimeFrame(1, TimeFrameUnit.Day)
                }
                tf = timeframe_map.get(timeframe)
                if tf is None:
                    raise ValueError(f"Invalid timeframe: {timeframe}")

                bars = self.api.get_bars(
                    ticker,
                    timeframe=tf,
                    start=start_date.isoformat(),
                    end=end_date.isoformat(),
                    adjustment='raw',
                    limit=10000  # Max limit per request
                ).df

                if bars.empty:
                    self.logger.warning(
                        f"No data returned for {ticker} between {start_date} and {end_date}"
                    )
                    print(f"CRITICAL DEBUG: No data returned for {ticker} between {start_date} and {end_date}")
                    return pd.DataFrame()

                # Ensure the index is a DateTimeIndex
                if not isinstance(bars.index, pd.DatetimeIndex):
                    bars.index = pd.to_datetime(bars.index)
                bars = bars.sort_index()

                # Rename columns if necessary
                if set(['o', 'h', 'l', 'c', 'v']).issubset(bars.columns):
                    bars.rename(
                        columns={'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume'},
                        inplace=True
                    )

                # Convert timezone and filter market hours
                ny_tz = pytz.timezone('America/New_York')
                bars.index = bars.index.tz_convert(ny_tz)
                bars = bars.between_time('09:30', '16:00')

                self.logger.info(
                    f"Successfully fetched {len(bars)} bars for {ticker} from {start_date} to {end_date}"
                )
                print(
                    f"CRITICAL DEBUG: Successfully fetched {len(bars)} bars for {ticker} from {start_date} to {end_date}"
                )
                return bars

            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {ticker}: {str(e)}")
                print(f"CRITICAL DEBUG: Attempt {attempt + 1} failed for {ticker}: {str(e)}")
                if attempt == self.retry_count - 1:
                    self.logger.error(
                        f"Failed to fetch data for {ticker} after {self.retry_count} attempts"
                    )
                    print(f"CRITICAL DEBUG: Failed to fetch data for {ticker} after {self.retry_count} attempts")
                    raise
                time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff

    def verify_api_access(self):
        """Verify API credentials and access"""
        try:
            clock = self.api.get_clock()
            if clock:
                self.logger.info("API access verified successfully")
                return True
            else:
                self.logger.error("API access verification failed")
                return False
        except Exception as e:
            self.logger.error(f"API access verification failed: {str(e)}")
            return False

    def get_bars(self, ticker, start_date, end_date):
        """
        Get historical bars for a ticker in a synchronous manner.
        """
        try:
            self.logger.info(f"Requesting bars for {ticker} from {start_date} to {end_date}")

            bars = self.api.get_bars(
                ticker,
                TimeFrame(1, TimeFrame.Unit.Minute),
                start=start_date.isoformat(),
                end=end_date.isoformat(),
                adjustment='raw'
            ).df

            if bars.empty:
                self.logger.warning(
                    f"No data returned for {ticker} between {start_date} and {end_date}"
                )
                return pd.DataFrame()

            self.logger.info(f"Successfully fetched {len(bars)} bars for {ticker}")
            return bars

        except Exception as e:
            self.logger.error(f"Error fetching bars: {str(e)}")
            raise

    def _get_bars_for_date(self, ticker, date):
        """Get bars for a specific date"""
        try:
            start_date = datetime.combine(date, datetime.min.time())
            end_date = datetime.combine(date, datetime.max.time())
            bars = self.get_bars(ticker, start_date, end_date)
            if not bars.empty:
                self.logger.info(
                    f"Fetched {len(bars)} bars for {ticker} on {date.strftime('%Y-%m-%d')}"
                )
            return bars
        except Exception as e:
            self.logger.error(f"Error fetching bars for {date}: {str(e)}")
            return pd.DataFrame()


class AlpacaAPIClientAsync:
    """
    Asynchronous client for interacting with Alpaca's REST API 
    (original second snippet from trading_execution_engine).
    """

    def __init__(self):
        self.logger = self._setup_logging()
        self.base_url = CONFIG['alpaca']['base_url']
        self.api_key = CONFIG['alpaca']['key_id']
        self.api_secret = CONFIG['alpaca']['secret_key']
        self.headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.api_secret
        }
        self.session = aiohttp.ClientSession(headers=self.headers)

    def _setup_logging(self):
        logger = logging.getLogger('alpaca_api')
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(CONFIG['logging']['log_file'])
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

    async def close(self):
        """Closes the aiohttp session and waits for all tasks to be completed."""
        if not self.session.closed:
            await self.session.close()
            self.logger.info("aiohttp session closed.")

    async def place_order_async(self, order_params):
        """
        Places an order asynchronously (POST /v2/orders).
        Retries up to 3 times on client errors, with exponential backoff.
        """
        url = f"{self.base_url}/v2/orders"
        for attempt in range(3):
            try:
                async with self.session.post(url, json=order_params, timeout=10) as response:
                    if response.status in (200, 201):
                        order = await response.json()
                        self.logger.info(f"Order placed: {order}")
                        return order
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Error placing order: {response.status} {error_text}")
                        response.raise_for_status()
            except aiohttp.ClientError as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                if attempt == 2:
                    self.logger.error("Failed to place order after 3 attempts")
                    raise
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                raise

    async def get_order_status_async(self, order_id):
        """
        Retrieves the status of an order asynchronously (GET /v2/orders/{order_id}).
        """
        url = f"{self.base_url}/v2/orders/{order_id}"
        try:
            async with self.session.get(url, timeout=10) as response:
                response.raise_for_status()
                order = await response.json()
                return order
        except aiohttp.ClientError as e:
            self.logger.error(f"Error retrieving order status: {e}")
            raise

    async def get_account_info_async(self):
        """
        Retrieves account information asynchronously (GET /v2/account).
        """
        url = f"{self.base_url}/v2/account"
        try:
            async with self.session.get(url, timeout=10) as response:
                response.raise_for_status()
                account_info = await response.json()
                return account_info
        except aiohttp.ClientError as e:
            self.logger.error(f"Error retrieving account info: {e}")
            raise

    async def get_positions_async(self):
        """
        Retrieves all open positions asynchronously (GET /v2/positions).
        """
        url = f"{self.base_url}/v2/positions"
        try:
            async with self.session.get(url, timeout=10) as response:
                response.raise_for_status()
                positions = await response.json()
                return positions
        except aiohttp.ClientError as e:
            self.logger.error(f"Error retrieving positions: {e}")
            raise

    async def get_position_async(self, ticker):
        """
        Retrieves a specific position asynchronously (GET /v2/positions/{symbol}).
        """
        url = f"{self.base_url}/v2/positions/{ticker}"
        try:
            async with self.session.get(url, timeout=10) as response:
                response.raise_for_status()
                position = await response.json()
                return position
        except aiohttp.ClientError as e:
            self.logger.error(f"Error retrieving position for {ticker}: {e}")
            raise

    async def cancel_all_orders_async(self):
        """
        Cancels all open orders asynchronously (DELETE /v2/orders).
        """
        url = f"{self.base_url}/v2/orders"
        for attempt in range(3):
            try:
                async with self.session.delete(url, timeout=10) as response:
                    if response.status in (200, 204):
                        self.logger.info("All open orders have been canceled.")
                        return await response.json() if response.content_length else None
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Error canceling orders: {response.status} {error_text}")
                        response.raise_for_status()
            except aiohttp.ClientError as e:
                self.logger.warning(f"Attempt {attempt + 1} to cancel all orders failed: {e}")
                await asyncio.sleep(2 ** attempt)
                if attempt == 2:
                    self.logger.error("Failed to cancel all orders after 3 attempts")
                    raise
            except Exception as e:
                self.logger.error(f"Unexpected error canceling orders: {e}")
                raise

    async def cancel_order_async(self, order_id: str):
        """
        Cancels a specific order asynchronously (DELETE /v2/orders/{order_id}).
        """
        url = f"{self.base_url}/v2/orders/{order_id}"
        for attempt in range(3):
            try:
                async with self.session.delete(url, timeout=10) as response:
                    if response.status in (200, 204):
                        self.logger.info(f"Order {order_id} has been canceled.")
                        return await response.json() if response.content_length else None
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Error canceling order {order_id}: {response.status} {error_text}")
                        response.raise_for_status()
            except aiohttp.ClientError as e:
                self.logger.warning(f"Attempt {attempt + 1} to cancel order {order_id} failed: {e}")
                await asyncio.sleep(2 ** attempt)
                if attempt == 2:
                    self.logger.error(f"Failed to cancel order {order_id} after 3 attempts")
                    raise
            except Exception as e:
                self.logger.error(f"Unexpected error canceling order {order_id}: {e}")
                raise


# End of the unified alpaca_api.py
