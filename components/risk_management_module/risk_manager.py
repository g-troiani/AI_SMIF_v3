# components/risk_management_module/risk_manager.py

from .stop_loss_handler import StopLossHandler
from .emergency_liquidation import EmergencyLiquidation
from components.risk_management_module.config import MAX_DRAW_DOWN_PERCENT
from components.data_management_module.data_manager import DataManager  # Actual DataManager used

class RiskManager:
    def __init__(self, portfolio_manager, trading_execution_engine):
        self.portfolio_manager = portfolio_manager
        self.trading_execution_engine = trading_execution_engine
        self.stop_loss_handler = StopLossHandler()
        self.emergency_liquidation = EmergencyLiquidation(portfolio_manager, trading_execution_engine)
        self.approved_strategies = {}  # {strategy_id: bool} to indicate strategy approval
        self.data_manager = DataManager()  # Actual data manager integration for retrieving current prices
    
    def validate_strategy(self, strategy_id, historical_performance):
        """Validate a strategy based on historical performance."""
        # For MVP, consider a simple approval criterion:
        # - positive total return 
        # - Sharpe ratio above 1
        total_return = historical_performance.get('total_return', 0)
        sharpe_ratio = historical_performance.get('sharpe_ratio', 0)
        if total_return > 0 and sharpe_ratio > 1:
            self.approved_strategies[strategy_id] = True
            return True
        else:
            self.approved_strategies[strategy_id] = False
            return False

    def is_strategy_approved(self, strategy_id):
        """Check if a strategy is approved."""
        return self.approved_strategies.get(strategy_id, False)

    def restrict_unapproved_strategies(self, active_strategies):
        """Remove unapproved strategies from the active list."""
        approved_active_strategies = [s for s in active_strategies if self.is_strategy_approved(s)]
        if len(approved_active_strategies) < len(active_strategies):
            print("Some strategies are not approved and have been deactivated.")
        return approved_active_strategies

    def set_stop_loss(self, new_stop_loss_percent):
        """Set new stop-loss percentage for all strategies."""
        self.stop_loss_handler.set_stop_loss(new_stop_loss_percent)
        print(f"Stop-loss updated to {new_stop_loss_percent}%.")

    def set_take_profit(self, new_take_profit_percent):
        """Set new take-profit percentage for all strategies."""
        self.stop_loss_handler.set_take_profit(new_take_profit_percent)
        print(f"Take-profit updated to {new_take_profit_percent}%.")

    def monitor_positions(self):
        """Monitor positions and enforce stop-loss/take-profit levels."""
        for strategy_id, positions in self.portfolio_manager.strategy_positions.items():
            for ticker, quantity in positions.items():
                if quantity > 0:
                    current_price = self.data_manager.get_current_price(ticker)  # real call to DataManager
                    purchase_price = self._get_average_purchase_price(strategy_id, ticker)
                    if self.stop_loss_handler.check_stop_loss(purchase_price, current_price):
                        print(f"Stop-loss triggered for {ticker} in strategy {strategy_id}")
                        self.trading_execution_engine.place_order(strategy_id, ticker, 'SELL', quantity)
                    elif self.stop_loss_handler.check_take_profit(purchase_price, current_price):
                        print(f"Take-profit triggered for {ticker} in strategy {strategy_id}")
                        self.trading_execution_engine.place_order(strategy_id, ticker, 'SELL', quantity)

    def handle_extreme_market_conditions(self):
        """Automate protective actions during extreme market conditions."""
        portfolio_metrics = self.portfolio_manager.get_portfolio_metrics()
        if portfolio_metrics and portfolio_metrics.get('max_drawdown', 0) > MAX_DRAW_DOWN_PERCENT:
            print("Extreme market conditions detected. Halting new trades and contacting user.")
            # Optionally call emergency liquidation or other protective measures

    def panic_button_pressed(self):
        """Handle emergency liquidation triggered by the user."""
        self.emergency_liquidation.initiate_liquidation()
    
    def enforce_risk_controls_on_trades(self, strategy_id, ticker, order_type, quantity):
        """Check if a trade violates any risk controls before execution."""
        if not self.is_strategy_approved(strategy_id):
            print(f"Strategy {strategy_id} is not approved. Trade blocked.")
            return False
        # Additional risk checks can be added here, e.g. verifying position sizes do not exceed strategy limits
        return True

    def _get_average_purchase_price(self, strategy_id, ticker):
        """Calculate the average purchase price of a position for a given strategy and ticker."""
        # We assume that strategy_trade_history is a dictionary of trades for each ticker 
        # This can be integrated with portfolio_manager's trade recording system
        trades = self.portfolio_manager.strategy_trade_history[strategy_id].get(ticker, [])
        total_cost = sum(trade['trade_price'] * trade['trade_quantity'] for trade in trades if trade['trade_quantity'] > 0)
        total_quantity = sum(trade['trade_quantity'] for trade in trades if trade['trade_quantity'] > 0)
        if total_quantity == 0:
            # If no quantity purchased, we fall back to current price for calculation
            current_price = self.data_manager.get_current_price(ticker)
            return current_price if current_price is not None else 100.0
        return total_cost / total_quantity
