# components/integration_communication_module/api_clients/base_data_service.py

from abc import ABC, abstractmethod

class BaseDataService(ABC):
    @abstractmethod
    def get_market_data(self, symbol, timeframe, start, end):
        pass
