# components/integration_communication_module/api_clients/base_trade_service.py

from abc import ABC, abstractmethod

class BaseTradeService(ABC):
    @abstractmethod
    def place_order(self, symbol, qty, side, type, time_in_force):
        pass

    @abstractmethod
    def get_account(self):
        pass
