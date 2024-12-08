# components/data_management_module/config.py

import os
from configparser import ConfigParser
from pathlib import Path

class DataConfig:
    def __init__(self):
        self.config = ConfigParser()
        
        # Define base paths
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / 'data'
        self.log_dir = self.project_root / 'logs'
        
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)
        
        self.load_config()

    def load_config(self):
        """Load configuration from config file and environment variables"""
        # Default settings
        self.config['DEFAULT'] = {
            'database_path': str(self.data_dir / 'market_data.db'),
            'tickers_file': str(self.project_root / 'tickers.csv'),
            'log_file': str(self.log_dir / 'data_manager.log'),
            'historical_data_years': '5',
            'data_frequency_minutes': '5',
            'batch_size': '1000',
            'zeromq_port': '5555',
            'zeromq_topic': 'market_data'
        }

        # Data API settings
        self.config['api'] = {
            'base_url': 'https://data.alpaca.markets/v2',
            'key_id': os.getenv('APCA_API_KEY_ID', ''),
            'secret_key': os.getenv('APCA_API_SECRET_KEY', ''),
            'rate_limit_retry_attempts': '3',
            'rate_limit_retry_wait': '5',
            'rate_limit_delay': '0.2'
        }

        # Validate required settings
        self._validate_config()

    def _validate_config(self):
        """Validate critical configuration settings"""
        if not self.config['api']['key_id'] or not self.config['api']['secret_key']:
            raise ValueError("Alpaca API credentials not found in environment variables")

    def get(self, section, key):
        """Get a configuration value"""
        return self.config.get(section, key)

    def get_int(self, section, key):
        """Get an integer configuration value"""
        return self.config.getint(section, key)

    def get_float(self, section, key):
        """Get a float configuration value"""
        return self.config.getfloat(section, key)

# Global config instance
config = DataConfig()