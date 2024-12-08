# File: components/trading_execution_engine/execution_engine.py
# Type: py

import os
import asyncio
import threading
import queue
import json
from datetime import datetime, time
import pytz
import logging
from typing import Optional, Dict, Any
from .trade_signal import TradeSignal
from .order_manager import OrderManager
from .alpaca_api import AlpacaAPIClient
from .config import CONFIG

# File: components/trading_execution_engine/execution_engine.py
# Type: py

# File: components/trading_execution_engine/execution_engine.py
# Type: py

class ExecutionEngine:
    """
    Processes trade signals asynchronously and executes trades with error recovery.
    """

    def __init__(
        self,
        alpaca_client: Optional[AlpacaAPIClient] = None,
        order_manager: Optional[OrderManager] = None
    ):
        self.signal_queue = queue.Queue()
        self.order_manager = order_manager if order_manager else OrderManager()
        self.alpaca_client = alpaca_client if alpaca_client else AlpacaAPIClient()
        self.logger = self._setup_logging()
        self.loop = asyncio.get_event_loop()
        self.daily_pnl = 0.0
        self.risk_config = CONFIG['risk']
        self.recovery_interval = 300  # 5 minutes
        self.max_retries = 3
        self.retry_delays = [2, 5, 10]  # Exponential backoff delays in seconds
        self._active_orders: Dict[str, Dict[str, Any]] = {}

        self._start_recovery_task()




    def _setup_logging(self):
        logger = logging.getLogger('execution_engine')
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(CONFIG['logging']['log_file'])
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

    def _run_event_loop(self):
        """Runs the event loop for processing signals."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._process_signals())

    def _start_recovery_task(self):
        """Starts the periodic recovery task for failed trades."""
        async def run_recovery():
            while not self.stop_event.is_set():
                # If in test mode, reduce the sleep interval to quickly exit
                interval = 0.1 if os.getenv("TEST_MODE") else self.recovery_interval
                await asyncio.sleep(interval)
                if self.stop_event.is_set():
                    break
                try:
                    await self._recover_failed_trades()
                except Exception as e:
                    self.logger.error(f"Error in recovery task: {e}")

        asyncio.run_coroutine_threadsafe(run_recovery(), self.loop)

    # File: components/trading_execution_engine/execution_engine.py
    # Type: py

    async def _recover_failed_trades(self):
        """Attempts to recover failed trades with retry logic."""
        try:
            failed_trades = self._get_pending_failed_trades_for_recovery()
            for trade_info in failed_trades:
                trade_id, trade_signal_json, error_message, retry_count = trade_info
                await self._recover_single_failed_trade(trade_id, trade_signal_json, error_message, retry_count)
        except Exception as e:
            self.logger.error(f"Error in recovery process: {e}")

    def _get_pending_failed_trades_for_recovery(self):
        """Retrieves pending failed trades from the order manager for recovery."""
        return self.order_manager.get_pending_failed_trades(self.max_retries)

    async def _recover_single_failed_trade(self, trade_id, trade_signal_json, error_message, retry_count):
        """Attempts to recover a single failed trade."""
        self.logger.info(f"Attempting to recover failed trade {trade_id}, retry {retry_count + 1}")
        try:
            trade_signal_dict = json.loads(trade_signal_json)
            trade_signal = TradeSignal.from_dict(trade_signal_dict)

            delay = self.retry_delays[min(retry_count, len(self.retry_delays) - 1)]
            await asyncio.sleep(delay)

            if await self.validate_trade_signal(trade_signal):
                await self.execute_trade_with_recovery(trade_signal, is_recovery=True)
                self.order_manager.update_failed_trade_status(trade_id, 'resolved')
                self.logger.info(f"Successfully recovered trade {trade_id}")
            else:
                await self.handle_failed_trade(
                    trade_signal,
                    "Trade signal validation failed during recovery",
                    trade_id
                )
        except Exception as e:
            self.logger.error(f"Error recovering trade {trade_id}: {e}")
            if retry_count + 1 >= self.max_retries:
                self.order_manager.update_failed_trade_status(trade_id, 'failed')
            else:
                # Attempt to get trade_signal from locals if it was successfully created, else pass None.
                await self.handle_failed_trade(
                    locals().get('trade_signal'),
                    str(e),
                    trade_id
                )
        finally:
            # Wait a brief moment before processing the next trade to avoid flooding logs.
            await asyncio.sleep(1)


    async def _process_signals(self):
        """Processes trade signals from the queue."""
        while not self.stop_event.is_set():
            try:
                trade_signal = await self.loop.run_in_executor(None, self.signal_queue.get)
                if trade_signal is None:
                    continue
                await self.execute_trade_signal(trade_signal)
            except Exception as e:
                self.logger.error(f"Error processing trade signal: {e}")
                if isinstance(trade_signal, TradeSignal):
                    await self.handle_failed_trade(trade_signal, str(e))

    async def handle_failed_trade(self, trade_signal: TradeSignal, error_message: str,
                                  existing_trade_id: Optional[str] = None):
        """Handles failed trades by logging and initiating recovery process."""
        try:
            if existing_trade_id:
                self.order_manager.update_failed_trade_status(
                    existing_trade_id, 'retry', error_message
                )
            else:
                self.order_manager.log_failed_trade(trade_signal, error_message)

            self.logger.error(f"Trade failed: {error_message}")

            order_id = self._active_orders.get(trade_signal.strategy_id)
            if order_id:
                try:
                    await self.alpaca_client.cancel_order_async(order_id)
                except Exception as e:
                    self.logger.error(f"Error canceling failed order {order_id}: {e}")
                finally:
                    self._active_orders.pop(trade_signal.strategy_id, None)

        except Exception as e:
            self.logger.error(f"Error handling failed trade: {e}")

    async def validate_trade_signal(self, trade_signal: TradeSignal) -> bool:
        """Validates trade signal against risk management rules."""
        try:
            account_info = await self.alpaca_client.get_account_info_async()
            portfolio_value = float(account_info['portfolio_value'])

            if trade_signal.price is None and trade_signal.order_type == 'market':
                trade_signal.price = 0.0  # Default to 0 if price not provided

            validation_price = (trade_signal.limit_price if trade_signal.order_type == 'limit'
                                else trade_signal.stop_price if trade_signal.order_type == 'stop'
                                else trade_signal.price)

            order_value = trade_signal.quantity * validation_price
            max_position_value = portfolio_value * self.risk_config['max_position_size_pct']

            if order_value > max_position_value:
                self.logger.warning(f"Order value {order_value} exceeds maximum position size {max_position_value}")
                return False

            if order_value > self.risk_config['max_order_value']:
                self.logger.warning(f"Order value {order_value} exceeds maximum order value {self.risk_config['max_order_value']}")
                return False

            if self.daily_pnl <= -(portfolio_value * self.risk_config['daily_loss_limit_pct']):
                self.logger.warning("Daily loss limit reached")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating trade signal: {e}")
            return False

    def add_trade_signal(self, trade_signal: TradeSignal):
        """Adds a trade signal to the processing queue."""
        self.signal_queue.put(trade_signal)
        self.logger.info(f"Trade signal added to queue: {trade_signal}")

    def is_market_open(self) -> bool:
        """Checks if the market is currently open."""
        tz = pytz.timezone('America/New_York')
        now = datetime.now(tz)
        market_open = time(9, 30)
        market_close = time(16, 0)
        return market_open <= now.time() <= market_close

    async def execute_trade_signal(self, trade_signal: TradeSignal):
        """Main method for executing trade signals with error handling."""
        if not self.is_market_open():
            self.logger.warning("Market is closed. Trade signal will not be executed.")
            await self.handle_failed_trade(trade_signal, "Market closed")
            return

        self.logger.info(f"Processing trade signal: {trade_signal}")
        try:
            if not await self.validate_trade_signal(trade_signal):
                await self.handle_failed_trade(trade_signal, "Trade signal validation failed")
                return
            await self.execute_trade_with_recovery(trade_signal)
        except Exception as e:
            self.logger.error(f"Error executing trade signal: {e}")
            await self.handle_failed_trade(trade_signal, str(e))

    async def execute_trade_with_recovery(self, trade_signal: TradeSignal, is_recovery: bool = False):
        """Executes a trade with built-in recovery mechanisms."""
        for attempt in range(self.max_retries):
            try:
                await self.place_order(trade_signal)
                return True
            except Exception as e:
                if attempt == self.max_retries - 1:
                    if not is_recovery:
                        await self.handle_failed_trade(trade_signal, str(e))
                    raise
                delay = self.retry_delays[attempt]
                self.logger.warning(f"Retrying trade after {delay}s. Error: {e}")
                await asyncio.sleep(delay)
        return False

    # File: components/trading_execution_engine/execution_engine.py

    async def place_order(self, trade_signal: TradeSignal):
        """Places an order with the broker."""
        self.logger.info(f"Placing order for trade signal: {trade_signal}")
        start_time = datetime.now()

        order_params = {
            'symbol': trade_signal.ticker,
            'qty': trade_signal.quantity,
            'side': trade_signal.signal_type.lower(),  # e.g. 'buy' or 'sell'
            'type': trade_signal.order_type,
            'time_in_force': trade_signal.time_in_force,
            'client_order_id': trade_signal.strategy_id
        }

        if trade_signal.order_type == 'limit':
            order_params['limit_price'] = trade_signal.limit_price
        elif trade_signal.order_type == 'stop':
            order_params['stop_price'] = trade_signal.stop_price

        try:
            order = await self.alpaca_client.place_order_async(order_params)
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Order placed successfully: {order} (execution time: {execution_time:.3f}s)")

            order['is_manual'] = 1 if trade_signal.strategy_id == 'manual_trade' else 0
            order['execution_time'] = execution_time
            order['side'] = order_params['side']  # Ensure 'side' is recorded

            self.order_manager.add_order(order)
            self._active_orders[trade_signal.strategy_id] = order['id']
            await self.check_order_status(order['id'])
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            raise


    async def check_order_status(self, order_id: str):
        """Monitors the status of a placed order."""
        self.logger.info(f"Checking status for order ID: {order_id}")
        try:
            for _ in range(10):  # Check status up to 10 times
                order = await self.alpaca_client.get_order_status_async(order_id)
                status = order['status']
                self.logger.info(f"Order {order_id} status: {status}")
                self.order_manager.update_order(order)

                if status == 'filled':
                    self.logger.info(f"Order {order_id} filled.")
                    await self.update_daily_pnl()
                    break
                elif status in ('canceled', 'rejected'):
                    self.logger.warning(f"Order {order_id} {status}.")
                    break

                await asyncio.sleep(5)
            else:
                self.logger.error(f"Order {order_id} status check timed out.")
        except Exception as e:
            self.logger.error(f"Error checking order status: {e}")
            raise

    async def update_daily_pnl(self):
        """Updates the daily P&L based on account information."""
        try:
            account_info = await self.alpaca_client.get_account_info_async()
            self.daily_pnl = float(account_info.get('equity')) - float(account_info.get('last_equity'))
            self.logger.info(f"Updated daily P&L: {self.daily_pnl}")
        except Exception as e:
            self.logger.error(f"Error updating daily P&L: {e}")

    async def update_portfolio(self):
        """Updates portfolio information."""
        self.logger.info("Updating portfolio information.")
        try:
            account_info = await self.alpaca_client.get_account_info_async()
            positions = await self.alpaca_client.get_positions_async()
            self.logger.info(f"Account balance: {account_info['cash']}")
            self.logger.info(f"Current positions: {positions}")
        except Exception as e:
            self.logger.error(f"Error updating portfolio: {e}")
            raise

    async def liquidate_position(self, ticker: str):
        """Liquidates a specific position."""
        self.logger.info(f"Liquidating position for {ticker}")
        try:
            position = await self.alpaca_client.get_position_async(ticker)
            qty = position['qty']
            trade_signal = TradeSignal(
                ticker=ticker,
                signal_type='SELL',
                quantity=float(qty),
                strategy_id='liquidation',
                timestamp=datetime.utcnow(),
                price=None
            )
            await self.execute_trade_with_recovery(trade_signal)
        except Exception as e:
            self.logger.error(f"Error liquidating position: {e}")
            raise

    async def liquidate_all_positions(self):
        """Liquidates all positions."""
        self.logger.info("Liquidating all positions.")
        try:
            positions = await self.alpaca_client.get_positions_async()
            tasks = []
            for position in positions:
                ticker = position['symbol']
                qty = position['qty']
                trade_signal = TradeSignal(
                    ticker=ticker,
                    signal_type='SELL',
                    quantity=float(qty),
                    strategy_id='liquidation',
                    timestamp=datetime.utcnow(),
                    price=None
                )
                tasks.append(self.execute_trade_with_recovery(trade_signal))
            await asyncio.gather(*tasks)
            self.logger.info("All positions have been liquidated.")
        except Exception as e:
            self.logger.error(f"Error liquidating all positions: {e}")
            for position in positions:
                try:
                    ticker = position['symbol']
                    await self.handle_failed_trade(
                        TradeSignal(
                            ticker=ticker,
                            signal_type='SELL',
                            quantity=float(position['qty']),
                            strategy_id='liquidation_recovery',
                            timestamp=datetime.utcnow(),
                            price=None
                        ),
                        f"Failed during bulk liquidation: {str(e)}"
                    )
                except Exception as inner_e:
                    self.logger.error(f"Error handling failed liquidation for {ticker}: {inner_e}")
            raise

    async def cancel_all_orders(self):
        """Cancels all pending orders."""
        self.logger.info("Canceling all pending orders.")
        try:
            self._active_orders.clear()
            await self.alpaca_client.cancel_all_orders_async()
            self.logger.info("All orders have been canceled.")
        except Exception as e:
            self.logger.error(f"Error canceling all orders: {e}")
            raise

    async def shutdown(self):
        """Gracefully shuts down the engine, ensuring resources are cleaned up."""
        self.logger.info("Shutting down execution engine.")
        # Cancel the recovery task if it exists
        if hasattr(self, '_recovery_task') and self._recovery_task is not None:
            self._recovery_task.cancel()
            del self._recovery_task

        # Run cleanup
        await self.cleanup()

        # Close the Alpaca API client session
        await self.alpaca_client.close()

        self.logger.info("Execution engine shutdown complete.")

    async def shutdown(self):
        """Gracefully shuts down the engine, ensuring resources are cleaned up."""
        self.logger.info("Shutting down execution engine.")
        # Cancel the recovery task if it exists
        if hasattr(self, '_recovery_task') and self._recovery_task is not None:
            self._recovery_task.cancel()

        # Run cleanup
        await self.cleanup()

        # Close the Alpaca API client session
        await self.alpaca_client.close()

        self.logger.info("Execution engine shutdown complete.")

    async def cleanup(self):
        """Performs cleanup operations before shutdown."""
        try:
            self.logger.info("Starting cleanup process.")
            await self.cancel_all_orders()

            while not self.signal_queue.empty():
                try:
                    trade_signal = self.signal_queue.get_nowait()
                    if trade_signal is not None:
                        await self.handle_failed_trade(
                            trade_signal,
                            "Trade signal not processed due to shutdown"
                        )
                except queue.Empty:
                    break

            # Final status update for active orders
            final_status_updates = []
            for strategy_id, order_id in self._active_orders.items():
                try:
                    order = await self.alpaca_client.get_order_status_async(order_id)
                    self.order_manager.update_order(order)
                    final_status_updates.append(f"Order {order_id}: {order['status']}")
                except Exception as e:
                    self.logger.error(f"Error updating final status for order {order_id}: {e}")

            if final_status_updates:
                self.logger.info("Final order statuses: %s", ", ".join(final_status_updates))

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        finally:
            self._active_orders.clear()




if __name__ == '__main__':
    execution_engine = ExecutionEngine()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        execution_engine.shutdown()
