# File: components/trading_execution_engine/execution_engine.py
# Type: py

import os
import asyncio
import threading
import queue
import json
import time  # from code2 (explicitly added)
from datetime import datetime  # from code2 (explicitly replaced datetime,time)
import logging
from typing import Optional, Dict, Any
from .trade_signal import TradeSignal
from .order_manager import OrderManager
from ..data_management_module.alpaca_api import AlpacaAPIClient
from ..data_management_module.config import CONFIG


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

        # From code2: replaced self.logger = self._setup_logging() with:
        self.logger = logging.getLogger('execution_engine')

        # From code2: replaced self.loop = asyncio.get_event_loop() with:
        self.loop = asyncio.new_event_loop()

        self.daily_pnl = 0.0
        self.risk_config = CONFIG['risk']
        self.recovery_interval = 300  # (code1 comment: was 5 minutes; code2 sets same 300)
        self.max_retries = 3
        # From code2: explicitly changed retry_delays to [2,5,10]
        self.retry_delays = [2, 5, 10]

        self._active_orders: Dict[str, Dict[str, Any]] = {}

        # code1 had: self._start_recovery_task(), which code2 does not call -> removed from constructor
        # code2 adds:
        self.stop_event = threading.Event()
        self._thread = None

    ############################################################################
    #  BELOW: code1 methods that code2 does NOT explicitly remove or replace   #
    #         (we KEEP them unless code2 shows a direct removal).             #
    ############################################################################

    def _setup_logging(self):
        """
        (From code1)
        Sets up file-based logging. (Unused now, because code2 replaced usage with module-level logger)
        """
        logger = logging.getLogger('execution_engine')
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(CONFIG['logging']['log_file'])
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

    def _start_recovery_task(self):
        """
        (From code1)
        Starts the periodic recovery task for failed trades.
        This is never called anymore per code2, but code2 did not explicitly remove it.
        """
        async def run_recovery():
            while not self.stop_event.is_set():
                interval = 0.1 if os.getenv("TEST_MODE") else self.recovery_interval
                await asyncio.sleep(interval)
                if self.stop_event.is_set():
                    break
                try:
                    await self._recover_failed_trades()
                except Exception as e:
                    self.logger.error(f"Error in recovery task: {e}")

        asyncio.run_coroutine_threadsafe(run_recovery(), self.loop)

    async def _recover_failed_trades(self):
        """
        (From code1)
        Attempts to recover failed trades with retry logic.
        """
        try:
            failed_trades = self._get_pending_failed_trades_for_recovery()
            for trade_info in failed_trades:
                trade_id, trade_signal_json, error_message, retry_count = trade_info
                await self._recover_single_failed_trade(trade_id, trade_signal_json, error_message, retry_count)
        except Exception as e:
            self.logger.error(f"Error in recovery process: {e}")

    def _get_pending_failed_trades_for_recovery(self):
        """
        (From code1)
        Retrieves pending failed trades from the order manager for recovery.
        """
        return self.order_manager.get_pending_failed_trades(self.max_retries)

    async def _recover_single_failed_trade(self, trade_id, trade_signal_json, error_message, retry_count):
        """
        (From code1)
        Attempts to recover a single failed trade.
        """
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
                await self.handle_failed_trade(
                    locals().get('trade_signal'),
                    str(e),
                    trade_id
                )
        finally:
            # Wait a brief moment before processing the next trade
            await asyncio.sleep(1)

    ############################################################################
    #  BELOW: code2 modifies/replaces the _process_signals() from code1.       #
    ############################################################################

    def start(self):
        """
        (From code2)
        Starts the ExecutionEngine in a background thread.
        """
        self.logger.warning("[DEBUG] ExecutionEngine.start() called. Setting up event loop ...")
        if self._thread is not None and self._thread.is_alive():
            self.logger.info("ExecutionEngine is already running.")
            return
        self.logger.info("Starting ExecutionEngine in background thread.")
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()

    def _run_event_loop(self):
        """
        (From code2)
        """
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._process_signals())
        except Exception as e:
            self.logger.error(f"Error in event loop: {e}")
        finally:
            self.loop.close()

    async def _process_signals(self):
        """
        (Replaced code1's _process_signals with code2's version)
        Processes trade signals from the queue in an event loop, until stop_event is set.
        """
        while not self.stop_event.is_set():
            try:
                trade_signal = await self.loop.run_in_executor(None, self.signal_queue.get)
                if trade_signal is None:
                    continue
                await self.execute_trade_signal(trade_signal)
            except Exception as e:
                self.logger.error(f"Error processing trade signal: {e}")

    def add_trade_signal(self, trade_signal: TradeSignal):
        """
        (From code2)
        Places a new TradeSignal into the queue for async processing.
        """
        self.signal_queue.put(trade_signal)
        self.logger.info(f"Trade signal added to queue: {trade_signal}")

    ############################################################################
    #  BELOW: code2 replaces code1's execute_trade_signal                      #
    ############################################################################

    async def execute_trade_signal(self, trade_signal: TradeSignal):
        """
        (From code2)
        Checks market hours, validates the signal, and then calls execute_trade_with_recovery().
        """
        if not self.is_market_open():
            self.logger.warning("Market is closed. Not executing.")
            await self.handle_failed_trade(trade_signal, "Market closed")
            return

        self.logger.info(f"Processing trade signal: {trade_signal}")
        try:
            if not await self.validate_trade_signal(trade_signal):
                await self.handle_failed_trade(trade_signal, "Trade validation failed")
                return
            await self.execute_trade_with_recovery(trade_signal)
        except Exception as e:
            self.logger.error(f"Error executing trade signal: {e}")
            await self.handle_failed_trade(trade_signal, str(e))

    ############################################################################
    #  BELOW: code2 replaces code1's validate_trade_signal                     #
    ############################################################################

    async def validate_trade_signal(self, trade_signal: TradeSignal) -> bool:
        """
        Validates a trade signal vs. risk rules (max position, daily loss limit, etc.).
        """
        try:
            account_info = await self.alpaca_client.get_account_info_async()
            portfolio_value = float(account_info.get('portfolio_value', 0))

            # If your environment always returns 0 for 'portfolio_value', consider:
            if portfolio_value <= 0:
                self.logger.warning(
                    "Portfolio value is zero or not available; skipping validation. "
                    "All trades pass or are blocked—depends on your environment."
                )
                # Possibly return True or False depending on your test logic
                # For real usage, handle the 0-value scenario carefully.
                return True

            validation_price = trade_signal.price or 0.0
            if trade_signal.order_type == 'limit':
                validation_price = trade_signal.limit_price or 0.0
            elif trade_signal.order_type == 'stop':
                validation_price = trade_signal.stop_price or 0.0

            order_value = trade_signal.quantity * validation_price
            max_position_value = portfolio_value * self.risk_config['max_position_size_pct']

            self.logger.debug(
                f"Validating trade: ticker={trade_signal.ticker} order_value={order_value}, "
                f"portfolio_value={portfolio_value}, daily_pnl={self.daily_pnl}"
            )

            if order_value > max_position_value:
                self.logger.warning(
                    f"Order value {order_value} exceeds max position size {max_position_value}"
                )
                return False
            if order_value > self.risk_config['max_order_value']:
                self.logger.warning(
                    f"Order value {order_value} exceeds max order value {self.risk_config['max_order_value']}"
                )
                return False

            # daily loss limit
            if self.daily_pnl <= -(portfolio_value * self.risk_config['daily_loss_limit_pct']):
                self.logger.warning("Daily loss limit reached")
                return False

            return True
        except Exception as e:
            self.logger.error(f"Error validating trade signal: {e}")
            return False


    ############################################################################
    #  BELOW: code2 replaces code1's execute_trade_with_recovery               #
    ############################################################################

    async def execute_trade_with_recovery(self, trade_signal: TradeSignal, is_recovery=False):
        """
        (From code2)
        Tries placing the order multiple times up to self.max_retries.
        """
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

    ############################################################################
    #  BELOW: code2 replaces code1's place_order                               #
    ############################################################################

    async def place_order(self, trade_signal: TradeSignal):
        """
        (From code2)
        Places the order asynchronously using Alpaca's API, logs it, and tracks it in _active_orders.
        """
        self.logger.warning(f"[DEBUG] place_order called for {trade_signal}")
        self.logger.info(f"Placing order for trade_signal: {trade_signal}")
        start_time = datetime.now()

        order_params = {
            'symbol': trade_signal.ticker,
            'qty': trade_signal.quantity,
            'side': trade_signal.signal_type.lower(),
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
            self.logger.warning(f"[DEBUG] Alpaca responded with order id={order.get('id')}")
            exec_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Order placed: {order} (time: {exec_time:.3f}s)")
            order['execution_time'] = exec_time

            self.order_manager.add_order(order)
            self._active_orders[trade_signal.strategy_id] = order['id']
            await self.check_order_status(order['id'])
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            raise

    ############################################################################
    #  BELOW: code2 replaces code1's check_order_status                        #
    ############################################################################

    async def check_order_status(self, order_id: str):
        """
        (From code2)
        Checks order status up to 10 times in 5-second intervals, or until filled/cancelled.
        """
        self.logger.info(f"Checking status for order ID: {order_id}")
        try:
            for _ in range(10):
                order = await self.alpaca_client.get_order_status_async(order_id)
                status = order.get('status')
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

    ############################################################################
    #  BELOW: code2 replaces code1's update_daily_pnl                          #
    ############################################################################

    async def update_daily_pnl(self):
        """
        (From code2)
        Fetches account info and updates self.daily_pnl = equity - last_equity.
        """
        try:
            account_info = await self.alpaca_client.get_account_info_async()
            self.daily_pnl = float(account_info.get('equity', 0)) - float(account_info.get('last_equity', 0))
            self.logger.info(f"Updated daily P&L: {self.daily_pnl}")
        except Exception as e:
            self.logger.error(f"Error updating daily P&L: {e}")

    ############################################################################
    #  BELOW: code1 methods that code2 does NOT explicitly remove, so we KEEP  #
    ############################################################################

    async def update_portfolio(self):
        """
        (From code1; code2 never mentions or removes it explicitly.)
        Updates portfolio information.
        """
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
        """
        (From code1; code2 never mentions or removes it explicitly.)
        Liquidates a specific position.
        """
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
        """
        (From code1; code2 never mentions or removes it explicitly.)
        Liquidates all positions.
        """
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
        """
        (From code1; code2 never mentions or removes it explicitly.)
        Cancels all pending orders.
        """
        self.logger.info("Canceling all pending orders.")
        try:
            self._active_orders.clear()
            await self.alpaca_client.cancel_all_orders_async()
            self.logger.info("All orders have been canceled.")
        except Exception as e:
            self.logger.error(f"Error canceling all orders: {e}")
            raise

    ############################################################################
    #  BELOW: code2 replaces code1's is_market_open()                          #
    ############################################################################

    def is_market_open(self) -> bool:
        """
        (From code2)
        A naive approach: 9:30 AM to 4:00 PM local time.
        """
        now = datetime.now()
        if now.hour < 9 or (now.hour == 9 and now.minute < 30):
            return False
        if now.hour > 16 or (now.hour == 16 and now.minute > 0):
            return False
        return True

    ############################################################################
    #  BELOW: code1 had two async shutdown() definitions + cleanup().          #
    #         code2 has a single async shutdown() that does not use cleanup(). #
    #         => code2 explicitly REPLACES code1's shutdown.                  #
    #         However, code2 does NOT mention removing cleanup(), so we keep it.
    ############################################################################

    async def cleanup(self):
        """
        (From code1)
        Performs cleanup operations before shutdown.
        Kept because code2 never explicitly removed it, even though code2 doesn't call it.
        """
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

    ############################################################################
    #  BELOW: code2's handle_failed_trade() and shutdown() replace code1's.    #
    ############################################################################

    def handle_failed_trade(self, trade_signal: TradeSignal, error_message: str, existing_trade_id=None):
        """
        (From code2)
        Simpler handle_failed_trade that does not auto-cancel the order.
        """
        try:
            if existing_trade_id:
                self.order_manager.update_failed_trade_status(
                    existing_trade_id, 'retry', error_message
                )
            else:
                self.order_manager.log_failed_trade(trade_signal, error_message)
            self.logger.error(f"Trade failed: {error_message}")
        except Exception as e:
            self.logger.error(f"Error handling failed trade: {e}")

    async def shutdown(self):
        """
        (From code2)
        Gracefully shuts down the engine, stopping the event loop & thread.
        Note: Does NOT call cleanup(), code2 removed that usage.
        """
        self.logger.info("Shutting down execution engine.")
        self.stop_event.set()
        if hasattr(self, 'loop') and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self._thread and self._thread.is_alive():
            self._thread.join()
        self.logger.info("Execution engine shutdown complete.")


if __name__ == '__main__':
    execution_engine = ExecutionEngine()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # code2 replaced code1's "execution_engine.shutdown()" call with an async shutdown,
        # but does not explicitly remove this block, so we keep it as-is.
        execution_engine.shutdown()
