# File: components/trading_execution_engine/alpaca_api.py
# Type: py

import aiohttp
import asyncio
import logging
from .config import CONFIG

class AlpacaAPIClient:
    """Client for interacting with Alpaca's REST API asynchronously"""

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
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

    async def close(self):
        """Closes the aiohttp session and waits for all tasks to be completed."""
        if not self.session.closed:
            await self.session.close()
            self.logger.info("aiohttp session closed.")


    async def place_order_async(self, order_params):
        """
        Places an order asynchronously.
        """
        url = f"{self.base_url}/v2/orders"
        for attempt in range(3):  # Retry up to 3 times
            try:
                async with self.session.post(url, json=order_params, timeout=10) as response:
                    if response.status == 200 or response.status == 201:
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
                    self.logger.error(f"Failed to place order after 3 attempts")
                    raise
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                raise

    async def get_order_status_async(self, order_id):
        """
        Retrieves the status of an order asynchronously.
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
        Retrieves account information asynchronously.
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
        Retrieves all open positions asynchronously.
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
        Retrieves a specific position asynchronously.
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
        Cancels all open orders asynchronously.
        """
        url = f"{self.base_url}/v2/orders"
        for attempt in range(3):  # Retry up to 3 times
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
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                if attempt == 2:
                    self.logger.error("Failed to cancel all orders after 3 attempts")
                    raise
            except Exception as e:
                self.logger.error(f"Unexpected error canceling orders: {e}")
                raise

    async def cancel_order_async(self, order_id: str):
        """
        Cancels a specific order asynchronously.
        """
        url = f"{self.base_url}/v2/orders/{order_id}"
        for attempt in range(3):  # Retry up to 3 times
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
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                if attempt == 2:
                    self.logger.error(f"Failed to cancel order {order_id} after 3 attempts")
                    raise
            except Exception as e:
                self.logger.error(f"Unexpected error canceling order {order_id}: {e}")
                raise
