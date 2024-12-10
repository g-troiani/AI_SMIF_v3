# tests/test_alpaca_client.py

import unittest
from components.integration_communication_module.config import Config
from components.integration_communication_module.credentials_manager import CredentialsManager
from components.integration_communication_module.api_clients.alpaca_client import AlpacaClient

class TestAlpacaClient(unittest.TestCase):
    def setUp(self):
        config = Config()
        credentials_manager = CredentialsManager(config)
        self.alpaca_client = AlpacaClient(credentials_manager)

    def test_get_account(self):
        account = self.alpaca_client.get_account()
        self.assertIsNotNone(account)
        print("Account equity:", account.equity)

if __name__ == '__main__':
    unittest.main()
