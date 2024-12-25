# components/data_management_module/config.py

import os
from configparser import ConfigParser
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

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
            'tickers_file': str(self.data_dir / 'tickers.csv'),
            'log_file': str(self.log_dir / 'data_manager.log'),
            'historical_data_years': '5',
            'data_frequency_minutes': '5',
            'batch_size': '1000',
            'zeromq_port': '5555',
            'zeromq_topic': 'market_data',
            'live_trading_mode': 'False',
            'use_alpaca_store': 'False',
            'live_trading_database_path': str(self.data_dir / 'live_trading_data.db')
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

        if 'strategies' not in self.config.sections():
            self.config.add_section('strategies')

        # Validate required settings
        self._validate_config()

    def _validate_config(self):
        """Validate critical configuration settings"""
        if not self.config['DEFAULT']['database_path']:
            raise ValueError("Database path missing from config")

    def get(self, section, key, fallback=None):
        """Get a configuration value"""
        return self.config.get(section, key, fallback=fallback)

    def get_int(self, section, key):
        """Get an integer configuration value"""
        return self.config.getint(section, key)

    def get_float(self, section, key):
        """Get a float configuration value"""
        return self.config.getfloat(section, key)

    def sections(self):
        return self.config.sections()

    def items(self, section):
        return self.config.items(section)

# Global config instance
config = DataConfig()

# Sprint 1: Added new class for unified configuration loading
class UnifiedConfigLoader:
    """
    Loads global config, including both live and backtesting settings.
    Simplifies references so the Backtester does not fetch environment variables directly.
    """

    @classmethod
    def get_backtest_setting(cls, key, default=None):
        """
        Example: Retrieve a backtest-related config from environment or default values.
        """
        # For demonstration, just a single environment or fallback approach
        if key == 'historical_data_years':
            # e.g. environment variable, or fallback
            return int(os.getenv('BACKTEST_DATA_YEARS', '5'))
        # Additional keys can be handled similarly
        return default

    @classmethod
    def is_live_trading_mode(cls):
        """
        Already existing method from your original code or suggestion #1 example.
        """
        val = os.getenv('LIVE_TRADING_MODE', 'False')
        return val.lower() in ['true', '1', 'yes']

    @classmethod
    def use_alpaca_store(cls):
        env_val = os.getenv('USE_ALPACA_STORE', '')
        if env_val.lower() in ['true', '1', 'yes']:
            return True
        elif env_val.lower() in ['false', '0', 'no', '']:
            val = config.get('DEFAULT', 'use_alpaca_store', fallback='False').lower() == 'true'
            return val
        return False

    @classmethod
    def get_strategy_mode(cls, strategy_name):
        if not cls.is_live_trading_mode():
            return 'backtest'
        mode = config.get('strategies', strategy_name, fallback='backtest').lower()
        if mode not in ['live', 'backtest']:
            mode = 'backtest'
        return mode
    
    @classmethod
    def set_strategy_mode(cls, strategy_name, new_mode):
        if new_mode not in ['live', 'backtest']:
            new_mode = 'backtest'
        config.config.set('strategies', strategy_name, new_mode)
        logger.info(f"set_strategy_mode: Strategy {strategy_name} mode set to {new_mode} in runtime config.")

    @classmethod
    def list_strategies(cls):
        if 'strategies' in config.sections():
            return [item[0] for item in config.items('strategies')]
        return ['default_strategy']    