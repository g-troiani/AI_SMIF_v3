# components/integration_communication_module/service_factory.py

from .api_clients.alpaca_client import AlpacaClient
from .credentials_manager import CredentialsManager
from .config import Config

class ServiceFactory:
    @staticmethod
    def get_data_service(service_name):
        if service_name == 'alpaca':
            credentials_manager = CredentialsManager(Config())
            return AlpacaClient(credentials_manager)
        else:
            raise ValueError(f"Unknown data service: {service_name}")

    @staticmethod
    def get_trade_service(service_name):
        if service_name == 'alpaca':
            credentials_manager = CredentialsManager(Config())
            return AlpacaClient(credentials_manager)
        else:
            raise ValueError(f"Unknown trade service: {service_name}")
