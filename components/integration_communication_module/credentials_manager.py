# components/integration_communication_module/credentials_manager.py

class CredentialsManager:
    def __init__(self, config):
        self._config = config

    def get_alpaca_credentials(self):
        if not self._config.ALPACA_API_KEY or not self._config.ALPACA_SECRET_KEY:
            raise ValueError("Alpaca API credentials are not set.")
        return {
            'api_key': self._config.ALPACA_API_KEY,
            'secret_key': self._config.ALPACA_SECRET_KEY,
            'base_url': self._config.ALPACA_BASE_URL
        }

    def get_zeromq_port(self):
        return self._config.ZEROMQ_PORT
