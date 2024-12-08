# components/portfolio_management_module/portfolio_manager.py

from datetime import datetime
from .monitor import PortfolioMonitor
from .config import DEFAULT_ALLOCATION_PER_STRATEGY
from .performance_metrics import (
    calculate_total_return,
    calculate_daily_returns,
    calculate_sharpe_ratio,
    calculate_max_drawdown
)

class PortfolioManager:
    def __init__(self):
        self.strategy_allocations = {}
        self.strategy_positions = {}  # {strategy_id: {ticker: quantity}}
        self.strategy_value_history = {}  # {strategy_id: [history of daily portfolio values]}
        self.strategy_metrics = {}  # {strategy_id: {'total_return': ..., 'sharpe_ratio': ..., 'max_drawdown': ...}}

    def allocate_capital_to_strategies(self, active_strategies):
        """Allocate capital to each active strategy based on default allocations and total capital."""
        total_capital = self.get_total_capital()
        required_allocation = len(active_strategies) * DEFAULT_ALLOCATION_PER_STRATEGY

        if total_capital is None:
            # If we can't determine total capital, allocate default to each strategy
            for strategy_id in active_strategies:
                self.strategy_allocations[strategy_id] = DEFAULT_ALLOCATION_PER_STRATEGY
        else:
            if total_capital >= required_allocation:
                # Allocate the full default amount to each strategy
                for strategy_id in active_strategies:
                    self.strategy_allocations[strategy_id] = DEFAULT_ALLOCATION_PER_STRATEGY
            else:
                # Insufficient capital, allocate proportionally
                ratio = total_capital / required_allocation if required_allocation != 0 else 0.0
                for strategy_id in active_strategies:
                    allocation = DEFAULT_ALLOCATION_PER_STRATEGY * ratio
                    self.strategy_allocations[strategy_id] = allocation
        return self.strategy_allocations

    def get_total_capital(self):
        """Get the total capital available in the user's account."""
        # Placeholder: For MVP, we'll assume a fixed total capital
        return 100000.0  # Example: $100,000 total capital

    def get_strategy_allocation(self, strategy_id):
        """Return the allocated capital for a given strategy."""
        return self.strategy_allocations.get(strategy_id, 0)

    def calculate_order_quantity(self, strategy_id, stock_price, trade_direction, existing_position=0):
        """Calculate how many shares can be traded based on allocation, price, and direction."""
        allocated_capital = self.get_strategy_allocation(strategy_id)
        
        if trade_direction.upper() == "BUY":
            if stock_price > 0:
                # how many shares can we buy with the allocated capital?
                max_shares = allocated_capital // stock_price
                return int(max_shares)
            else:
                return 0
        elif trade_direction.upper() == "SELL":
            # For SELL, the quantity is determined by the existing position of that stock in the strategy
            return int(existing_position)
        else:
            return 0

    def update_allocation_after_trade(self, strategy_id, trade_direction, trade_price, trade_quantity):
        """Update allocated capital after a trade is executed."""
        total_trade_value = trade_price * trade_quantity
        current_allocation = self.get_strategy_allocation(strategy_id)
        
        if trade_direction.upper() == "BUY":
            new_allocation = current_allocation - total_trade_value
            self.strategy_allocations[strategy_id] = max(new_allocation, 0)
        elif trade_direction.upper() == "SELL":
            new_allocation = current_allocation + total_trade_value
            self.strategy_allocations[strategy_id] = new_allocation

    def record_trade(self, strategy_id, ticker, trade_quantity, trade_price):
        """Record trade execution for performance tracking."""
        if strategy_id not in self.strategy_positions:
            self.strategy_positions[strategy_id] = {}
        current_position = self.strategy_positions[strategy_id].get(ticker, 0)
        new_position = current_position + trade_quantity
        if new_position == 0:
            # Remove the ticker from positions if quantity is 0
            if ticker in self.strategy_positions[strategy_id]:
                del self.strategy_positions[strategy_id][ticker]
        else:
            self.strategy_positions[strategy_id][ticker] = new_position

    def update_strategy_value(self, strategy_id, new_value):
        """Update the daily value of a strategy's portfolio."""
        if strategy_id not in self.strategy_value_history:
            self.strategy_value_history[strategy_id] = []
        self.strategy_value_history[strategy_id].append(new_value)

    def calculate_strategy_performance(self, strategy_id):
        """Calculate and store performance metrics for a given strategy."""
        values = self.strategy_value_history.get(strategy_id, [])
        if len(values) < 2:
            # Not enough data to calculate returns
            return
        initial_value = values[0]
        current_value = values[-1]
        total_ret = calculate_total_return(initial_value, current_value)
        daily_returns = calculate_daily_returns(values)
        sharpe = calculate_sharpe_ratio(daily_returns)
        mdd = calculate_max_drawdown(values)
        self.strategy_metrics[strategy_id] = {
            'total_return': total_ret,
            'sharpe_ratio': sharpe,
            'max_drawdown': mdd
        }

    def calculate_portfolio_performance(self):
        """Calculate and store performance metrics for the entire portfolio."""
        total_values = []
        for strategy_id, values in self.strategy_value_history.items():
            if values:
                total_values.append(values[-1])
        
        if not total_values:
            return None

        portfolio_value = sum(total_values)
        initial_value = sum(values[0] for values in self.strategy_value_history.values() if values)
        total_ret = calculate_total_return(initial_value, portfolio_value)
        combined_history = self._calculate_combined_portfolio_history()
        daily_returns = calculate_daily_returns(combined_history)
        sharpe = calculate_sharpe_ratio(daily_returns)
        mdd = calculate_max_drawdown(combined_history)
        portfolio_metrics = {
            'total_return': total_ret,
            'sharpe_ratio': sharpe,
            'max_drawdown': mdd
        }
        benchmark_return = self._get_benchmark_return()
        actual_alpha = total_ret - benchmark_return if benchmark_return is not None else None
        expected_alpha = self._calculate_expected_alpha()
        if actual_alpha is not None:
            portfolio_metrics['actual_alpha'] = actual_alpha
        if expected_alpha is not None:
            portfolio_metrics['expected_alpha'] = expected_alpha

        return portfolio_metrics
    
    def _calculate_combined_portfolio_history(self):
        """Helper to aggregate daily total portfolio values from strategy histories."""
        if not self.strategy_value_history:
            return []
        max_days = max(len(values) for values in self.strategy_value_history.values() if values)
        combined_history = []
        for day in range(max_days):
            day_total = sum(values[day] for values in self.strategy_value_history.values() if len(values) > day)
            combined_history.append(day_total)
        return combined_history
    
    def _get_benchmark_return(self):
        """Retrieve benchmark actual returns. Placeholder for actual integration."""
        return 10.0  # for MVP
    
    def _calculate_expected_alpha(self):
        """Calculate expected alpha from backtesting data. Placeholder."""
        return 5.0

    def get_strategy_metrics(self, strategy_id):
        """Return performance metrics for a given strategy."""
        return self.strategy_metrics.get(strategy_id, {})

    def get_portfolio_metrics(self):
        """Return performance metrics for the entire portfolio."""
        return self.calculate_portfolio_performance()

    def get_total_exposure(self):
        """Provide details of total portfolio positions for risk management."""
        total_exposure = {}
        for strategy_id, positions in self.strategy_positions.items():
            for ticker, quantity in positions.items():
                if ticker in total_exposure:
                    total_exposure[ticker] += quantity
                else:
                    total_exposure[ticker] = quantity
        return total_exposure

    def adjust_allocations_based_on_risk(self, new_allocations):
        """Adapt allocations based on risk assessments from the Risk Management Module."""
        for strategy_id, allocation in new_allocations.items():
            self.strategy_allocations[strategy_id] = allocation

    def get_current_holdings(self):
        """Return current holdings and their market values."""
        current_holdings = {}
        for strategy_id, positions in self.strategy_positions.items():
            holdings_value = 0.0
            for ticker, quantity in positions.items():
                current_price = self._get_current_price_for_ticker(ticker)
                position_value = current_price * quantity
                holdings_value += position_value
            current_holdings[strategy_id] = holdings_value
        return current_holdings

    def _get_current_price_for_ticker(self, ticker):
        """Get current market price for a ticker. Placeholder for integration with Data Management Module."""
        return 100.0  # Placeholder

    def check_portfolio_for_alerts(self):
        """Check for portfolio events requiring alerts."""
        alerts = []
        portfolio_metrics = self.calculate_portfolio_performance()
        if portfolio_metrics and 'max_drawdown' in portfolio_metrics and portfolio_metrics['max_drawdown'] > 20:
            alerts.append("Significant portfolio drawdown detected!")
        for strategy_id, allocation in self.strategy_allocations.items():
            if allocation < 0:
                alerts.append(f"Insufficient capital for strategy {strategy_id}. Allocation is negative.")
        return alerts
