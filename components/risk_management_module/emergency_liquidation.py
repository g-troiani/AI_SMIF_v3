# components/risk_management_module/emergency_liquidation.py

class EmergencyLiquidation:
    def __init__(self, portfolio_manager, trading_execution_engine):
        self.portfolio_manager = portfolio_manager
        self.trading_execution_engine = trading_execution_engine

    def initiate_liquidation(self):
        """Liquidate all positions immediately."""
        holdings = self.portfolio_manager.get_current_holdings()
        for strategy_id, value in holdings.items():
            positions = self.portfolio_manager.strategy_positions.get(strategy_id, {})
            for ticker, quantity in positions.items():
                if quantity > 0:
                    # Initiate a sell order for all holdings
                    self.trading_execution_engine.place_order(strategy_id, ticker, 'SELL', quantity)
        # After liquidation, update portfolio and log the event
        print("Emergency liquidation triggered. All positions have been liquidated.")
