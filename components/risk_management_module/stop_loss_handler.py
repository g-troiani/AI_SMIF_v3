# components/risk_management_module/stop_loss_handler.py

from .config import DEFAULT_STOP_LOSS_PERCENT, DEFAULT_TAKE_PROFIT_PERCENT

class StopLossHandler:
    def __init__(self, stop_loss_percent=DEFAULT_STOP_LOSS_PERCENT, take_profit_percent=DEFAULT_TAKE_PROFIT_PERCENT):
        self.stop_loss_percent = stop_loss_percent
        self.take_profit_percent = take_profit_percent
    
    def set_stop_loss(self, new_stop_loss_percent):
        """Set a new stop-loss percentage."""
        self.stop_loss_percent = new_stop_loss_percent

    def set_take_profit(self, new_take_profit_percent):
        """Set a new take-profit percentage."""
        self.take_profit_percent = new_take_profit_percent

    def check_stop_loss(self, purchase_price, current_price):
        """Check if current price triggers a stop-loss condition."""
        if current_price <= purchase_price * (1 - self.stop_loss_percent / 100.0):
            return True
        return False

    def check_take_profit(self, purchase_price, current_price):
        """Check if current price triggers a take-profit condition."""
        if current_price >= purchase_price * (1 + self.take_profit_percent / 100.0):
            return True
        return False
