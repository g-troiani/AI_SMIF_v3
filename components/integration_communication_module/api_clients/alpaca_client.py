# components/integration_communication_module/api_clients/alpaca_client.py

import alpaca_trade_api as tradeapi
from ..logger import logger
from .base_data_service import BaseDataService
from .base_trade_service import BaseTradeService
from ..models import MarketData, Order

class AlpacaClient(BaseDataService, BaseTradeService):
    def __init__(self, credentials_manager):
        creds = credentials_manager.get_alpaca_credentials()
        self.api = tradeapi.REST(
            key_id=creds['api_key'],
            secret_key=creds['secret_key'],
            base_url=creds['base_url']
        )
        logger.info("AlpacaClient initialized.")

    def get_account(self):
        try:
            account = self.api.get_account()
            logger.info("Account retrieved successfully.")
            return account
        except Exception as e:
            logger.error(f"Error retrieving account: {e}")
            raise

    def get_market_data(self, symbol, timeframe, start, end):
        try:
            barset = self.api.get_barset(symbol, timeframe, start=start, end=end)
            bars = barset[symbol]
            logger.info(f"Market data for {symbol} retrieved successfully.")
            # Convert to MarketData instances
            market_data = []
            for bar in bars:
                market_data.append(MarketData(
                    symbol=symbol,
                    timestamp=bar.t.isoformat(),
                    open=bar.o,
                    high=bar.h,
                    low=bar.l,
                    close=bar.c,
                    volume=bar.v
                ))
            return market_data
        except Exception as e:
            logger.error(f"Error retrieving market data for {symbol}: {e}")
            raise

    def place_order(self, symbol, qty, side, type, time_in_force):
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=type,
                time_in_force=time_in_force
            )
            logger.info(f"Order placed successfully: {order.id}")
            return Order(
                id=order.id,
                symbol=order.symbol,
                qty=order.qty,
                side=order.side,
                type=order.type,
                time_in_force=order.time_in_force,
                status=order.status
            )
        except Exception as e:
            logger.error(f"Error placing order for {symbol}: {e}")
            raise
